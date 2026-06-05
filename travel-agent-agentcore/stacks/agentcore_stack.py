from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
)
from aws_cdk.aws_bedrockagentcore import (
    CfnGateway,
    CfnGatewayTarget,
    CfnMemory,
    CfnApiKeyCredentialProvider
)

from constructs import Construct

# API key del demo — mismo valor que tiene el Authorizer Lambda del MCP server
AIRLINE_API_KEY = "airline-demo-key-2026"

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

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        lambda_arn: str,
        mcp_endpoint: str,
        **kwargs,
    ) -> None:
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

        # ── IAM Role para el Gateway ───────────────────────────────────────────
        gateway_role = iam.Role(
            self, "TravelAgentGatewayRole",
            role_name="TravelAgentGatewayRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Role del Gateway para invocar la Lambda get_trip_summary",
        )

        # Permiso para invocar la Lambda get_trip_summary
        gateway_role.add_to_policy(iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[lambda_arn],
        ))

         # Permisos para que el Gateway gestione las credenciales del Credential Provider:
        # - GetWorkloadAccessToken: obtiene el token de identidad interno del Gateway
        # - GetResourceApiKey: recupera el API key del Credential Provider
        # - secretsmanager:GetSecretValue: lee el secret interno que crea CfnApiKeyCredentialProvider
        #   (AgentCore guarda la key en un secret propio con prefijo bedrock-agentcore-identity)
        gateway_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetResourceApiKey",
            ],
            resources=["*"],
        ))

        gateway_role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=["arn:aws:secretsmanager:*:*:secret:bedrock-agentcore-identity*"],
        ))

        # ── API Key Credential Provider ────────────────────────────────────────
        # El Gateway usa este provider para inyectar el API key en cada request
        # al MCP server de aerolínea. El agente nunca ve la key.
        #
        # Demo: la key está hardcodeada en el template CDK (visible en CloudFormation).
        #
        # Producción: reemplazar api_key= por add_override para pasar api_key_secret_arn.
        # El schema de CloudFormation lo soporta pero el construct Python todavía no
        # lo expone. Con add_override la key vive en Secrets Manager y nadie la ve:
        #
        #   api_key_provider.add_override(
        #       "Properties.ApiKeySecretArn",
        #       "arn:aws:secretsmanager:us-east-1:123456789012:secret:airline-key"
        #   )
        api_key_provider = CfnApiKeyCredentialProvider(
            self, "AirlineApiKeyProvider",
            name="TravelAgentAirlineApiKey",
            api_key=AIRLINE_API_KEY,
        )

        # ── AgentCore Gateway ──────────────────────────────────────────────────
        # authorizer_type "AWS_IAM" → el agente se autentica con SigV4.
        # El agente usa streamablehttp_client_with_sigv4 para firmar cada request.
        gateway = CfnGateway(
            self, "TravelAgentGateway",
            name="TravelAgentGateway",
            description="Gateway del Travel Agent — Target Lambda",
            authorizer_type="AWS_IAM",
            protocol_type="MCP",
            role_arn=gateway_role.role_arn,
        )

        # ── Target1: Lambda get_trip_summary (sin Identity, solo IAM) ─────────
        lambda_target = CfnGatewayTarget(
            self, "TripSummaryLambdaTarget",
            name="TripSummaryTarget",
            description="Resumen de viaje del usuario — datos mock (en producción: base de datos)",
            gateway_identifier=gateway.ref,
            # Lambda targets requieren especificar el tipo de credencial explícitamente.
            # GATEWAY_IAM_ROLE indica que el Gateway usa su propio role IAM para invocar la Lambda.
            credential_provider_configurations=[
                CfnGatewayTarget.CredentialProviderConfigurationProperty(
                    credential_provider_type="GATEWAY_IAM_ROLE",
                )
            ],
            target_configuration=CfnGatewayTarget.TargetConfigurationProperty(
                mcp=CfnGatewayTarget.McpTargetConfigurationProperty(
                    lambda_=CfnGatewayTarget.McpLambdaTargetConfigurationProperty(
                        lambda_arn=lambda_arn,
                        tool_schema=CfnGatewayTarget.ToolSchemaProperty(
                            inline_payload=[
                                CfnGatewayTarget.ToolDefinitionProperty(
                                    name="get_trip_summary",
                                    description=(
                                        "Retorna el resumen de viaje del usuario: "
                                        "vuelos reservados, hotel y costo total. "
                                        "En producción consulta la base de datos del usuario."
                                    ),
                                    input_schema=CfnGatewayTarget.SchemaDefinitionProperty(
                                        type="object",
                                        properties={
                                            "destination": CfnGatewayTarget.SchemaDefinitionProperty(
                                                type="string",
                                                description="Destino del viaje (ej: 'Tokyo', 'Paris')",
                                            ),
                                            "user_id": CfnGatewayTarget.SchemaDefinitionProperty(
                                                type="string",
                                                description="ID único del usuario",
                                            ),
                                        },
                                        required=["destination", "user_id"],
                                    ),
                                )
                            ]
                        ),
                    )
                )
            ),
        )

        # ── Target 2: MCP server de aerolínea ─────────────────────────────────
        # El Gateway inyecta el API key en el header Authorization antes de
        # reenviar cada request al MCP server. El agente no necesita saber la key.
        CfnGatewayTarget(
            self, "AirlineMcpTarget",
            name="AirlineSearch1Target",
            description="MCP server de aerolínea — search_flights + book_flight v2",
            gateway_identifier=gateway.ref,
            credential_provider_configurations=[
                CfnGatewayTarget.CredentialProviderConfigurationProperty(
                    credential_provider_type="API_KEY",
                    credential_provider=CfnGatewayTarget.CredentialProviderProperty(
                        api_key_credential_provider=CfnGatewayTarget.ApiKeyCredentialProviderProperty(
                            provider_arn=api_key_provider.attr_credential_provider_arn,
                            credential_location="HEADER",
                            credential_parameter_name="Authorization",
                        )
                    ),
                )
            ],
            target_configuration=CfnGatewayTarget.TargetConfigurationProperty(
                mcp=CfnGatewayTarget.McpTargetConfigurationProperty(
                    mcp_server=CfnGatewayTarget.McpServerTargetConfigurationProperty(
                        endpoint=mcp_endpoint,
                    )
                )
            ),
        )

        # ── Outputs ────────────────────────────────────────────────────────────
        # Estos valores los necesitás para configurar el agente después del deploy.
        CfnOutput(
            self, "TravelAgentMemoryId",
            value=memory.ref,
            description="Memory ID — setear como TRAVEL_AGENT_MEMORY_ID",
            export_name="TravelAgentMemoryId",
        )

        CfnOutput(
            self, "TravelAgentGatewayId",
            value=gateway.ref,
            description="Gateway ID",
            export_name="TravelAgentGatewayId",
        )

        CfnOutput(
            self, "TravelAgentGatewayUrl",
            value=gateway.attr_gateway_url,
            description="Gateway URL — setear como TRAVEL_AGENT_GATEWAY_URL",
            export_name="TravelAgentGatewayUrl",
        )

        # Exponemos el memory_id como atributo para otros stacks
        self.memory_id = memory.ref
        self.gateway_id = gateway.ref
        self.gateway_url = gateway.attr_gateway_url