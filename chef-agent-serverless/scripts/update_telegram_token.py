#!/usr/bin/env python3
"""
Script para actualizar el token de Telegram en Parameter Store de forma segura.

Uso:
    python scripts/update_telegram_token.py <token>
"""

import sys
import boto3

TELEGRAM_TOKEN_PARAM = "/chef-agent1/telegram/token"


def update_telegram_token(token: str):
    """Actualiza el token de Telegram en Parameter Store."""
    ssm_client = boto3.client("ssm")
    
    try:
        response = ssm_client.put_parameter(
            Name=TELEGRAM_TOKEN_PARAM,
            Value=token,
            Type="SecureString",
            Overwrite=True,
            Description="Token del bot de Telegram"
        )
        
        print(f"✅ Token actualizado exitosamente en {TELEGRAM_TOKEN_PARAM}")
        print(f"   Version: {response['Version']}")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando token: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Uso: python update_telegram_token.py <token>")
        print("Ejemplo: python update_telegram_token.py 8619226766:AAG-2Lj5DpLv4ZBe2CtPmjc73G1BkynJ1D8")
        sys.exit(1)
    
    token = sys.argv[1]
    
    # Validación básica del formato del token
    if ":" not in token or len(token) < 20:
        print("❌ El token no parece tener el formato correcto")
        print("   Formato esperado: XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        sys.exit(1)
    
    print(f"Actualizando token en Parameter Store...")
    
    if update_telegram_token(token):
        print("\n🤖 Token actualizado. Ya podés configurar el webhook:")
        print("   python scripts/setup_telegram_webhook.py <webhook_url>")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()