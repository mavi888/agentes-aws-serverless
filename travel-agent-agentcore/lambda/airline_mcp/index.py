"""
MCP Server: Aerolínea (mock)

Simula una API externa de aerolínea que requiere autenticación con API key.
El API key llega en el header Authorization — lo valida el Lambda Authorizer.

Expone dos herramientas MCP:
  - search_flights:  Busca vuelos disponibles entre dos ciudades
  - book_flight:     Reserva un vuelo seleccionado

Todos los datos son ficticios — es un demo educativo.
El Gateway gestiona el API key via Identity; el agente nunca lo ve.
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel("INFO")

# ── Datos mock de vuelos ───────────────────────────────────────────────────────
MOCK_FLIGHTS = {
    ("jfk", "nrt"): [
        {
            "flight_id": "AA175-20260810",
            "airline": "American Airlines",
            "flight": "AA 175",
            "origin": "JFK",
            "destination": "NRT",
            "departure": "2026-08-10 11:30",
            "arrival": "2026-08-11 15:45",
            "duration": "14h 15m",
            "class": "Economy",
            "price": 850.00,
            "currency": "USD",
            "seats_available": 12,
        },
        {
            "flight_id": "JL004-20260810",
            "airline": "Japan Airlines",
            "flight": "JL 004",
            "origin": "JFK",
            "destination": "NRT",
            "departure": "2026-08-10 13:00",
            "arrival": "2026-08-11 17:05",
            "duration": "14h 05m",
            "class": "Economy",
            "price": 920.00,
            "currency": "USD",
            "seats_available": 5,
        },
    ],
    ("jfk", "cdg"): [
        {
            "flight_id": "AF011-BUS-20260905",
            "airline": "Air France",
            "flight": "AF 011",
            "origin": "JFK",
            "destination": "CDG",
            "departure": "2026-09-05 23:55",
            "arrival": "2026-09-06 13:30",
            "duration": "7h 35m",
            "class": "Business",
            "price": 3200.00,
            "currency": "USD",
            "seats_available": 3,
        },
        {
            "flight_id": "AF011-ECO-20260905",
            "airline": "Air France",
            "flight": "AF 011",
            "origin": "JFK",
            "destination": "CDG",
            "departure": "2026-09-05 23:55",
            "arrival": "2026-09-06 13:30",
            "duration": "7h 35m",
            "class": "Economy",
            "price": 680.00,
            "currency": "USD",
            "seats_available": 18,
        },
    ],
    # ── Rutas desde Buenos Aires ───────────────────────────────────────────────
    ("eze", "jfk"): [
        {
            "flight_id": "AA901-BUS-20261001",
            "airline": "American Airlines",
            "flight": "AA 901",
            "origin": "EZE",
            "destination": "JFK",
            "departure": "2026-10-01 23:45",
            "arrival": "2026-10-02 08:30",
            "duration": "10h 45m",
            "class": "Business",
            "price": 4100.00,
            "currency": "USD",
            "seats_available": 4,
        },
        {
            "flight_id": "AA901-ECO-20261001",
            "airline": "American Airlines",
            "flight": "AA 901",
            "origin": "EZE",
            "destination": "JFK",
            "departure": "2026-10-01 23:45",
            "arrival": "2026-10-02 08:30",
            "duration": "10h 45m",
            "class": "Economy",
            "price": 890.00,
            "currency": "USD",
            "seats_available": 22,
        },
        {
            "flight_id": "AR110-ECO-20261001",
            "airline": "Aerolíneas Argentinas",
            "flight": "AR 110",
            "origin": "EZE",
            "destination": "JFK",
            "departure": "2026-10-01 21:00",
            "arrival": "2026-10-02 06:15",
            "duration": "11h 15m",
            "class": "Economy",
            "price": 750.00,
            "currency": "USD",
            "seats_available": 8,
        },
    ],
    ("eze", "mad"): [
        {
            "flight_id": "IB6844-ECO-20261015",
            "airline": "Iberia",
            "flight": "IB 6844",
            "origin": "EZE",
            "destination": "MAD",
            "departure": "2026-10-15 13:30",
            "arrival": "2026-10-16 06:45",
            "duration": "13h 15m",
            "class": "Economy",
            "price": 720.00,
            "currency": "USD",
            "seats_available": 15,
        },
    ],
    ("eze", "cdg"): [
        {
            "flight_id": "AF228-ECO-20261020",
            "airline": "Air France",
            "flight": "AF 228",
            "origin": "EZE",
            "destination": "CDG",
            "departure": "2026-10-20 17:15",
            "arrival": "2026-10-21 11:30",
            "duration": "14h 15m",
            "class": "Economy",
            "price": 810.00,
            "currency": "USD",
            "seats_available": 10,
        },
    ],
}

# ── Definición de herramientas MCP ─────────────────────────────────────────────
TOOLS = [
    {
        "name": "search_flights",
        "description": (
            "Busca vuelos disponibles entre dos ciudades en una fecha dada. "
            "Retorna lista de vuelos con precios, horarios y disponibilidad."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Código IATA del aeropuerto de origen (ej: 'JFK', 'EZE')",
                },
                "destination": {
                    "type": "string",
                    "description": "Código IATA del aeropuerto de destino (ej: 'NRT', 'CDG')",
                },
                "date": {
                    "type": "string",
                    "description": "Fecha de viaje en formato YYYY-MM-DD",
                },
                "cabin_class": {
                    "type": "string",
                    "description": "Clase de cabina: Economy, Business, First (opcional)",
                },
            },
            "required": ["origin", "destination", "date"],
        },
    },
    {
        "name": "book_flight",
        "description": (
            "Reserva un vuelo seleccionado. Requiere el flight_id obtenido de search_flights. "
            "Retorna confirmación de reserva con PNR y detalles."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "flight_id": {
                    "type": "string",
                    "description": "ID del vuelo a reservar (obtenido de search_flights)",
                },
                "passenger_name": {
                    "type": "string",
                    "description": "Nombre completo del pasajero",
                },
                "passport_number": {
                    "type": "string",
                    "description": "Número de pasaporte del pasajero",
                },
            },
            "required": ["flight_id", "passenger_name", "passport_number"],
        },
    },
]


# ── Handlers de herramientas ───────────────────────────────────────────────────

def search_flights(origin: str, destination: str, date: str, cabin_class: str = None) -> dict:
    """Busca vuelos disponibles entre dos ciudades."""
    key = (origin.lower(), destination.lower())
    flights = MOCK_FLIGHTS.get(key, [])

    if cabin_class:
        flights = [f for f in flights if f["class"].lower() == cabin_class.lower()]

    if not flights:
        return {
            "found": False,
            "message": f"No se encontraron vuelos de {origin} a {destination} el {date}",
            "flights": [],
        }

    return {
        "found": True,
        "origin": origin.upper(),
        "destination": destination.upper(),
        "date": date,
        "total_results": len(flights),
        "flights": flights,
        "note": "Datos de demo — en producción se consultaría la API real de la aerolínea",
    }


def book_flight(flight_id: str, passenger_name: str, passport_number: str) -> dict:
    """Reserva un vuelo y retorna confirmación."""
    # Buscar el vuelo en los datos mock
    found_flight = None
    for flights in MOCK_FLIGHTS.values():
        for flight in flights:
            if flight["flight_id"] == flight_id:
                found_flight = flight
                break
        if found_flight:
            break

    if not found_flight:
        return {
            "success": False,
            "error": f"Vuelo {flight_id} no encontrado. Verificá el flight_id.",
        }

    # Generar PNR ficticio
    import hashlib
    pnr = hashlib.md5(f"{flight_id}{passenger_name}".encode()).hexdigest()[:6].upper()

    return {
        "success": True,
        "confirmation": {
            "pnr": pnr,
            "status": "CONFIRMED",
            "flight": found_flight["flight"],
            "airline": found_flight["airline"],
            "origin": found_flight["origin"],
            "destination": found_flight["destination"],
            "departure": found_flight["departure"],
            "arrival": found_flight["arrival"],
            "class": found_flight["class"],
            "passenger": passenger_name,
            "total_price": found_flight["price"],
            "currency": found_flight["currency"],
        },
        "note": "Reserva de demo — en producción se procesaría el pago y confirmaría con la aerolínea",
    }


# ── Handlers del protocolo MCP ─────────────────────────────────────────────────

def handle_initialize(request_id, params):
    """Responde al mensaje initialize del protocolo MCP.

    El Gateway envía la versión que quiere usar en params.protocolVersion.
    Respondemos con esa misma versión si la soportamos, o con la nuestra.
    El Gateway soporta: 2025-03-26 y 2025-06-18.
    """
    supported = {"2025-03-26", "2025-06-18"}
    requested = (params or {}).get("protocolVersion", "2025-03-26")
    version = requested if requested in supported else "2025-03-26"

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "airline-api", "version": "1.0.0"},
        },
    }


def handle_tools_list(request_id):
    """Responde a tools/list con las herramientas disponibles."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": TOOLS},
    }


def handle_tools_call(request_id, params):
    """Ejecuta la herramienta solicitada."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    logger.info("🔧 Ejecutando herramienta: %s | args: %s", tool_name, arguments)

    if tool_name == "search_flights":
        result = search_flights(
            origin=arguments.get("origin", ""),
            destination=arguments.get("destination", ""),
            date=arguments.get("date", ""),
            cabin_class=arguments.get("cabin_class"),
        )
    elif tool_name == "book_flight":
        result = book_flight(
            flight_id=arguments.get("flight_id", ""),
            passenger_name=arguments.get("passenger_name", ""),
            passport_number=arguments.get("passport_number", ""),
        )
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Herramienta no encontrada: {tool_name}"},
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
            "isError": False,
        },
    }


def handler(event, context):
    """Handler Lambda del MCP server via Streamable HTTP."""
    logger.info("✈️ MCP server de aerolínea | evento: %s", json.dumps(event, default=str))

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
            "body": json.dumps({"error": "JSON inválido"}),
        }

    # Notificaciones MCP (sin id) no requieren respuesta
    if "id" not in request:
        logger.info("📬 Notificación recibida: %s", request.get("method"))
        return {"statusCode": 202, "headers": {"Content-Type": "application/json"}, "body": ""}

    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    logger.info("📨 Método MCP: %s", method)

    # Router de métodos MCP
    if method == "initialize":
        response = handle_initialize(request_id, params)
    elif method == "tools/list":
        response = handle_tools_list(request_id)
    elif method == "tools/call":
        response = handle_tools_call(request_id, params)
    else:
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Método no soportado: {method}"},
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }
