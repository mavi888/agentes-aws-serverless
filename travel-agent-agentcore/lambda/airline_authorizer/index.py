"""
Lambda Authorizer para el MCP server de aerolínea.

Valida el API key en el header Authorization comparándolo con
el valor hardcodeado en la variable de entorno AIRLINE_API_KEY.

Para producción se leería de Secrets Manager, pero para el demo
no vale la pena el costo extra.
"""

import os
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

# API key esperado — viene de la variable de entorno seteada en el stack
EXPECTED_KEY = os.environ.get("AIRLINE_API_KEY", "")


def handler(event, context):
    """Valida el API key del header Authorization.

    Para HTTP API Gateway v2 (payload format 2.0), retorna
    respuesta simple con isAuthorized: true/false.
    """
    logger.info("🔐 Authorizer invocado")

    # Extraer el token del header Authorization
    headers = event.get("headers", {})
    auth_header = headers.get("authorization", headers.get("Authorization", ""))

    # Soportar formato "Bearer <token>" o token directo
    token = auth_header
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]

    is_authorized = bool(token and EXPECTED_KEY and token == EXPECTED_KEY)

    if is_authorized:
        logger.info("✅ API key válido — acceso autorizado")
    else:
        logger.warning("⚠️ API key inválido o ausente")

    return {"isAuthorized": is_authorized}
