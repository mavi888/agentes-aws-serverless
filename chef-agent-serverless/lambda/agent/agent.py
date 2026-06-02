"""
Agente chef - asistente de cocina.

Usa Strands SDK con Bedrock y se conecta al MCP server remoto
de TheMealDB para buscar inspiración de recetas.

Persiste la heladera en S3 y la conversación via S3SessionManager.

Este módulo se puede usar tanto desde Lambda (index.py) como localmente.
"""

import os
import time
import logging

from pydantic import BaseModel, Field
from typing import List, Literal

import boto3

from strands import Agent, tool
from strands.models import BedrockModel
from strands.plugins import Plugin, hook
from strands.hooks import (
    BeforeToolCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    AfterModelCallEvent
)
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.tools.mcp import MCPClient
from strands_tools import calculator
from strands_tools import retrieve

from strands.session.s3_session_manager import S3SessionManager
from mcp.client.streamable_http import streamablehttp_client
from fridge_tool import create_heladera_tool

s3_client = boto3.client("s3")

logger = logging.getLogger()
logger.setLevel("INFO")

# Configuración desde variables de entorno
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "mcp-secret-token-2026")
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
SESSION_BUCKET = os.environ.get("SESSION_BUCKET", "")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")


SYSTEM_PROMPT="""Sos un chef profesional y amigable que ayuda a las personas a cocinar.

Tenés acceso a estas herramientas:
1. heladera — Para manejar los ingredientes disponibles del usuario
2. buscar_por_categoria — Para buscar recetas por tipo de cocina o categoría
3. obtener_receta — Para obtener los detalles completos de una receta
4. calculator — Para ajustar cantidades de ingredientes
5. retrieve — Para buscar recetas de la abuela, familiares y tradicionales en la base de conocimiento

Tu forma de trabajar:
1. Cuando el usuario quiere cocinar, revisá qué tiene en la heladera
2. Sugerí recetas creativas basándote en los ingredientes disponibles
3. Cuando el usuario pide inspiración o recetas de una cocina (mexicana, vietnamita, italiana, etc), usá buscar_por_categoria para buscar opciones reales
4. Cuando el usuario menciona "receta de la abuela", "receta familiar", "receta tradicional" o "receta casera", SIEMPRE usá retrieve primero antes de responder
5. Cuando eligen una receta, usá obtener_receta para dar los detalles completos
6. Cuando el usuario menciona ingredientes, agregalos a la heladera

Reglas:
- Siempre hablá en español
- Sé práctico y directo
- Sé creativo pero realista con las combinaciones de ingredientes
- NUNCA digas que no tenés acceso a recetas sin haber intentado usar retrieve primero
"""


# --- Plugin de logging ---
class LoggingPlugin(Plugin):
    name = "logging-plugin"

    def init_agent(self, agent):
        self._tool_start = None

    @hook
    def log_request(self, event: BeforeInvocationEvent) -> None:
        logger.info("📨 Nuevo mensaje recibido")

    @hook
    def log_before_tool(self, event: BeforeToolCallEvent) -> None:
        self._tool_start = time.time()
        tool_input = event.tool_use.get("input", {})
        logger.info("🔧 Usando herramienta: %s | args: %s", event.tool_use["name"], tool_input)
        print(f"  🔧 {event.tool_use['name']}({tool_input})")

    @hook
    def log_after_tool(self, event: AfterToolCallEvent) -> None:
        elapsed = time.time() - self._tool_start if self._tool_start else 0
        if event.exception is None:
            logger.info(
                "✅ Herramienta completada: %s (%.2fs)",
                event.tool_use["name"],
                elapsed,
            )
        else:
            logger.warning(
                "❌ Herramienta falló: %s (%.2fs)",
                event.tool_use["name"],
                elapsed,
            )
    
    @hook
    def log_guardrail(self, event: AfterModelCallEvent) -> None:
        if event.stop_response is None:
            return

        stop_reason = getattr(event.stop_response, "stop_reason", None)

        # stop_reason == "guardrail_intervened" es la señal principal
        if stop_reason == "guardrail_intervened":
            logger.warning("🛡️ GUARDRAIL INTERVINO — stop_reason: guardrail_intervened")
            print("\n🛡️ [GUARDRAIL] Intervino el guardrail (stop_reason=guardrail_intervened)\n")

        # Buscar guardrail trace en los bloques de contenido
        message = getattr(event.stop_response, "message", None)
        if message:
            content = message.get("content", []) if isinstance(message, dict) else getattr(message, "content", [])
            for block in content:
                if isinstance(block, dict) and block.get("guardContent"):
                    logger.warning("🛡️ GUARDRAIL — guardContent: %s", block["guardContent"])
                    print(f"\n🛡️ [GUARDRAIL] guardContent detectado: {block['guardContent']}\n")



# --- Plugin de reintentos ---
class RetryPlugin(Plugin):
    name = "retry-plugin"

    def init_agent(self, agent):
        self._retries = {}

    @hook
    def retry_on_failure(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use["name"]
        if event.exception is not None:
            retries = self._retries.get(tool_name, 0)
            if retries < 3:
                self._retries[tool_name] = retries + 1
                logger.warning(
                    "⚠️ %s falló, reintentando (%d/3)...",
                    tool_name,
                    retries + 1,
                )
                event.retry = True
            else:
                logger.error("🔥 %s falló después de 3 intentos", tool_name)
                self._retries[tool_name] = 0
        else:
            self._retries[tool_name] = 0


def create_agent(session_id: str = None):
    """Crea el agente de asistente de chef con conexión al MCP server remoto.

    Args:
        session_id: ID de sesión para persistir la conversación en S3.
                    Si es None, el agente funciona stateless.
    """
    model = BedrockModel(
        model_id=MODEL_ID,
        guardrail_id=GUARDRAIL_ID if GUARDRAIL_ID else None,
        guardrail_version=GUARDRAIL_VERSION if GUARDRAIL_ID else None,
        guardrail_trace="enabled",
        guardrail_redact_input=False,
        guardrail_redact_output=False,
        # Evalúa solo el último mensaje del usuario, no todo el historial.
        # Esto evita que el contexto previo "diluya" la detección del topic.
        guardrail_latest_message=True,
    )

    # La herramienta retrieve de strands_tools usa KNOWLEDGE_BASE_ID del entorno automáticamente — no necesita instanciación

    # Armar lista de tools
    tools: list = [calculator, retrieve]

    # MCP client solo si hay URL configurada
    if MCP_SERVER_URL:
        mcp_client = MCPClient(
            lambda: streamablehttp_client(
                url=MCP_SERVER_URL,
                headers={"Authorization": f"Bearer {MCP_AUTH_TOKEN}"},
            )
        )
        tools.append(mcp_client)
    else:
        logger.warning("⚠️ MCP_SERVER_URL no configurada, herramientas de recetas no disponibles")

    # Agregar heladera solo si hay bucket y session_id para persistir
    if session_id and SESSION_BUCKET:
        tools.append(create_heladera_tool(SESSION_BUCKET, session_id))

    # Session manager con S3 (si hay session_id y bucket configurado)
    session_manager = None
    if session_id and SESSION_BUCKET:
        session_manager = S3SessionManager(
            session_id=session_id,
            bucket=SESSION_BUCKET,
        )

    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=tools,
        plugins=[LoggingPlugin(), RetryPlugin()],
        session_manager=session_manager,
        conversation_manager=SummarizingConversationManager(
            summary_ratio=0.3,
            preserve_recent_messages=10,
        ),
    )

    return agent