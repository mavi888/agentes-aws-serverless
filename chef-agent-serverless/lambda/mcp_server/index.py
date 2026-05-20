"""
MCP Server wrapping TheMealDB API.

Exposes tools to browse recipes by category/cuisine and get full recipe details.
Accessible via Streamable HTTP (Lambda Function URL).
"""

import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger()
logger.setLevel("INFO")

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"

TOOLS = [
    {
        "name": "buscar_por_categoria",
        "description": (
            "Search recipes by category or cuisine area using TheMealDB API. "
            "IMPORTANT: All values MUST be in English. "
            "Categories: Beef, Chicken, Dessert, Lamb, Miscellaneous, Pasta, Pork, Seafood, Side, Starter, Vegan, Vegetarian, Breakfast, Goat. "
            "Cuisine areas: American, British, Canadian, Chinese, Croatian, Dutch, Egyptian, Filipino, French, Greek, Indian, Irish, Italian, Jamaican, Japanese, Kenyan, Malaysian, Mexican, Moroccan, Polish, Portuguese, Russian, Spanish, Thai, Tunisian, Turkish, Vietnamese. "
            "Use 'type' parameter to specify if searching by 'category' or 'area'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Category or cuisine area name in English (e.g. 'Vegetarian', 'Chinese', 'Seafood', 'Italian')",
                },
                "type": {
                    "type": "string",
                    "enum": ["category", "area"],
                    "description": "Type of search: 'category' for food type (Vegetarian, Dessert, Pasta) or 'area' for cuisine origin (Chinese, Mexican, Italian)",
                },
            },
            "required": ["query", "type"],
        },
    },
    {
        "name": "obtener_receta",
        "description": (
            "Get full recipe details by meal ID: complete ingredient list with measurements, "
            "step-by-step cooking instructions, and YouTube video link."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "meal_id": {
                    "type": "string",
                    "description": "Recipe ID (obtained from buscar_por_categoria results)",
                }
            },
            "required": ["meal_id"],
        },
    },
]


def hacer_peticion_api(url: str):
    """Makes an HTTP request to TheMealDB API."""
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Error requesting {url}: {e}")
        return None


def buscar_por_categoria(query: str, tipo: str) -> str:
    """Search recipes by category or cuisine area."""
    if tipo == "category":
        url = f"{MEALDB_BASE_URL}/filter.php?c={urllib.parse.quote(query)}"
    else:
        url = f"{MEALDB_BASE_URL}/filter.php?a={urllib.parse.quote(query)}"

    data = hacer_peticion_api(url)

    if not data or not data.get("meals"):
        return f"No recipes found for '{query}' ({tipo})."

    meals = data["meals"][:10]
    label = f"category '{query}'" if tipo == "category" else f"cuisine '{query}'"
    resultado = f"Recipes for {label}:\n\n"
    for meal in meals:
        resultado += f"• {meal['strMeal']} (ID: {meal['idMeal']})\n"

    return resultado


def obtener_receta(meal_id: str) -> str:
    """Get full recipe details by ID."""
    url = f"{MEALDB_BASE_URL}/lookup.php?i={meal_id}"
    data = hacer_peticion_api(url)

    if not data or not data.get("meals"):
        return f"No recipe found with ID '{meal_id}'."

    meal = data["meals"][0]
    resultado = f"🍽️ {meal['strMeal']}\n"
    resultado += f"Category: {meal.get('strCategory', 'N/A')}\n"
    resultado += f"Cuisine: {meal.get('strArea', 'N/A')}\n\n"

    resultado += "Ingredients:\n"
    for i in range(1, 21):
        ingredient = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ingredient and ingredient.strip():
            resultado += f"• {measure.strip() if measure else ''} {ingredient.strip()}\n"

    resultado += f"\nInstructions:\n{meal.get('strInstructions', 'Not available')}\n"

    if meal.get("strYoutube"):
        resultado += f"\nVideo: {meal['strYoutube']}\n"

    return resultado


def handle_initialize(request_id):
    """Responds to MCP initialize message."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "mealdb-recipe-server",
                "version": "1.0.0",
            },
        },
    }


def handle_tools_list(request_id):
    """Responds to tools/list."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": TOOLS},
    }


def handle_tools_call(request_id, params):
    """Executes an MCP tool."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "buscar_por_categoria":
            resultado = buscar_por_categoria(
                arguments.get("query", ""),
                arguments.get("type", "category"),
            )
        elif tool_name == "obtener_receta":
            resultado = obtener_receta(arguments.get("meal_id", ""))
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": resultado}],
                "isError": False,
            },
        }

    except Exception as e:
        logger.error(f"Error executing {tool_name}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            },
        }


def handler(event, context):
    """Lambda handler for MCP server via Streamable HTTP."""
    logger.info("Event received: %s", json.dumps(event, default=str))

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

    # Notifications (no response needed)
    if "id" not in request:
        logger.info("Notification: %s", request.get("method", ""))
        return {
            "statusCode": 202,
            "headers": {"Content-Type": "application/json"},
            "body": "",
        }

    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    logger.info("Method: %s, ID: %s", method, request_id)

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
                "message": f"Method not supported: {method}",
            },
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }
