"""
Script para correr el Travel Agent localmente.

Configuración antes de correr:
  1. Hacer cdk deploy --all en travel-agent-agentcore/
  2. Copiar los IDs de los Outputs y setear las variables de entorno:

     export TRAVEL_AGENT_GATEWAY_URL="https://<gateway-id>.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
     export TRAVEL_AGENT_MEMORY_ID="TravelAgent1Memory-XXXXXXXX"
     export SEMANTIC_STRATEGY_ID="semantic_builtin_XXXXXXXXXX"
     export USER_PREFERENCE_STRATEGY_ID="userpreference_builtin_XXXXXXXXXX"
     export AWS_REGION="us-east-1"

  Para obtener el Gateway URL:
     aws bedrock-agentcore get-gateway --gateway-identifier <GATEWAY_ID>

  Para obtener los Strategy IDs:
     python -c "
     from bedrock_agentcore.memory import MemoryClient
     c = MemoryClient(region_name='us-east-1')
     r = c.list_memory_strategies(memoryId='<TU_MEMORY_ID>')
     [print(s['name'], '->', s['memoryStrategyId']) for s in r.get('memoryStrategies', [])]
     "

Uso:
    python run_local.py --actor marcia
    python run_local.py --actor juan
"""

import os
import argparse
from agent import (
    create_agent,
    MEMORY_ID,
    SESSION_ID,
    GATEWAY_URL,
    _memory_configured,
    _gateway_configured,
    get_existing_memory,
)


def print_banner(actor_id: str, session_id: str):
    print("\n" + "=" * 65)
    print("✈️  Travel Agent — Asistente Personal de Viajes + Gateway")
    print("=" * 65)
    print(f"  Actor    : {actor_id}")
    print(f"  Sesión   : {session_id}")

    if _gateway_configured():
        print(f"  Gateway  : ✅ {GATEWAY_URL[:60]}...")
    else:
        print("  Gateway  : ⚠️  No configurado (seteá TRAVEL_AGENT_GATEWAY_URL)")
        print("             Las herramientas de vuelo y resumen de viaje no van a funcionar")

    if _memory_configured():
        print(f"  Memoria  : ✅ {MEMORY_ID}")
    else:
        print("  Memoria  : ⚠️  No configurada (seteá TRAVEL_AGENT_MEMORY_ID y Strategy IDs)")

    print("=" * 65)
    print("  Escribí 'salir' para terminar")
    print("  Escribí 'memoria' para ver qué recuerdo de vos")
    print("=" * 65 + "\n")


def show_memory(actor_id: str):
    """Muestra la memoria almacenada para el actor actual."""
    if not _memory_configured():
        print("⚠️  Memoria no configurada.\n")
        return

    from bedrock_agentcore.memory import MemoryClient
    client = MemoryClient(region_name=os.environ.get("AWS_REGION", "us-east-1"))
    context = get_existing_memory(client, actor_id)

    if context:
        print("\n🧠 Lo que sé de vos:")
        print(context)
        print()
    else:
        print("\n🧠 Todavía no tengo nada guardado sobre vos.\n")


def main():
    parser = argparse.ArgumentParser(description="Travel Agent local runner")
    parser.add_argument(
        "--actor", required=True,
        help="ID único del usuario. Cada persona tiene su propia memoria. Ej: --actor marcia"
    )
    args = parser.parse_args()

    actor_id = args.actor
    agent = create_agent(actor_id=actor_id)

    print_banner(actor_id, SESSION_ID)

    while True:
        try:
            user_input = input("Usuario: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n¡Hasta la próxima! ✈️\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n¡Gracias por usar el Travel Agent! ✈️\n")
            break

        if user_input.lower() == "memoria":
            show_memory(actor_id)
            continue

        try:
            print()
            agent(user_input)
            print()
        except Exception as e:
            print(f"\n⚠️  Error: {e}\n")


if __name__ == "__main__":
    main()
