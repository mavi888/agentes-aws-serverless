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


class McpStack(Stack):
    """Stack para el servidor MCP de meal db.

    Despliega una Lambda con API Gateway HTTP que expone las herramientas
    de meal db como un servidor MCP remoto.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda para el servidor MCP
        self.mcp_function = _lambda.Function(
            self,
            "McpMeal1ServerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda/mcp_server"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "LOG_LEVEL": "INFO",
            },
        )

        # Lambda Authorizer para validar token
        authorizer_function = _lambda.Function(
            self,
            "McpMeal1AuthorizerFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda/authorizer"),
            timeout=Duration.seconds(10),
            memory_size=128,
            environment={
                "AUTH_TOKEN": "mcp-secret-token-2026",
            },
        )

        # Authorizer HTTP API Gateway
        http_authorizer = authorizers.HttpLambdaAuthorizer(
            "McpMeal1Authorizer",
            authorizer_function,
            response_types=[authorizers.HttpLambdaResponseType.SIMPLE],
            identity_source=["$request.header.Authorization"],
        )

        # API Gateway HTTP
        self.api = apigwv2.HttpApi(
            self,
            "McpMeal1Api",
            api_name="support-mcp-meal-server",
            description="API para el servidor MCP de soporte",
        )

        # Integración Lambda
        integration = integrations.HttpLambdaIntegration(
            "McpMeal1Integration",
            self.mcp_function,
        )

        # Ruta POST /mcp (endpoint MCP protegido con authorizer)
        self.api.add_routes(
            path="/mcp",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
            authorizer=http_authorizer,
        )

        # URL del MCP server
        self.mcp_endpoint = f"{self.api.url}mcp"

        # Outputs
        CfnOutput(
            self,
            "McpMeal1ServerUrl",
            value=self.mcp_endpoint,
            description="URL del servidor MCP meal de soporte",
        )
