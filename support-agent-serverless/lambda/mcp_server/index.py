"""
Servidor MCP de base de conocimiento interna para soporte IT.

Expone la herramienta `buscar_solucion` como un servidor MCP
accesible via Streamable HTTP (Lambda Function URL).
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

# Base de conocimiento interna
KNOWLEDGE_BASE = {
    "vpn": (
        "Para problemas de VPN: 1) Verificar conexión a internet, "
        "2) Reiniciar cliente VPN, 3) Verificar credenciales, "
        "4) Contactar al equipo de redes si persiste."
    ),
    "email": (
        "Para problemas de email: 1) Verificar configuración IMAP/SMTP, "
        "2) Limpiar caché del cliente, 3) Verificar espacio en buzón, "
        "4) Probar acceso web."
    ),
    "password": (
        "Para reseteo de contraseña: 1) Ir al portal de autoservicio, "
        "2) Verificar identidad con MFA, "
        "3) Crear nueva contraseña siguiendo la política de seguridad."
    ),
    "impresora": (
        "Para problemas de impresora: 1) Verificar conexión de red, "
        "2) Reinstalar drivers, 3) Limpiar cola de impresión, "
        "4) Verificar toner/papel."
    ),
}

# Definición de herramientas MCP
TOOLS = [
    {
        "name": "buscar_solucion",
        "description": (
            "Busca en la base de conocimiento interna soluciones a problemas "
            "comunes de soporte IT. Categorías: vpn, email, password, impresora."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "problema": {
                    "type": "string",
                    "description": (
                        "Palabras clave del problema "
                        "(ej: 'vpn', 'email', 'password', 'impresora')"
                    ),
                }
            },
            "required": ["problema"],
        },
    }
]

def buscar_solucion(problema: str) -> str:
    """Busca solución en la base de conocimiento."""
    problema_lower = problema.lower()
    for key, solution in KNOWLEDGE_BASE.items():
        if key in problema_lower:
            return solution
    return (
        f"No encontré una solución específica para '{problema}'. "
        "Recomiendo escalar al equipo de soporte nivel 2."
    )


def handle_initialize(request_id):
    """Responde al mensaje initialize del protocolo MCP."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "support-knowledge-base",
                "version": "1.0.0",
            },
        },
    }

def handle_tools_list(request_id):
    """Responde a tools/list."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": TOOLS},
    }

def handle_tools_call(request_id, params):
    """Ejecuta una herramienta MCP."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "buscar_solucion":
        resultado = buscar_solucion(arguments.get("problema", ""))
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": resultado}],
                "isError": False,
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Herramienta no encontrada: {tool_name}",
        },
    }

def handler(event, context):
    """Handler Lambda para el servidor MCP via Streamable HTTP."""
    logger.info("Evento recibido: %s", json.dumps(event, default=str))

    # Parsear el body
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    try:
        request = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON"}),
        }

    # Manejar notificaciones (no requieren respuesta)
    if "id" not in request:
        method = request.get("method", "")
        logger.info("Notificación recibida: %s", method)
        return {
            "statusCode": 202,
            "headers": {"Content-Type": "application/json"},
            "body": "",
        }

    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    logger.info("Método: %s, ID: %s", method, request_id)

    # Router de métodos MCP
    if method == "initialize":
        response = handle_initialize(request_id)
    elif method == "tools/list":
        response = handle_tools_list(request_id)
    elif method == "tools/call":
        response = handle_tools_call(request_id, params)
    else:
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Método no soportado: {method}",
            },
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }