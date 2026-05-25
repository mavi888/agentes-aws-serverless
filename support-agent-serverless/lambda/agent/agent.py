"""
Agente de soporte técnico IT.

Usa Strands SDK con Bedrock y se conecta al MCP server remoto
de base de conocimiento interna (buscar_solucion) via Streamable HTTP.

Incluye plugins de logging y reintentos.

Este módulo se puede usar tanto desde Lambda (index.py) como localmente.
"""

import os
import time
import logging

from pydantic import BaseModel, Field
from typing import Literal

from strands import Agent, tool
from strands.models import BedrockModel
from strands.plugins import Plugin, hook
from strands.hooks import (
    BeforeToolCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    AfterModelCallEvent,
)
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.tools.mcp import MCPClient
from strands.session.s3_session_manager import S3SessionManager
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configurar handler para mostrar logs en consola
if not logger.handlers:  # Evitar duplicar handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Configuración desde variables de entorno
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "mcp-secret-token-2024")
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
SESSION_BUCKET = os.environ.get("SESSION_BUCKET", "")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")

SYSTEM_PROMPT = """Sos un agente de soporte técnico de IT amigable y eficiente.

Tenés acceso a la base de conocimiento interna para problemas comunes de IT
(VPN, email, contraseñas, impresoras).

Tu forma de trabajar:
1. Escuchá el problema del usuario
2. Usá la herramienta buscar_solucion para encontrar la respuesta
3. Explicá la solución paso a paso de forma clara
4. Si resolviste el problema o no podés ayudar más, creá un ticket de soporte usando crear_ticket
5. Si no encontrás solución, recomendá escalar al nivel 2

Reglas:
- Siempre hablá en español
- Sé empático y profesional
- Sé conciso pero completo
- Creá un ticket cuando:
  * El problema está resuelto (para documentar la solución)
  * No podés resolver el problema (para escalarlo)
  * El usuario indica que terminó la consulta
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
        logger.info("🔧 Usando herramienta: %s", event.tool_use["name"])

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
        # Buscar guardrail trace en el mensaje de respuesta
        message = event.stop_response.message
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("guardContent"):
                logger.warning("🛡️ GUARDRAIL INTERVINO: %s", block["guardContent"])
                print("\n🛡️ [GUARDRAIL] Contenido bloqueado detectado en la respuesta\n")
        # stop_reason puede ser "guardrail_intervened"
        if event.stop_response.stop_reason == "guardrail_intervened":
            logger.warning("🛡️ GUARDRAIL INTERVINO — stop_reason: guardrail_intervened")



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


# --- Modelo Pydantic para tickets ---
class SupportTicket(BaseModel):
    """A structured support ticket generated from a user interaction."""

    titulo: str = Field(description="Título breve y descriptivo del problema")
    prioridad: Literal["baja", "media", "alta", "crítica"] = Field(
        description="Nivel de prioridad del ticket"
    )
    categoria: str = Field(
        description="Categoría del problema: redes, email, seguridad, hardware, software, otro"
    )
    descripcion: str = Field(
        description="Descripción del problema reportado por el usuario"
    )
    solucion: str = Field(
        description="Solución proporcionada o pasos a seguir"
    )


@tool
def crear_ticket(
    titulo: str,
    prioridad: Literal["baja", "media", "alta", "crítica"],
    categoria: str,
    descripcion: str,
    solucion: str
) -> str:
    """Crea un ticket de soporte estructurado.
    
    Usá esta herramienta cuando:
    - El problema está resuelto (para documentar)
    - No podés resolver el problema (para escalar)
    - El usuario indica que terminó la consulta
    
    Args:
        titulo: Título breve del problema
        prioridad: Nivel de prioridad (baja, media, alta, crítica)
        categoria: Categoría (redes, email, seguridad, hardware, software, otro)
        descripcion: Descripción detallada del problema
        solucion: Solución aplicada o pasos recomendados
    """
    ticket = SupportTicket(
        titulo=titulo,
        prioridad=prioridad,
        categoria=categoria,
        descripcion=descripcion,
        solucion=solucion
    )
    
    # Log del ticket creado
    logger.info("Ticket creado: %s", ticket.model_dump())
    
    return f"✅ Ticket #{hash(titulo) % 10000:04d} creado exitosamente:\n" \
           f"📋 **{titulo}** (Prioridad: {prioridad})\n" \
           f"🏷️ Categoría: {categoria}\n" \
           f"📝 El ticket ha sido registrado en el sistema."


def create_agent(session_id: str = None):
    """Crea el agente de soporte con conexión al MCP server remoto.
    """
    model = BedrockModel(
        model_id=MODEL_ID,
        guardrail_id=GUARDRAIL_ID if GUARDRAIL_ID else None,
        guardrail_version=GUARDRAIL_VERSION if GUARDRAIL_ID else None,
        guardrail_trace="enabled",
        guardrail_redact_input=True,
        guardrail_redact_output=True,
    )
    
    mcp_client = MCPClient(
        lambda: streamablehttp_client(
            url=MCP_SERVER_URL,
            headers={"Authorization": f"Bearer {MCP_AUTH_TOKEN}"},
        )
    )

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
        tools=[mcp_client, crear_ticket],
        plugins=[LoggingPlugin(), RetryPlugin()],
        session_manager=session_manager,
        conversation_manager=SummarizingConversationManager(
            summary_ratio=0.3,
            preserve_recent_messages=10,
        ),
    )

    return agent