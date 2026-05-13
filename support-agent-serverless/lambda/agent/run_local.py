"""
Script para correr el agente de soporte localmente.

Uso:
    export MCP_SERVER_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com/mcp"
    export MCP_AUTH_TOKEN="mcp-secret-token-2024"
    python run_local.py
"""

from agent import create_agent


def main():
    print("🎧 Soporte Técnico IT (local)")
    print("------------------------------")
    print("Escribí 'salir' para terminar\n")

    agent = create_agent()

    while True:
        user_input = input("Usuario: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n¡Gracias por contactar soporte! 👋")
            break

        try:
            print()
            result = agent(user_input)
            print()
        except Exception as e:
            print(f"\n⚠️ Ocurrió un error: {e}")
            print("Podés seguir conversando, intentá de nuevo.\n")


if __name__ == "__main__":
    main()
