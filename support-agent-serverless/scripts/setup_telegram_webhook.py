#!/usr/bin/env python3
"""
Script para configurar el webhook de Telegram después del deploy.

Uso:
    python scripts/setup_telegram_webhook.py <webhook_url>
    
El token se lee desde AWS Parameter Store.
"""

import sys
import urllib.request
import urllib.parse
import json
import boto3

# Cliente SSM para leer el token
ssm_client = boto3.client("ssm")
TELEGRAM_TOKEN_PARAM = "/support-agent/telegram/token01"


def get_telegram_token():
    """Obtiene el token de Telegram desde Parameter Store."""
    print(f"🔍 Leyendo token desde Parameter Store: {TELEGRAM_TOKEN_PARAM}")
    try:
        response = ssm_client.get_parameter(
            Name=TELEGRAM_TOKEN_PARAM,
            WithDecryption=True
        )
        token = response["Parameter"]["Value"]
        print(f"✅ Token obtenido exitosamente (longitud: {len(token)})")
        return token
    except Exception as e:
        print(f"❌ Error obteniendo token desde Parameter Store: {e}")
        print(f"   Asegurate de que el parámetro {TELEGRAM_TOKEN_PARAM} existe")
        sys.exit(1)


def set_webhook(webhook_url: str):
    """Configura el webhook en Telegram."""
    print(f"🔧 Configurando webhook en Telegram...")
    token = get_telegram_token()
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    print(f"📡 Enviando request a: {url}")
    
    data = {
        "url": webhook_url,
    }
    
    req_data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=req_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    print(f"📤 Enviando datos: {data}")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(f"📥 Respuesta recibida: {result}")
            return result
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        return None


def get_webhook_info():
    """Obtiene información del webhook actual."""
    print(f"📋 Obteniendo info del webhook...")
    token = get_telegram_token()
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result
    except Exception as e:
        print(f"❌ Error obteniendo info del webhook: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Uso: python setup_telegram_webhook.py <webhook_url>")
        print("Ejemplo: python setup_telegram_webhook.py https://abc123.execute-api.us-east-1.amazonaws.com/prod/webhook")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    
    print(f"Configurando webhook: {webhook_url}")
    result = set_webhook(webhook_url)
    
    if result and result.get("ok"):
        print("✅ Webhook configurado exitosamente")
    else:
        print(f"❌ Error configurando webhook: {result}")
        sys.exit(1)
    
    print("\nInfo del webhook:")
    info = get_webhook_info()
    if info and info.get("ok"):
        webhook_info = info["result"]
        print(f"  URL: {webhook_info.get('url', 'No configurada')}")
        print(f"  Pending updates: {webhook_info.get('pending_update_count', 0)}")
        if webhook_info.get("last_error_message"):
            print(f"  Último error: {webhook_info['last_error_message']}")
    
    print(f"\n🤖 Tu bot está listo. Buscalo en Telegram y empezá a chatear!")


if __name__ == "__main__":
    main()