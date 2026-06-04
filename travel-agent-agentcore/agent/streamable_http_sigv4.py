"""
Helper para conectar al AgentCore Gateway con autenticación SigV4.

El Gateway con authorizer_type="AWS_IAM" requiere que cada request
esté firmado con SigV4. Este módulo usa httpx-aws-auth para generar
el objeto auth que streamablehttp_client acepta directamente.

Uso:
    from streamable_http_sigv4 import make_sigv4_auth
    from strands.tools.mcp import MCPClient
    from mcp.client.streamable_http import streamablehttp_client

    auth = make_sigv4_auth()
    mcp_client = MCPClient(
        lambda: streamablehttp_client(GATEWAY_URL, auth=auth)
    )
"""

import os

import boto3
from httpx_aws_auth import AwsCredentials, AwsSigV4Auth


def make_sigv4_auth(
    service: str = "bedrock-agentcore",
    region: str = None,
    session: boto3.Session = None,
) -> AwsSigV4Auth:
    """
    Crea un objeto auth SigV4 compatible con httpx / streamablehttp_client.

    La región se resuelve en este orden:
      1. Parámetro `region` si se pasa explícitamente
      2. Variable de entorno AWS_REGION
      3. Variable de entorno AWS_DEFAULT_REGION
      4. Default: "us-east-1"

    Args:
        service: Nombre del servicio AWS. Default: "bedrock-agentcore"
        region:  Región AWS. Si es None, se lee de las variables de entorno.
        session: boto3.Session a usar. Si es None, usa las credenciales del entorno.

    Returns:
        AwsSigV4Auth listo para pasarle a streamablehttp_client(url, auth=...)
    """
    _region = (
        region
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )

    _session = session or boto3.Session()
    creds = _session.get_credentials().get_frozen_credentials()

    return AwsSigV4Auth(
        credentials=AwsCredentials(
            access_key=creds.access_key,
            secret_key=creds.secret_key,
            session_token=creds.token,
        ),
        service=service,
        region=_region,
    )
