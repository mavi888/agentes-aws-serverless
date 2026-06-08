import os

import aws_cdk
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
)
from aws_cdk.aws_bedrockagentcore import (
    CfnGateway,
    CfnGatewayTarget,
    CfnMemory,
    CfnApiKeyCredentialProvider,
    Runtime,
    AgentRuntimeArtifact,
    AgentCoreRuntime,
)

from constructs import Construct

# API key del demo — mismo valor que tiene el Authorizer Lambda del MCP server
AIRLINE_API_KEY = "airline-demo-key-2026"

class AgentCoreStack(Stack):
    """
    Stack de AgentCore: Memory + Gateway + Runtime.

    Target 1 (Lambda):
      - get_trip_summary
      - El Gateway la invoca con su IAM role (GATEWAY_IAM_ROLE)

    Target 2 (MCP server de aerolínea):
      - search_flights + book_flight
      - El Gateway inyecta el API key en el header Authorization (API_KEY)
      - El agente nunca ve la key

    Runtime:
      - Hostea el Travel Agent (agent/main.py) como CodeZip en S3
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

        # ── IAM Role para el Runtime ───────────────────────────────────────────
        runtime_role = iam.Role(
            self, "TravelAgentRuntimeRole",
            role_name="TravelAgentRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Rol del AgentCore Runtime para el Travel Agent",
        )

        # Bedrock: invocar modelos (Nova Lite con cross-region inference prefix)
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            resources=[
                f"arn:aws:bedrock:*::foundation-model/*",
                f"arn:aws:bedrock:*:{self.account}:inference-profile/*",
            ],
        ))

        # AgentCore Gateway: invocar el Gateway del Travel Agent (SigV4)
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock-agentcore:InvokeGateway"],
            resources=["*"],
        ))

        # AgentCore Memory: leer y escribir memorias del usuario
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:GetMemoryRecord",
                "bedrock-agentcore:ListMemoryRecords",
                "bedrock-agentcore:RetrieveMemoryRecords",
                "bedrock-agentcore:PutMemoryRecords",
                "bedrock-agentcore:DeleteMemoryRecord",
                "bedrock-agentcore:ListEvents",
                "bedrock-agentcore:GetEvent",
                "bedrock-agentcore:DeleteEvent",
            ],
            resources=[
                f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:memory/{memory.attr_memory_id}",
                f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:memory/{memory.attr_memory_id}/*",
            ],
        ))

        # AgentCore Memory control plane: resolver Strategy IDs al arrancar
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock-agentcore:GetMemory"],
            resources=[memory.attr_memory_arn],
        ))

        # CloudWatch Logs
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            resources=["*"],
        ))

        # X-Ray — requerido para observability / traces
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets",
            ],
            resources=["*"],
        ))

        # S3: leer el asset de código subido por CDK
        runtime_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=["arn:aws:s3:::cdk-*"],
        ))

        # ── AgentCore Runtime — Direct Code Deployment (CodeZip) ──────────────
        # El Runtime CodeZip NO instala requirements.txt automáticamente —
        # las dependencias deben incluirse en el zip.
        # Usamos bundling para hacer `pip install` antes de zipar.
        # El Runtime rechaza __pycache__ compilados para otra arquitectura,
        # así que los eliminamos del output.
        agent_artifact = AgentRuntimeArtifact.from_code_asset(
            entrypoint=["opentelemetry-instrument","main.py"],
            path=os.path.join(os.path.dirname(__file__), "..", "agent"),
            runtime=AgentCoreRuntime.PYTHON_3_13,
            bundling=aws_cdk.BundlingOptions(
                image=aws_cdk.DockerImage.from_registry("python:3.13-slim"),
                command=[
                    "bash", "-c",
                    # 1. Copiar el código fuente al output
                    "cp -r /asset-input/. /asset-output/ && "
                    # 2. Instalar dependencias directamente en el output
                    "pip install -r /asset-output/requirements.txt -t /asset-output --quiet --no-compile && "
                    # 3. Eliminar __pycache__ y .pyc que el Runtime rechaza
                    "find /asset-output -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && "
                    "find /asset-output -name '*.pyc' -delete && "
                    "find /asset-output -name '*.pyo' -delete"
                ],
            ),
        )

        runtime = Runtime(
            self, "TravelAgentRuntime",
            runtime_name="TravelAgentRuntime",
            description="Travel Agent — Gateway MCP + Memory",
            execution_role=runtime_role,
            agent_runtime_artifact=agent_artifact,
            environment_variables={
                "TRAVEL_AGENT_GATEWAY_URL": gateway.attr_gateway_url,
                "TRAVEL_AGENT_MEMORY_ID":   memory.attr_memory_id,
                "MODEL_ID":                 "us.amazon.nova-lite-v1:0",
                "AWS_DEFAULT_REGION":       "us-east-1",
            },
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

        CfnOutput(
            self, "TravelAgentRuntimeArn",
            value=runtime.agent_runtime_arn,
            description="ARN del Runtime — usalo con test_runtime.py para invocar el agente",
            export_name="TravelAgentRuntimeArn",
        )

        # Exponemos el memory_id como atributo para otros stacks
        self.memory_id = memory.ref
        self.gateway_id = gateway.ref
        self.gateway_url = gateway.attr_gateway_url
        self.runtime_arn  = runtime.agent_runtime_arn