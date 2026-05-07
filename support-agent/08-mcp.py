import time
import uuid
from pydantic import BaseModel, Field
from typing import Literal
from strands import Agent, tool
from strands.models import BedrockModel
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent, BeforeInvocationEvent
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

bedrock_Model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0")

# --- Plugin de logging (igual que antes) ---
class LoggingPlugin(Plugin):
    name = "logging-plugin"

    def init_agent(self, agent):
        self._tool_start = None

    @hook
    def log_request(self, event: BeforeInvocationEvent) -> None:
        print("📨 --- Nuevo mensaje recibido ---")

    @hook
    def log_before_tool(self, event: BeforeToolCallEvent) -> None:
        self._tool_start = time.time()
        print(f"🔧 Usando herramienta: {event.tool_use['name']}")

    @hook
    def log_after_tool(self, event: AfterToolCallEvent) -> None:
        elapsed = time.time() - self._tool_start if self._tool_start else 0
        print(f"✅ Herramienta completada: {event.tool_use['name']} ({elapsed:.2f}s)")


# --- Herramienta: base de conocimiento (igual que antes) ---
knowledge_base = {
    "vpn": "Para problemas de VPN: 1) Verificar conexión a internet, 2) Reiniciar cliente VPN, 3) Verificar credenciales, 4) Contactar al equipo de redes si persiste.",
    "email": "Para problemas de email: 1) Verificar configuración IMAP/SMTP, 2) Limpiar caché del cliente, 3) Verificar espacio en buzón, 4) Probar acceso web.",
    "password": "Para reseteo de contraseña: 1) Ir al portal de autoservicio, 2) Verificar identidad con MFA, 3) Crear nueva contraseña siguiendo la política de seguridad.",
    "impresora": "Para problemas de impresora: 1) Verificar conexión de red, 2) Reinstalar drivers, 3) Limpiar cola de impresión, 4) Verificar toner/papel.",
}

# ---  (igual que antes) ---
@tool
def buscar_solucion(problema: str) -> str:
    """
    Search the internal knowledge base for solutions to common IT support issues.

    Args:
        problema: Keywords describing the issue (e.g., 'vpn', 'email', 'password', 'impresora')
    """
    problema_lower = problema.lower()
    for key, solution in knowledge_base.items():
        if key in problema_lower:
            return solution
    return f"No encontré una solución específica para '{problema}'. Recomiendo escalar al equipo de soporte nivel 2."


# --- Modelo Pydantic para tickets (igual que antes) ---
class SupportTicket(BaseModel):
    """A structured support ticket generated from a user interaction."""
    titulo: str = Field(description="Título breve y descriptivo del problema")
    prioridad: Literal["baja", "media", "alta", "crítica"] = Field(description="Nivel de prioridad del ticket")
    categoria: str = Field(description="Categoría del problema: redes, email, seguridad, hardware, software, otro")
    descripcion: str = Field(description="Descripción del problema reportado por el usuario")
    solucion: str = Field(description="Solución proporcionada o pasos a seguir")


# --- Función para generar ticket (igual que antes) ---
def crear_ticket(agent, conversacion: str) -> SupportTicket:
    """Genera un ticket estructurado a partir de la conversación."""
    result = agent(
        f"Basándote en esta conversación de soporte, generá un ticket:\n\n{conversacion}",
        structured_output_model=SupportTicket
    )
    return result.structured_output

# --- MCP: Documentación de AWS ---
aws_docs_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"],
        env={"FASTMCP_LOG_LEVEL": "ERROR"}
    )
))
# --- Loop interactivo (ahora recibe el agente como parámetro) ---
def main(soporte):
    print("¿En qué te puedo ayudar? (escribí 'salir' para terminar)\n")

    conversacion_actual = []

    while True:
        user_input = input("Usuario: ")

        if user_input.lower() in ["salir", "exit", "quit"]:
            if conversacion_actual:
                print("\n📝 Generando ticket de soporte...\n")
                ticket = crear_ticket(soporte, "\n".join(conversacion_actual))
                print(f"  Título:      {ticket.titulo}")
                print(f"  Prioridad:   {ticket.prioridad}")
                print(f"  Categoría:   {ticket.categoria}")
                print(f"  Descripción: {ticket.descripcion}")
                print(f"  Solución:    {ticket.solucion}")
            print("\n¡Gracias por contactar soporte! 👋")
            break

        conversacion_actual.append(f"Usuario: {user_input}")

        print()
        result = soporte(user_input)
        conversacion_actual.append(f"Agente: {result}")
        print()


if __name__ == "__main__":
    print("🎧 Soporte Técnico IT")
    print("--------------------")
    print("1. Nueva consulta")
    print("2. Continuar consulta anterior")
    choice = input("\nElegí una opción: ")

    if choice == "2":
        session_id = input("Ingresá tu ID de sesión: ")
    else:
        session_id = str(uuid.uuid4())[:8]
        print(f"\n📌 Tu ID de sesión es: {session_id}")
        print("   (Guardalo para retomar después)\n")

    session_manager = FileSessionManager(
        session_id=session_id,
        storage_dir="./soporte_sessions"
    )

    soporte = Agent(
        system_prompt="""Sos un agente de soporte técnico de IT amigable y eficiente.
            Tenés acceso a dos fuentes de información:
            1. buscar_solucion — Base de conocimiento interna para problemas comunes de IT (VPN, email, contraseñas, impresoras)
            2. Herramientas de documentación de AWS — Para cualquier pregunta sobre servicios de AWS (S3, Lambda, EC2, IAM, etc.)

            Tu forma de trabajar:
            1. Escuchá el problema del usuario
            2. Si el problema es sobre servicios de AWS, usá las herramientas de documentación de AWS
            3. Si el problema es de IT general, usá buscar_solucion
            4. Si no estás seguro, probá ambas fuentes
            5. Explicá la solución paso a paso de forma clara
            6. Si no encontrás solución en ninguna fuente, recomendá escalar al nivel 2

            Reglas:
            - Siempre hablá en español
            - Sé empático y profesional
            - Cuando uses documentación de AWS, citá la fuente
            """,
        tools=[buscar_solucion, aws_docs_client],
        model=bedrock_Model,
        plugins=[LoggingPlugin()],
        conversation_manager=SummarizingConversationManager(
            summary_ratio=0.3,
            preserve_recent_messages=10
        ),
        session_manager=session_manager
    )

    main(soporte)