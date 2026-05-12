"""
Lambda Authorizer para el API Gateway HTTP del servidor MCP.

Valida que el request incluya un token válido en el header Authorization.
Por ahora usa un token hardcodeado; en producción se recomienda usar
Secrets Manager o Parameter Store.
"""

import os
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

# Token esperado (hardcodeado para desarrollo)
EXPECTED_TOKEN = os.environ.get("AUTH_TOKEN", "mcp-secret-token-2024")


def handler(event, context):
    """Valida el token Bearer del header Authorization.

    Para HTTP API Gateway (payload format 2.0), retorna una respuesta
    simple con isAuthorized: true/false.
    """
    logger.info("Authorizer invocado")

    # Extraer el token del header Authorization
    headers = event.get("headers", {})
    auth_header = headers.get("authorization", "")

    # Soportar formato "Bearer <token>" o token directo
    token = auth_header
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]

    # Validar token
    is_authorized = token == EXPECTED_TOKEN

    if not is_authorized:
        logger.warning("Token inválido o ausente")
    else:
        logger.info("Token válido, acceso autorizado")

    return {
        "isAuthorized": is_authorized,
    }
