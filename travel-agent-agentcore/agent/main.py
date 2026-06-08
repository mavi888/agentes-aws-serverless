"""
Travel Agent — Entrypoint para AgentCore Runtime.
Versión diagnóstico: imports mínimos para aislar el problema.
"""

import os
import sys
import logging

# Logging básico a stdout para que el Runtime lo capture
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

logger.info("🚀 main.py iniciando — Python %s", sys.version)
logger.info("📦 PATH: %s", sys.path[:3])

# Intentar importar BedrockAgentCoreApp y loguear el resultado
try:
    from bedrock_agentcore import BedrockAgentCoreApp
    logger.info("✅ BedrockAgentCoreApp importado OK")
except Exception as e:
    logger.error("❌ Error importando BedrockAgentCoreApp: %s", e)
    # Fallback: si no está disponible el SDK, usamos un servidor HTTP mínimo
    # para que el Runtime no quede en estado de error permanente
    import json
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class MinimalHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"Healthy"}')

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            logger.info("POST %s body=%s", self.path, body[:200])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": f"Import error: {e}. Check CloudWatch logs."
            }).encode())

        def log_message(self, format, *args):
            logger.info(format, *args)

    logger.info("⚠️  Iniciando servidor HTTP fallback en puerto 8080")
    server = HTTPServer(("0.0.0.0", 8080), MinimalHandler)
    server.serve_forever()

# Si llegamos aquí, BedrockAgentCoreApp está disponible
try:
    from agent import create_agent
    logger.info("✅ create_agent importado OK")
except Exception as e:
    logger.error("❌ Error importando create_agent: %s", e)
    raise

app = BedrockAgentCoreApp()
_agent_cache: dict = {}


@app.entrypoint
def invoke(payload: dict, context) -> dict:
    prompt     = payload.get("prompt", "")
    actor_id   = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id") or (
        context.session_id if hasattr(context, "session_id") else "default"
    )

    logger.info("📨 invoke | actor=%s | prompt=%s", actor_id, prompt[:50])

    if not prompt:
        return {"response": "No recibí ningún mensaje."}

    cache_key = f"{actor_id}:{session_id}"

    try:
        if cache_key not in _agent_cache:
            logger.info("🆕 Creando agente | actor=%s", actor_id)
            _agent_cache[cache_key] = create_agent(actor_id=actor_id, session_id=session_id)
            logger.info("✅ Agente creado")

        result = _agent_cache[cache_key](prompt)
        response_text = str(result)
        logger.info("✅ Respuesta | chars=%d", len(response_text))
        return {"response": response_text}

    except Exception as e:
        logger.exception("❌ Error en invoke: %s", e)
        return {"response": f"Error: {type(e).__name__}: {e}"}


if __name__ == "__main__":
    logger.info("🏃 Iniciando app.run()")
    app.run()
