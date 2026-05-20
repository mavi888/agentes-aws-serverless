"""
Script para correr el agente chef localmente.

Uso:
    export MCP_SERVER_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com/mcp"
    export MCP_AUTH_TOKEN="mcp-secret-token-2026"
    export SESSION_BUCKET="<nombre-del-bucket>"  # opcional, para persistir recetas
    python run_local.py
"""

from agent import create_agent


def main():
    print("👨‍� Chef Agent (local)")
    print("----------------------")
    print("Contame qué tenés en la heladera y te ayudo a cocinar!")
    print("Escribí 'salir' para terminar\n")

    agent = create_agent(session_id="local-session-2")

    # Debug: mostrar herramientas disponibles
    print(f"🔧 Tools disponibles: {[t.tool_name if hasattr(t, 'tool_name') else str(t) for t in agent.tool_registry.get_all_tools_config()]}")
    print()

    while True:
        user_input = input("Vos: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n¡Buen provecho! 🍽️👋")
            break

        try:
            print()
            agent(user_input)
            print()
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            print("Intentá de nuevo.\n")


if __name__ == "__main__":
    main()
