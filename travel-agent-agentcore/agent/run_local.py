"""
Script para correr el agente localmente.

Uso:
    python run_local.py

"""

import os
from agent import create_agent


def main():
    print("🎧 Agente asistente de viajes - versión local")
    print("------------------------------")

    print("Escribí 'salir' para terminar\n")

    agent = create_agent()

    while True:
        user_input = input("Usuario: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n¡Gracias por contactar al asistente al viajero! 👋")
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
