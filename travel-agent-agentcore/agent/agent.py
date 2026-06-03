"""
Agente asistente de viajes
"""

import os
import time
import logging

from strands import Agent
from strands.models import BedrockModel
from strands.plugins import Plugin, hook
from strands.hooks import (
    BeforeToolCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
)

logger = logging.getLogger()
logger.setLevel("INFO")

# Configuración desde variables de entorno
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

SYSTEM_PROMPT = """Sos un asistente personal de viajes. 
Tu trabajo es ayudar al usuario a planificar 
viajes y recordar sus preferencias a lo largo del tiempo.

Al inicio de cada conversación recibirás las preferencias conocidas del usuario 
como contexto. Usá esa información para personalizar tus respuestas — no preguntes 
por información que ya tenés.

Durante la conversación, aprendé activamente sobre las preferencias del usuario:
- Aerolíneas preferidas (programas de fidelidad, aerolíneas favoritas)
- Preferencias de asiento (ventana, pasillo, extra espacio)
- Clase de cabina (económica, business)
- Destinos favoritos o lugares que quiere visitar
- Estilo de viaje (solo vuelos directos, acepta escalas, viaja liviano, etc.)
- Preferencias de hotel (cadena, estrellas, ubicación)
- Cualquier otra preferencia relevante que mencione

Cuando aprendas algo nuevo sobre el usuario, reconocelo de forma natural — 
que no parezca un formulario.

Si no tenés contexto del usuario todavía, hacé algunas preguntas para conocer 
sus preferencias de viaje.
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


def create_agent(session_id: str = None):
    """Crea el agente de soporte con KB y Guardrail."""

    model = BedrockModel(
        model_id=MODEL_ID,
    )

    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[],
        plugins=[LoggingPlugin()]
    )

    return agent