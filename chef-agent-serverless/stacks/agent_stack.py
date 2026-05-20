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
    """Stack para el agente chef.

    Despliega una Lambda con el agente Strands que:
    - Usa Bedrock como modelo
    - Se conecta al servidor MCP remoto para obtener las recetas
    - Maneja tanto requests directos como webhooks de Telegram
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        mcp_endpoint: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Bucket S3 para sesiones del agente
        self.sessions_bucket = s3.Bucket(
            self,
            "Chef1AgentSessionsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Parameter Store para el token de Telegram (encriptado)
        telegram_token_param = ssm.StringParameter(
            self,
            "Chef1TelegramBotTokenParameter",
            parameter_name="/chef-agent1/telegram/token",
            string_value="PLACEHOLDER_TOKEN_UPDATE_MANUALLY",
            description="Token del bot de Telegram - Actualizar manualmente después del deploy",
        )

        # Lambda unificada: Agente + Telegram Bot
        self.agent_function = _lambda.Function(
            self,
            "Chef1SupportAgentFunction",
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
                "MCP_AUTH_TOKEN": "mcp-secret-token-2026",
                "MODEL_ID": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
                "SESSION_BUCKET": self.sessions_bucket.bucket_name,
                "TELEGRAM_TOKEN_PARAM": telegram_token_param.parameter_name,
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

        # API Gateway para el webhook de Telegram
        self.telegram_api = apigateway.RestApi(
            self,
            "Chef1TelegramWebhookApi",
            rest_api_name="chef-telegram-webhook",
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
            "Chef1TelegramWebhookUrl",
            value=f"{self.telegram_api.url}webhook",
            description="URL del webhook para configurar en Telegram",
        )

        CfnOutput(
            self,
            "Chef1TelegramTokenParameterName",
            value=telegram_token_param.parameter_name,
            description="Parámetro de SSM para actualizar con el token real de Telegram",
        )