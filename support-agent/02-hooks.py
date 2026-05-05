import time
from strands import Agent, tool
from strands.models import BedrockModel
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent, BeforeInvocationEvent

bedrock_Model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0")

# --- Plugin de logging ---
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


# --- Herramienta: base de conocimiento simple ---
knowledge_base = {
    "vpn": "Para problemas de VPN: 1) Verificar conexión a internet, 2) Reiniciar cliente VPN, 3) Verificar credenciales, 4) Contactar al equipo de redes si persiste.",
    "email": "Para problemas de email: 1) Verificar configuración IMAP/SMTP, 2) Limpiar caché del cliente, 3) Verificar espacio en buzón, 4) Probar acceso web.",
    "password": "Para reseteo de contraseña: 1) Ir al portal de autoservicio, 2) Verificar identidad con MFA, 3) Crear nueva contraseña siguiendo la política de seguridad.",
    "impresora": "Para problemas de impresora: 1) Verificar conexión de red, 2) Reinstalar drivers, 3) Limpiar cola de impresión, 4) Verificar toner/papel.",
}

@tool
def buscar_solucion(problema: str) -> str:
    """
    Search the internal knowledge base for solutions to common IT support issues.
    Use this when the user describes a technical problem.

    Args:
        problema: Keywords describing the issue (e.g., 'vpn', 'email', 'password', 'impresora')
    """
    problema_lower = problema.lower()
    for key, solution in knowledge_base.items():
        if key in problema_lower:
            return solution
    return f"No encontré una solución específica para '{problema}'. Recomiendo escalar al equipo de soporte nivel 2."


# --- Agente ---
soporte = Agent(
    system_prompt="""Sos un agente de soporte técnico de IT amigable y eficiente.

    Tu forma de trabajar:
    1. Escuchá el problema del usuario
    2. Buscá en la base de conocimiento usando la herramienta buscar_solucion
    3. Explicá la solución paso a paso de forma clara
    4. Si no encontrás solución, recomendá escalar al nivel 2

    Reglas:
    - Siempre hablá en español
    - Sé empático y profesional
    - Pedí más detalles si el problema no está claro
    """,
    tools=[buscar_solucion],
    model=bedrock_Model,
    plugins=[LoggingPlugin()]
)


# --- Sesión interactiva ---
def main():
    print("🎧 Soporte Técnico IT (escribí 'salir' para terminar)")
    print("----------------------------------------------------")
    print("¿En qué te puedo ayudar?\n")

    while True:
        user_input = input("Usuario: ")

        if user_input.lower() in ["salir", "exit", "quit"]:
            print("¡Gracias por contactar soporte! 👋")
            break

        print()
        soporte(user_input)
        print()


if __name__ == "__main__":
    main()