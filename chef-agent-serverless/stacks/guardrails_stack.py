from aws_cdk import Stack, CfnOutput
from aws_cdk.aws_bedrock import CfnGuardrail, CfnGuardrailVersion
from constructs import Construct


class GuardrailStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Crear el Guardrail con el construct L1 (CfnGuardrail)
        self.guardrail = CfnGuardrail(self, "ChefAgent1Guardrail",
            name="chef-agent1-guardrail",
            description="Guardrail para el agente chef agent",
            blocked_input_messaging=(
                "Solo puedo ayudarte con recetas y cocina. "
                "¿Qué querés cocinar hoy?"
            ),
            blocked_outputs_messaging=(
                 "No puedo responder eso. "
                "¿Hay alguna receta en la que pueda ayudarte?"
            ),
            # Content Filters
            content_policy_config=CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="HATE",
                        input_strength="HIGH",
                        output_strength="HIGH",
                    ),
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="INSULTS",
                        input_strength="HIGH",
                        output_strength="HIGH",
                    ),
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="SEXUAL",
                        input_strength="HIGH",
                        output_strength="HIGH",
                    ),
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="VIOLENCE",
                        input_strength="HIGH",
                        output_strength="HIGH",
                    ),
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="MISCONDUCT",
                        input_strength="HIGH",
                        output_strength="HIGH",
                    ),
                    CfnGuardrail.ContentFilterConfigProperty(
                        type="PROMPT_ATTACK",
                        input_strength="HIGH",
                        output_strength="NONE",
                    ),
                ]
            ),
            # Denied Topics
            topic_policy_config=CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    CfnGuardrail.TopicConfigProperty(
                        name="FueraDeCocina",
                        type="DENY",
                        definition=(
                            "Consultas ajenas a cocina, recetas, ingredientes o gastronomía. "
                            "Incluye deportes, tecnología, política, finanzas, chistes, geografía e historia."
                        ),
                        examples=[
                            "¿Cuál es la mejor acción de bolsa?",
                            "¿Quién ganó las elecciones?",
                            "¿Quién gana el campeonato del mundo?",
                            "Contame un chiste",
                            "¿Cuántos mundiales ganó Brasil?",
                        ],
                        input_enabled=True,
                        input_action="BLOCK",
                        output_enabled=True,
                        output_action="BLOCK",
                    ),
                ]
            ),
        )

        # Crear una versión (necesario para usar el guardrail en producción)
        # Para crear una nueva versión después de cambios, usar la CLI:
        # aws bedrock create-guardrail-version --guardrail-identifier <ID> --region us-east-1
        self.guardrail_version = CfnGuardrailVersion(self, "ChefAgent1GuardrailVersion",
            guardrail_identifier=self.guardrail.attr_guardrail_id,
            description="Versión inicial",
        )

        # Outputs
        CfnOutput(self, "ChefAgent1GuardrailId",
            value=self.guardrail.attr_guardrail_id,
        )
        CfnOutput(self, "ChefAgent1GuardrailVersionOutput",
            value=self.guardrail_version.attr_version,
        )

        # Exponer como propiedades del stack
        self.guardrail_id = self.guardrail.attr_guardrail_id
        self.guardrail_version_number = self.guardrail_version.attr_version
