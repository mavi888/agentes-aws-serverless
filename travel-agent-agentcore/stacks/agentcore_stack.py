from aws_cdk import (
    Stack,
    CfnOutput,
)
from aws_cdk.aws_bedrockagentcore import CfnMemory
from constructs import Construct


class AgentCoreStack(Stack):
    """
    CDK Stack que provisiona AgentCore Memory para el Travel Agent.

    Estrategias de memoria:
    - SEMANTIC:         Memoria a largo plazo con búsqueda vectorial (RAG).
                        Persiste entre sesiones. Ideal para destinos visitados,
                        preferencias de viaje, historial de reservas.
    - USER_PREFERENCE:  Almacena preferencias explícitas del usuario
                        (asiento de ventana, aerolínea favorita, clase de vuelo, etc.)
                        Persiste entre sesiones y se actualiza automáticamente.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── AgentCore Memory con estrategias Semantic + User Preference ────────
        # event_expiry_duration: días que AgentCore retiene los eventos de sesión
        # antes de procesarlos y consolidarlos en las estrategias de memoria.
        memory = CfnMemory(
            self, "TravelAgentMemory",
            name="TravelAgentMemory",
            description="Memoria del Travel Agent con estrategias Semantic y User Preference",
            event_expiry_duration=30,
            memory_strategies=[
                # ── Estrategia 1: Semantic Memory ──────────────────────────
                # Extrae y almacena hechos clave de las conversaciones.
                # El agente recupera memoria relevante por similitud semántica.
                # Namespace: /strategies/{strategyId}/actors/{actorId}
                CfnMemory.MemoryStrategyProperty(
                    semantic_memory_strategy=CfnMemory.SemanticMemoryStrategyProperty(
                        name="TravelAgentSemanticMemory",
                        description=(
                            "Memoria semántica para el Travel Agent. "
                            "Almacena hechos clave: destinos visitados, preferencias "
                            "de viaje, historial de reservas y contexto del usuario."
                        ),
                    )
                ),
                # ── Estrategia 2: User Preference Memory ───────────────────
                # Captura preferencias explícitas del usuario.
                # Se actualiza automáticamente cuando el usuario las expresa.
                # Namespace: /strategies/{strategyId}/actors/{actorId}
                CfnMemory.MemoryStrategyProperty(
                    user_preference_memory_strategy=CfnMemory.UserPreferenceMemoryStrategyProperty(
                        name="TravelAgentUserPreferences",
                        description=(
                            "Preferencias del usuario para el Travel Agent. "
                            "Almacena: clase de vuelo preferida, asiento (ventana/pasillo), "
                            "aerolíneas favoritas, tipo de hotel, restricciones dietéticas "
                            "y cualquier preferencia de viaje expresada por el usuario."
                        ),
                    )
                ),
            ],
        )

        # ── Outputs ────────────────────────────────────────────────────────────
        # Estos valores los necesitás para configurar el agente después del deploy.
        CfnOutput(
            self, "TravelAgentMemoryId",
            value=memory.ref,
            description="Memory ID — setear como TRAVEL_AGENT_MEMORY_ID",
            export_name="TravelAgentMemoryId",
        )

        # Exponemos el memory_id como atributo para otros stacks
        self.memory_id = memory.ref
