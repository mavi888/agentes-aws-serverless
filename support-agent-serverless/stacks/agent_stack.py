from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    BundlingOptions,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_ssm as ssm,
)
from constructs import Construct


class AgentStack(Stack):
    """Stack para el agente de soporte técnico.

    Despliega una Lambda con el agente Strands que:
    - Usa Bedrock (Nova Lite) como modelo
    - Se conecta al servidor MCP remoto para la base de conocimiento
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        mcp_endpoint: str,
        guardrail_id: str,
        guardrail_version: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Bucket S3 para sesiones del agente
        self.sessions_bucket = s3.Bucket(
            self,
            "Agent01SessionsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Parameter Store para el token de Telegram (encriptado)
        telegram_token_param = ssm.StringParameter(
            self,
            "TelegramBotTokenParameter",
            parameter_name="/support-agent/telegram/token01",
            string_value="PLACEHOLDER_TOKEN_UPDATE_MANUALLY",
            description="Token del bot de Telegram - Actualizar manualmente después del deploy",
        )

        # Lambda para el agente
        self.agent_function = _lambda.Function(
            self,
            "SupportAgentFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                "lambda/agent",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_13.bundling_image,
                    platform="linux/amd64",
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && "
                        "cp -r . /asset-output",
                    ],
                ),
            ),
            timeout=Duration.seconds(120),
            memory_size=512,
            environment={
                "MCP_SERVER_URL": mcp_endpoint,
                "MCP_AUTH_TOKEN": "mcp-secret-token-2024",
                "MODEL_ID": "us.amazon.nova-lite-v1:0",
                "SESSION_BUCKET": self.sessions_bucket.bucket_name,
                "TELEGRAM_TOKEN_PARAM": telegram_token_param.parameter_name,
                "GUARDRAIL_ID": guardrail_id,
                "GUARDRAIL_VERSION": guardrail_version
            },
        )

        # Permisos para invocar Bedrock
        self.agent_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        )

        # Permisos para leer/escribir sesiones en S3
        self.sessions_bucket.grant_read_write(self.agent_function)

        # Permisos para leer el token de Telegram
        telegram_token_param.grant_read(self.agent_function)


        # Function URL para testing directo
        function_url = self.agent_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[_lambda.HttpMethod.ALL],
                allowed_headers=["*"],
            ),
        )

        # API Gateway para el webhook de Telegram
        self.telegram_api = apigateway.RestApi(
            self,
            "TelegramWebhookApi01",
            rest_api_name="telegram-webhook01",
            description="Webhook para el bot de Telegram",
        )

        # Integración Lambda para el webhook (misma Lambda del agente)
        telegram_integration = apigateway.LambdaIntegration(
            self.agent_function
        )

        # Ruta POST /webhook para Telegram
        self.telegram_api.root.add_resource("webhook").add_method(
            "POST", telegram_integration
        )

        # Outputs
        CfnOutput(
            self,
            "AgentFunctionUrl",
            value=function_url.url,
            description="URL directa para testear la función Lambda del agente",
        )

        CfnOutput(
            self,
            "AgentFunctionName",
            value=self.agent_function.function_name,
            description="Nombre de la función Lambda del agente",
        )

        CfnOutput(
            self,
            "TelegramWebhookUrl01",
            value=f"{self.telegram_api.url}webhook",
            description="URL del webhook para configurar en Telegram",
        )