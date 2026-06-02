"""
Script para correr el agente chef localmente.

Uso:
    export AWS_REGION="us-east-1"
    export MCP_SERVER_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com/mcp"
    export MCP_AUTH_TOKEN="mcp-secret-token-2026"
    export SESSION_BUCKET="<nombre-del-bucket>"  # opcional, para persistir recetas
    export GUARDRAIL_ID="<tu-guardrail-id>"       # opcional, del output del cdk deploy
    export GUARDRAIL_VERSION="1"                   # opcional, default 1
    export KNOWLEDGE_BASE_ID="<ID del output>"
    python run_local.py
"""

import os
import logging
from agent import create_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

def main():
    print("👨‍� Chef Agent (local)")
    print("----------------------")
    print(f"🛡️  GUARDRAIL_ID:      {os.environ.get('GUARDRAIL_ID', '⚠️  NO SETEADO')}")
    print(f"🛡️  GUARDRAIL_VERSION: {os.environ.get('GUARDRAIL_VERSION', '⚠️  NO SETEADO')}")
    print(f"🛡️  KNOWLEDGE_BASE_ID: {os.environ.get('KNOWLEDGE_BASE_ID', '⚠️  NO SETEADO')}")
    print("Contame qué tenés en la heladera y te ayudo a cocinar!")
    print("Escribí 'salir' para terminar\n")

    agent = create_agent(session_id="local-session-5")

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
