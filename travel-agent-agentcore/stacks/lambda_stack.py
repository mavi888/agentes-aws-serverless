"""
Stack para la Lambda get_trip_summary.

Despliega una Lambda independiente que simula retornar un resumen de viaje.
En producción, esta Lambda consultaría la base de datos del usuario.
El Gateway la invoca directamente via IAM — sin Identity.
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
)
from constructs import Construct


class LambdaStack(Stack):
    """Stack independiente para la Lambda get_trip_summary.

    Expone el ARN de la Lambda para que el GatewayStack lo consuma
    al configurar el Target Lambda del Gateway.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Lambda: get_trip_summary ───────────────────────────────────────────
        # Retorna datos de viaje ficticios (mock).
        # En producción consultaría DynamoDB u otro storage del usuario.
        self.trip_summary_function = _lambda.Function(
            self,
            "GetTripSummaryFunction",
            function_name="get_trip_summary",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda/get_trip_summary"),
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Retorna un resumen de viaje ficticio para el demo del Gateway",
        )

        # ── Outputs ────────────────────────────────────────────────────────────
        CfnOutput(
            self, "TripSummaryFunctionArn",
            value=self.trip_summary_function.function_arn,
            description="ARN de la Lambda get_trip_summary — se usa en el Gateway Target",
            export_name="TripSummaryFunctionArn",
        )
