"""
Stack para el MCP server de aerolínea (mock).

Despliega:
  - Lambda con el servidor MCP (search_flights + book_flight)
  - Lambda Authorizer que valida el API key (hardcodeado — es un demo)
  - HTTP API Gateway v2 con la ruta /mcp protegida por el authorizer

El API key está hardcodeado en una variable de entorno de la Lambda Authorizer.
En producción viviría en Secrets Manager, pero para el demo no vale la pena el costo.
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_apigatewayv2_authorizers as authorizers,
)
from constructs import Construct

# API key del demo — mismo valor que usa el Credential Provider en AgentCoreStack
AIRLINE_API_KEY = "airline-demo-key-2026"


class McpStack(Stack):
    """Stack para el MCP server de aerolínea.

    Arquitectura idéntica al support-agent-serverless:
    Lambda + API Gateway HTTP + Lambda Authorizer con API key.

    El API key está hardcodeado como variable de entorno del Authorizer.
    El Gateway lo inyecta en el header Authorization via el Credential Provider.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Lambda: MCP server de aerolínea ───────────────────────────────────
        self.mcp_function = _lambda.Function(
            self,
            "AirlineMcpServerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda/airline_mcp"),
            timeout=Duration.seconds(30),
            memory_size=256,
            description="MCP server que simula una API de aerolínea externa",
        )

        # ── Lambda: Authorizer que valida el API key ───────────────────────────
        # La key está hardcodeada como variable de entorno — es un demo.
        # En producción se leería de Secrets Manager.
        authorizer_function = _lambda.Function(
            self,
            "AirlineAuthorizerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda/airline_authorizer"),
            timeout=Duration.seconds(10),
            memory_size=128,
            environment={
                "AIRLINE_API_KEY": AIRLINE_API_KEY,
            },
        )

        # ── HTTP API Gateway v2 ────────────────────────────────────────────────
        http_authorizer = authorizers.HttpLambdaAuthorizer(
            "AirlineMcpAuthorizer",
            authorizer_function,
            response_types=[authorizers.HttpLambdaResponseType.SIMPLE],
            identity_source=["$request.header.Authorization"],
        )

        self.api = apigwv2.HttpApi(
            self,
            "AirlineMcpApi",
            api_name="travel-agent-airline-mcp",
            description="MCP server de aerolínea para el Travel Agent demo",
        )

        integration = integrations.HttpLambdaIntegration(
            "AirlineMcpIntegration",
            self.mcp_function,
        )

        # Ruta POST /mcp protegida con el authorizer
        self.api.add_routes(
            path="/mcp",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
            authorizer=http_authorizer,
        )

        # URL completa del MCP server
        self.mcp_endpoint = f"{self.api.url}mcp"

        # ── Outputs ────────────────────────────────────────────────────────────
        CfnOutput(
            self, "AirlineMcpServerUrl",
            value=self.mcp_endpoint,
            description="URL del MCP server de aerolínea",
            export_name="AirlineMcpServerUrl",
        )
