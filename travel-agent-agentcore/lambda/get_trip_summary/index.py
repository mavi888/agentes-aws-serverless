"""
Lambda: get_trip_summary

Retorna un resumen de viaje ficticio para el demo.
Recibe destination y user_id como parámetros.

En producción esto consultaría la base de datos del usuario (DynamoDB, RDS, etc.)
para retornar sus vuelos reservados, hotel confirmado y costo total real.

El Gateway invoca esta Lambda via IAM — no hay auth token de por medio.
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

# ── Datos mock por destino ─────────────────────────────────────────────────────
# En producción se consultaría la DB del usuario con el user_id.
MOCK_TRIPS = {
    "tokyo": {
        "destination": "Tokyo, Japan",
        "flights": {
            "outbound": {
                "flight": "AA 175",
                "origin": "JFK",
                "destination": "NRT",
                "departure": "2026-08-10 11:30",
                "arrival": "2026-08-11 15:45",
                "class": "Economy",
            },
            "return": {
                "flight": "AA 176",
                "origin": "NRT",
                "destination": "JFK",
                "departure": "2026-08-20 17:00",
                "arrival": "2026-08-20 16:30",
                "class": "Economy",
            },
        },
        "hotel": {
            "name": "Park Hyatt Tokyo",
            "check_in": "2026-08-11",
            "check_out": "2026-08-20",
            "nights": 9,
            "room": "Deluxe Room",
        },
        "total_cost": 4850.00,
        "currency": "USD",
        "status": "confirmed",
    },
    "paris": {
        "destination": "Paris, France",
        "flights": {
            "outbound": {
                "flight": "AF 011",
                "origin": "JFK",
                "destination": "CDG",
                "departure": "2026-09-05 23:55",
                "arrival": "2026-09-06 13:30",
                "class": "Business",
            },
            "return": {
                "flight": "AF 012",
                "origin": "CDG",
                "destination": "JFK",
                "departure": "2026-09-12 10:00",
                "arrival": "2026-09-12 12:45",
                "class": "Business",
            },
        },
        "hotel": {
            "name": "Le Meurice",
            "check_in": "2026-09-06",
            "check_out": "2026-09-12",
            "nights": 6,
            "room": "Superior Room with Eiffel Tower View",
        },
        "total_cost": 9200.00,
        "currency": "USD",
        "status": "confirmed",
    },
    "default": {
        "destination": "Destino desconocido",
        "flights": {
            "outbound": {
                "flight": "XX 001",
                "origin": "JFK",
                "destination": "???",
                "departure": "2026-10-01 08:00",
                "arrival": "2026-10-01 16:00",
                "class": "Economy",
            },
        },
        "hotel": {
            "name": "Hotel genérico",
            "check_in": "2026-10-01",
            "check_out": "2026-10-07",
            "nights": 6,
            "room": "Standard",
        },
        "total_cost": 1500.00,
        "currency": "USD",
        "status": "pending",
    },
}


def handler(event, context):
    """Handler del Gateway AgentCore.

    El Gateway envía los parámetros de la herramienta MCP en el body del evento.
    Formato esperado: {"destination": "...", "user_id": "..."}
    """
    logger.info("✈️ get_trip_summary invocada | evento: %s", json.dumps(event, default=str))

    # Extraer parámetros — el Gateway puede enviarlos directamente o en body
    if isinstance(event, dict):
        destination = event.get("destination", "")
        user_id = event.get("user_id", "unknown")

        # Si vienen en body como string JSON
        if not destination and "body" in event:
            try:
                body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
                destination = body.get("destination", "")
                user_id = body.get("user_id", "unknown")
            except (json.JSONDecodeError, TypeError):
                pass
    else:
        destination = ""
        user_id = "unknown"

    logger.info("🗺️ Buscando resumen para destino='%s' user_id='%s'", destination, user_id)

    # Buscar en los datos mock por destino (case-insensitive)
    trip_key = destination.lower().split(",")[0].strip()
    trip_data = MOCK_TRIPS.get(trip_key, MOCK_TRIPS["default"])

    # Agregar el user_id al resultado para confirmar que llegó bien
    result = {
        **trip_data,
        "user_id": user_id,
        "note": (
            "Datos de demo. En producción, esta Lambda consultaría "
            f"la base de datos del usuario '{user_id}' para retornar "
            "reservas reales."
        ),
    }

    logger.info("✅ Retornando resumen de viaje para %s", destination)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result, ensure_ascii=False),
    }
