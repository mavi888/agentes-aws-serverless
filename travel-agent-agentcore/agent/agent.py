"""
Agente asistente de viajes con AgentCore Memory.

Estrategias de memoria integradas:
  - SEMANTIC:         Hechos del usuario (destinos, historial, contexto)
  - USER_PREFERENCE:  Preferencias explícitas (aerolínea, asiento, clase, hotel)
"""

import os
import time
import logging
from datetime import datetime

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands.plugins import Plugin, hook
from strands.hooks import (
    BeforeToolCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
)

import boto3
from streamable_http_sigv4 import make_sigv4_auth
from mcp.client.streamable_http import streamablehttp_client

# AgentCore Memory
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

logger = logging.getLogger()
logger.setLevel("INFO")

# ── Configuración ──────────────────────────────────────────────────────────────
MODEL_ID   = os.environ.get("MODEL_ID",   "us.amazon.nova-lite-v1:0")
REGION     = os.environ.get("AWS_REGION", "us-east-1")

# Memory ID: se obtiene del Output del CDK stack después del deploy.
# Localmente se puede pasar por variable de entorno o hardcodearlo tras el deploy.
MEMORY_ID  = os.environ.get("TRAVEL_AGENT_MEMORY_ID", "")  # ← completar tras cdk deploy

# Strategy IDs: se generan al crear el Memory resource.
# Se obtienen llamando a list_memory_strategies(memoryId=MEMORY_ID) o desde la consola.
SEMANTIC_STRATEGY_ID         = os.environ.get("SEMANTIC_STRATEGY_ID",         "")
USER_PREFERENCE_STRATEGY_ID  = os.environ.get("USER_PREFERENCE_STRATEGY_ID",  "")

# ── SESSION_ID: identifica la conversación actual ─────────────────────────────
# Se genera una vez por proceso. El ACTOR_ID lo provee el caller (run_local, Lambda, etc.)
SESSION_ID = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Gateway URL — output del AgentCoreStack después del deploy
GATEWAY_URL = os.environ.get("TRAVEL_AGENT_GATEWAY_URL", "")


# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Sos un asistente personal de viajes con acceso a herramientas reales.

== IDENTIDAD DEL USUARIO ==
Tu user_id es: {actor_id}
Usá siempre este user_id cuando llames a get_trip_summary.

== HERRAMIENTAS DISPONIBLES ==

1. get_trip_summary(destination, user_id):
   - Retorna el resumen de un viaje ya reservado: vuelos, hotel y costo total.
   - Usala cuando el usuario quiera ver detalles de un viaje existente.
   - Siempre pasá user_id="{actor_id}" — es el identificador del usuario actual.
   - Los datos son de demo — en producción consultaría la base de datos real.

== (Fase 2 — próximamente) ==
2. search_flights(origin, destination, date, cabin_class)
3. book_flight(flight_id, passenger_name, passport_number)

== USO DE MEMORIA ==

Al INICIO de la conversación:
  - Usá search_memory para recuperar preferencias e historial del usuario.

Durante la conversación, guardá cosas importantes:
  - Aerolíneas preferidas → add_memory("Prefiere volar con JAL en clase business")
  - Preferencia de asiento → add_memory("Prefiere asiento de ventana en vuelos largos")
  - Destinos visitados → add_memory("Visitó Tokyo en agosto 2026")
  - Presupuesto → add_memory("Presupuesto para Europa: USD 5000")

Reglas:
  - No preguntés info que ya tenés en memoria.
  - Respondé en el idioma que usa el usuario.
  - Los datos de demo son ficticios — aclaralo si el usuario pregunta.
"""


# ── Plugin de logging ──────────────────────────────────────────────────────────
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
            logger.info("✅ %s completada (%.2fs)", event.tool_use["name"], elapsed)
        else:
            logger.warning("❌ %s falló (%.2fs)", event.tool_use["name"], elapsed)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _memory_configured() -> bool:
    """Retorna True si el Memory ID y los Strategy IDs están configurados."""
    return bool(MEMORY_ID and SEMANTIC_STRATEGY_ID and USER_PREFERENCE_STRATEGY_ID)


def _gateway_configured() -> bool:
    return bool(GATEWAY_URL)


def get_existing_memory(memory_client: MemoryClient, actor_id: str) -> str:
    """
    Recupera el contexto del usuario combinando dos estrategias:

    - User Preference → list_memory_records: son pocas preferencias consolidadas
      (aerolínea, asiento, clase de vuelo) y querés tenerlas TODAS sin filtro semántico.

    - Semantic → retrieve_memory_records con query genérica: los hechos semánticos
      pueden acumularse (destinos, conversaciones pasadas) y la búsqueda semántica
      filtra los más relevantes sin cortar arbitrariamente por posición.
    """
    semantic_namespace        = f"/strategies/{SEMANTIC_STRATEGY_ID}/actors/{actor_id}"
    user_preference_namespace = f"/strategies/{USER_PREFERENCE_STRATEGY_ID}/actors/{actor_id}"
    lines = []

    # User Preference → list: queremos TODAS las preferencias sin filtro
    try:
        resp = memory_client.list_memory_records(
            memoryId=MEMORY_ID,
            namespace=user_preference_namespace,
            maxResults=50,  # preferencias son pocas, 50 es más que suficiente
        )
        prefs = resp.get("memoryRecordSummaries", [])
        if prefs:
            lines.append("=== Preferencias del usuario ===")
            for p in prefs:
                text = p.get("content", {}).get("text", "")
                if text:
                    lines.append(f"- {text}")
    except Exception as e:
        logger.warning("No se pudo recuperar preferencias: %s", e)

    # Semantic → retrieve: búsqueda semántica para traer los hechos más relevantes
    # en usuarios con historial largo sin cortar por posición arbitrariamente
    try:
        resp = memory_client.retrieve_memory_records(
            memoryId=MEMORY_ID,
            namespace=semantic_namespace,
            searchCriteria={
                "searchQuery": "preferencias de viaje destinos visitados historial reservas"
            },
            maxResults=10,
        )
        facts = resp.get("memoryRecordSummaries", [])
        if facts:
            lines.append("=== Historial y contexto de viajes ===")
            for f in facts:
                text = f.get("content", {}).get("text", "")
                if text:
                    lines.append(f"- {text}")
    except Exception as e:
        logger.warning("No se pudo recuperar historial semántico: %s", e)

    return "\n".join(lines) if lines else ""


# ── Factory principal ──────────────────────────────────────────────────────────
def create_agent(actor_id: str, session_id: str = None):
    """
    Crea el Travel Agent con memoria integrada.

    Args:
        actor_id:   ID del usuario. Requerido — cada usuario tiene su propia memoria.
        session_id: ID de sesión. Si no se pasa, se genera uno por timestamp.

    Si TRAVEL_AGENT_MEMORY_ID no está configurado, el agente funciona
    sin memoria (útil para desarrollo antes del primer deploy).
    """
    _session_id = session_id or SESSION_ID

    model = BedrockModel(model_id=MODEL_ID)
    tools = []
    session_mgr = None
    memory_context = ""

    if _memory_configured():
        memory_client = MemoryClient(region_name=REGION)

        # Namespace semántico para el tool provider y session manager
        semantic_namespace = f"/strategies/{SEMANTIC_STRATEGY_ID}/actors/{actor_id}"

        # 1. Recuperar contexto previo para inyectar al system prompt
        memory_context = get_existing_memory(memory_client, actor_id)

        # 2. Tool Provider → herramientas search_memory / add_memory
        memory_tool_provider = AgentCoreMemoryToolProvider(
            memory_id=MEMORY_ID,
            actor_id=actor_id,
            session_id=_session_id,
            namespace=semantic_namespace,
            region=REGION,
        )
        tools = memory_tool_provider.tools

        # 3. Session Manager → guarda cada turno automáticamente
        agentcore_config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=_session_id,
            actor_id=actor_id,
        )
        session_mgr = AgentCoreMemorySessionManager(
            agentcore_memory_config=agentcore_config,
            region_name=REGION,
        )
        logger.info("✅ Memoria conectada | actor=%s | session=%s", actor_id, _session_id)
    else:
        logger.warning(
            "⚠️  TRAVEL_AGENT_MEMORY_ID no configurado — agente sin memoria. "
            "Completá las variables de entorno tras el cdk deploy."
        )

    # ── Conectar al Gateway via MCPClient con SigV4 ───────────────────────────
    # El Gateway usa authorizer_type="AWS_IAM" — requiere SigV4 en cada request.
    # make_sigv4_auth() crea el objeto auth que streamablehttp_client acepta directo.
    if _gateway_configured():
        auth = make_sigv4_auth(region=REGION)
        gateway_client = MCPClient(
            lambda: streamablehttp_client(GATEWAY_URL, auth=auth)
        )
        tools.append(gateway_client)
        logger.info("✅ Gateway conectado (SigV4): %s", GATEWAY_URL)
    else:
        logger.warning(
            "⚠️  TRAVEL_AGENT_GATEWAY_URL no configurado — sin herramientas de Gateway. "
            "Completá las variables de entorno tras el cdk deploy."
        )

    # Construir system prompt — si ya hay contexto inyectado, el agente
    # no necesita hacer search_memory al inicio (evita retrieve doble).
    if memory_context:
        full_system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"== CONTEXTO PREVIO DEL USUARIO ==\n"
            f"{memory_context}\n\n"
            "NOTA: Ya tenés el contexto del usuario inyectado arriba. "
            "No es necesario llamar search_memory al inicio — usá ese contexto directamente. "
            "Sí usá search_memory durante la conversación si necesitás buscar algo específico."
        )
    else:
        full_system_prompt = SYSTEM_PROMPT

    agent = Agent(
        model=model,
        system_prompt=full_system_prompt,
        tools=tools,
        session_manager=session_mgr,
        plugins=[LoggingPlugin()],
    )

    return agent
