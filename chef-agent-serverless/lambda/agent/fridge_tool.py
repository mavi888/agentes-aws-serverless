"""
Herramienta para gestionar el contenido de la heladera del usuario.

Persiste los datos en S3 como JSON, un archivo por usuario.
Estructura en S3: s3://{bucket}/fridges/{session_id}.json

Usa una factory function para evitar estado global del módulo
y prevenir contaminación entre invocaciones de Lambda.
"""

import json
import logging
from typing import List

import boto3
from strands import tool

logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")


def create_heladera_tool(bucket: str, session_id: str):
    """Factory que crea la tool de heladera con bucket y session_id fijos.

    Args:
        bucket: Nombre del bucket S3 donde persistir.
        session_id: ID del usuario/sesión actual.

    Returns:
        La función tool decorada, lista para pasar al agente.
    """

    s3_key = f"fridges/{session_id}.json"

    def _load() -> list:
        try:
            resp = s3_client.get_object(Bucket=bucket, Key=s3_key)
            data = json.loads(resp["Body"].read().decode("utf-8"))
            return data if isinstance(data, list) else []
        except s3_client.exceptions.NoSuchKey:
            return []
        except Exception as e:
            logger.error("Error cargando heladera: %s", e)
            return []

    def _save(items: list):
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json.dumps(items, ensure_ascii=False, indent=2),
            ContentType="application/json",
        )

    @tool
    def heladera(action: str, items: List[str] = []) -> str:
        """Gestiona el contenido de la heladera del usuario. Permite agregar, quitar y listar ingredientes.

        Args:
            action: Acción a realizar. Valores posibles: "agregar", "quitar", "listar".
            items: Lista de ingredientes (requerido para agregar/quitar). Ej: ["tomate", "cebolla", "leche"]

        Returns:
            Resultado de la operación con el estado actual de la heladera.
        """
        action = action.lower().strip()

        if action == "listar":
            current = _load()
            if not current:
                return "🧊 La heladera está vacía. ¡Hora de ir al super!"
            resultado = "🧊 Contenido de tu heladera:\n\n"
            for item in current:
                resultado += f"• {item}\n"
            resultado += f"\n📦 Total: {len(current)} items"
            return resultado

        elif action == "agregar":
            if not items:
                return "❌ Necesito saber qué ingredientes querés agregar."
            current = _load()
            current_lower = [i.lower() for i in current]
            agregados = []
            duplicados = []
            for item in items:
                if item.lower().strip() in current_lower:
                    duplicados.append(item)
                else:
                    current.append(item.strip())
                    current_lower.append(item.lower().strip())
                    agregados.append(item.strip())
            _save(current)
            msg = ""
            if agregados:
                msg += f"✅ Agregué: {', '.join(agregados)}"
            if duplicados:
                if msg:
                    msg += "\n"
                msg += f"ℹ️ Ya estaban: {', '.join(duplicados)}"
            return msg

        elif action == "quitar":
            if not items:
                return "❌ Necesito saber qué ingredientes querés quitar."
            current = _load()
            quitados = []
            no_encontrados = []
            for item in items:
                item_lower = item.lower().strip()
                found = [i for i in current if i.lower() == item_lower]
                if found:
                    current = [i for i in current if i.lower() != item_lower]
                    quitados.append(item)
                else:
                    no_encontrados.append(item)
            _save(current)
            msg = ""
            if quitados:
                msg += f"🗑️ Quité: {', '.join(quitados)}"
            if no_encontrados:
                if msg:
                    msg += "\n"
                msg += f"🤔 No encontré: {', '.join(no_encontrados)}"
            return msg

        else:
            return "❌ Acción no reconocida. Usá: 'agregar', 'quitar' o 'listar'."

    return heladera
