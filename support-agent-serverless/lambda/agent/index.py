"""
Handler Lambda para el agente de soporte técnico IT.

Maneja los requests directos JSON.
"""

import json
import logging
import os
import urllib.request
import urllib.parse
import boto3

from agent import create_agent

logger = logging.getLogger()
logger.setLevel("INFO")


def handle_direct_request(body: str):
    """Maneja request directo JSON."""
    try:
        request = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "JSON inválido en el body"}),
        }

    user_message = request.get("message", "")
    if not user_message:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Campo 'message' requerido"}),
        }

    # Session ID para mantener el estado de la conversación
    session_id = request.get("session_id")

    try:
        agent = create_agent(session_id=session_id)
        result = agent(user_message)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "response": str(result),
                    "status": "ok",
                },
                ensure_ascii=False,
            ),
        }
    except Exception as e:
        logger.error("Error ejecutando agente: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": "Error interno del agente",
                    "detail": str(e),
                },
                ensure_ascii=False,
            ),
        }


def handler(event, context):
    logger.info("Evento recibido: %s", json.dumps(event, default=str))

    # Parsear el body
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    logger.info("Procesando como request directo")
    return handle_direct_request(body)