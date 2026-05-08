import time
import uuid
import logging
from typing import List, Literal
from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent, BeforeInvocationEvent
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import calculator, current_time

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


# Lista de ingredientes en memoria
available_ingredients = []

@tool
def mi_heladera(action: str, ingredients: str = "") -> str:
    """
    Manage the user's available ingredients list (their fridge).
    Use this tool whenever the user mentions ingredients they have,
    wants to check what's available, or needs to update their list.

    Args:
        action: The action to perform. Must be one of:
            - 'agregar': Add ingredients to the list
            - 'quitar': Remove an ingredient from the list
            - 'listar': Show all available ingredients
            - 'limpiar': Clear the entire list
        ingredients: Comma-separated list of ingredients.
            Required for 'agregar' and 'quitar'.
            Not needed for 'listar' and 'limpiar'.

    Returns:
        A message confirming the action performed and the current state of the list.
    """
    global available_ingredients

    if action == "agregar":
        if not ingredients:
            return "Error: necesito saber qué ingredientes agregar."
        new_items = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
        added = []
        for item in new_items:
            if item not in available_ingredients:
                available_ingredients.append(item)
                added.append(item)
        if added:
            return f"Agregué: {', '.join(added)}. Heladera actual: {', '.join(available_ingredients)}"
        return f"Esos ingredientes ya estaban en la lista. Heladera actual: {', '.join(available_ingredients)}"

    elif action == "quitar":
        if not ingredients:
            return "Error: necesito saber qué ingrediente quitar."
        item = ingredients.strip().lower()
        if item in available_ingredients:
            available_ingredients.remove(item)
            remaining = ', '.join(available_ingredients) if available_ingredients else "vacía"
            return f"Quité '{item}'. Heladera actual: {remaining}"
        return f"'{item}' no está en la heladera. Ingredientes disponibles: {', '.join(available_ingredients)}"

    elif action == "listar":
        if not available_ingredients:
            return "La heladera está vacía. Decime qué ingredientes tenés."
        return f"Ingredientes disponibles: {', '.join(available_ingredients)}"

    elif action == "limpiar":
        available_ingredients.clear()
        return "Listo, la heladera está vacía."

    return f"Error: acción '{action}' no reconocida. Usá 'agregar', 'quitar', 'listar' o 'limpiar'."

# --- NUEVO: Modelo Pydantic para recetas ---
class Recipe(BaseModel):
    """A structured recipe generated from the conversation."""
    nombre: str = Field(description="Nombre de la receta")
    ingredientes: List[str] = Field(description="Lista de ingredientes con cantidades")
    pasos: List[str] = Field(description="Pasos de preparación en orden")
    tiempo_preparacion: str = Field(description="Tiempo estimado de preparación")
    porciones: int = Field(description="Cantidad de porciones")
    dificultad: Literal["fácil", "media", "difícil"] = Field(description="Nivel de dificultad")


# --- NUEVO: Función para generar receta estructurada ---
def generar_receta(agent) -> Recipe | None:
    """Genera una receta estructurada a partir de la conversación."""
    try:
        result = agent(
            "Generá la receta que discutimos en esta conversación.",
            structured_output_model=Recipe
        )
        receta = result.structured_output
        if receta:
            print(f"  📖 {receta.nombre}")
            print(f"  ⏱️  {receta.tiempo_preparacion} | 🍽️ {receta.porciones} porciones | {receta.dificultad}")
            print(f"  🥗 Ingredientes:")
            for ing in receta.ingredientes:
                print(f"     - {ing}")
            print(f"  👨‍🍳 Pasos:")
            for i, paso in enumerate(receta.pasos, 1):
                print(f"     {i}. {paso}")
            print()
        return receta
    except Exception as e:
        print(f"⚠️ No se pudo generar la receta: {e}")
        return None


def main():
    print("🧑‍🍳 Chef Assistant 2.0")
    print("---------------------")
    print("1. Nueva sesión")
    print("2. Continuar sesión anterior")
    choice = input("\nElegí una opción: ")

    if choice == "2":
        session_id = input("Ingresá tu ID de sesión: ")
    else:
        session_id = str(uuid.uuid4())[:8]
        print(f"\n📌 Tu ID de sesión es: {session_id}")
        print("   (Guardalo para retomar después)\n")

    # NUEVO: Session manager
    session_manager = FileSessionManager(
        session_id=session_id,
        storage_dir="./chef_sessions"
    )

    chef = Agent(
        system_prompt="""Sos un chef profesional y amigable que ayuda a las personas a cocinar 
        con lo que tienen disponible en su heladera.

        Tu forma de trabajar:
        1. Primero preguntá qué ingredientes tiene el usuario y agregalos a la heladera usando la herramienta mi_heladera
        2. Usá current_time para saber qué hora es y sugerir recetas apropiadas al momento del día (desayuno, almuerzo, merienda, cena)
        3. Cuando sugieras recetas, basate en los ingredientes disponibles en la heladera
        4. Cuando el usuario diga para cuántas personas cocina, usá calculator para ajustar las cantidades de ingredientes

        Reglas:
        - Siempre hablá en español
        - Sé práctico y directo con las sugerencias
        - Si el usuario no tiene suficientes ingredientes para una receta, sugerí alternativas o decile qué le falta
        - Cuando ajustes cantidades, mostrá el cálculo claramente
        - Sé creativo pero realista con las combinaciones de ingredientes
        """,
        tools=[current_time, calculator, mi_heladera],
        plugins=[LoggingPlugin()],
        conversation_manager=SummarizingConversationManager(
            summary_ratio=0.3,
            preserve_recent_messages=10
        ),
        session_manager=session_manager
    )

    while True:
        user_input = input("Vos: ")

        if user_input.lower() in ["salir", "exit", "quit"]:

            # NUEVO: Generar receta estructurada si hubo conversación
            if chef.messages:
                print("\n📝 Generando receta estructurada...\n")
                generar_receta(chef)

            print("¡Buen provecho! 👋")
            break
        

        print()
        chef(user_input)
        print()


if __name__ == "__main__":
    main()