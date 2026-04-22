import logging
from strands import Agent, tool
from strands_tools import calculator, current_time

# (Opcional) Debug logging
# logging.getLogger("strands").setLevel(logging.DEBUG)
# logging.basicConfig(
#     format="%(levelname)s | %(name)s | %(message)s",
#     handlers=[logging.StreamHandler()]
# )

# --- Tu herramienta personalizada ---
@tool
def mi_heladera(action: str, ingredients: str = "") -> str:
    """
    [Tu docstring acá — describí bien qué hace, los parámetros y las acciones]
    """
    # Tu implementación acá
    pass

# --- Tu agente ---
chef = Agent(
    system_prompt="""[Tu system prompt acá]""",
    tools=[current_time, calculator, mi_heladera]
)

# --- Sesión interactiva ---
def main():
    print("🧑‍🍳 Chef Assistant (escribí 'salir' para terminar)")
    print("------------------------------------------------")
    
    while True:
        user_input = input("\nVos: ")
        
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("¡Buen provecho! 👋")
            break
        
        print()
        chef(user_input)

if __name__ == "__main__":
    main()