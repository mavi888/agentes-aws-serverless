"""
Handler Lambda para el agente de asistente de chef

Maneja tanto webhooks de Telegram como requests directos JSON.
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

# Cliente SSM para leer parámetros
ssm_client = boto3.client("ssm")

# Configuración
TELEGRAM_TOKEN_PARAM = os.environ.get("TELEGRAM_TOKEN_PARAM", "")

# Cache del token (se lee una vez por cold start)
_telegram_token = None


def get_telegram_token():
    """Obtiene el token de Telegram desde Parameter Store."""
    global _telegram_token
    
    if _telegram_token is None and TELEGRAM_TOKEN_PARAM:
        try:
            response = ssm_client.get_parameter(
                Name=TELEGRAM_TOKEN_PARAM,
                WithDecryption=True
            )
            _telegram_token = response["Parameter"]["Value"]
        except Exception as e:
            logger.error("Error obteniendo token de Telegram: %s", str(e))
            # No fallar si no hay token configurado (para uso directo)
    
    return _telegram_token


def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje a Telegram usando la API."""
    token = get_telegram_token()
    if not token:
        logger.error("No hay token de Telegram configurado")
        return None
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text
    }
    
    req_data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=req_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error("Error enviando mensaje a Telegram: %s", str(e))
        return None


def handle_telegram_webhook(body: str):
    """Maneja webhook de Telegram."""
    try:
        update = json.loads(body)
        
        # Extraer el mensaje
        message = update.get("message")
        if not message:
            logger.info("Update sin mensaje, ignorando")
            return {"statusCode": 200}
        
        chat_id = message["chat"]["id"]
        user_message = message.get("text", "")
        
        if not user_message:
            send_telegram_message(chat_id, "Solo puedo procesar mensajes de texto.")
            return {"statusCode": 200}
        
        logger.info("Mensaje de Telegram chat_id %s: %s", chat_id, user_message)
        
        # Usar chat_id como session_id para mantener contexto
        session_id = f"telegram-{chat_id}"
        
        # Procesar con el agente
        try:
            agent = create_agent(session_id=session_id)
            agent_response = agent(user_message)
            
            # Enviar respuesta a Telegram
            send_telegram_message(chat_id, str(agent_response))
            
        except Exception as e:
            logger.error("Error procesando con agente: %s", str(e), exc_info=True)
            send_telegram_message(
                chat_id, 
                "Lo siento, hay un problema técnico. Intentá de nuevo en unos minutos."
            )
        
        return {"statusCode": 200}
        
    except Exception as e:
        logger.error("Error procesando webhook de Telegram: %s", str(e), exc_info=True)
        return {"statusCode": 500}


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
    """Handler unificado: webhook de Telegram o request directo."""
    logger.info("Evento recibido: %s", json.dumps(event, default=str))

    # Parsear el body
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    # Detectar si es webhook de Telegram o request directo
    # Los webhooks de Telegram tienen estructura específica con "update_id"
    try:
        parsed_body = json.loads(body) if body else {}
        is_telegram_webhook = "update_id" in parsed_body or "message" in parsed_body
    except:
        is_telegram_webhook = False

    if is_telegram_webhook:
        logger.info("Procesando como webhook de Telegram")
        return handle_telegram_webhook(body)
    else:
        logger.info("Procesando como request directo")
        return handle_direct_request(body)