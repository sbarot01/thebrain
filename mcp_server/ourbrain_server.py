import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize Firebase
SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Initialize MCP server
mcp = FastMCP("OurBrain")


# ── Tool 1: Get all meals ──────────────────────────────────────────
@mcp.tool()
def get_meals() -> str:
    """Get all meals stored in OurKitchen, including name, cuisine, proteins, and ingredients."""
    meals_ref = db.collection('meals').stream()
    meals = []
    for doc in meals_ref:
        meal = doc.to_dict()
        meal['id'] = doc.id
        meals.append(meal)
    return json.dumps(meals, default=str)


# ── Tool 2: Get meal history with full meal details ────────────────
@mcp.tool()
def get_meal_history() -> str:
    """Get the full weekly meal history, with each planned meal enriched with its recipe details."""
    # Build meal lookup
    meals_ref = db.collection('meals').stream()
    meals_by_id = {}
    for doc in meals_ref:
        meals_by_id[doc.id] = doc.to_dict()

    # Fetch and enrich history
    history_ref = db.collection('history').stream()
    enriched_weeks = []
    for doc in history_ref:
        week = doc.to_dict()
        week_id = doc.id
        slots = []
        for key, value in week.items():
            if key == 'id':
                continue
            if isinstance(value, dict) and 'mealId' in value:
                meal = meals_by_id.get(value['mealId'], {})
                slots.append({
                    'date': value.get('dayKey'),
                    'slot': value.get('slot'),
                    'meal_name': meal.get('name', 'Unknown'),
                    'cuisine': meal.get('cuisine', ''),
                    'proteins': meal.get('proteins', []),
                    'ingredients': meal.get('ingredients', [])
                })
        slots.sort(key=lambda x: x['date'])
        enriched_weeks.append({'week_of': week_id, 'meals': slots})

    enriched_weeks.sort(key=lambda x: x['week_of'])
    return json.dumps(enriched_weeks, default=str)


# ── Tool 3: Get household preferences ─────────────────────────────
@mcp.tool()
def get_preferences() -> str:
    """Get household dietary preferences and restrictions."""
    prefs_ref = db.collection('prefs').stream()
    prefs = {}
    for doc in prefs_ref:
        prefs[doc.id] = doc.to_dict()
    return json.dumps(prefs, default=str)


# ── Tool 4: Get grocery list ───────────────────────────────────────
@mcp.tool()
def get_groceries() -> str:
    """Get the current grocery list."""
    groceries_ref = db.collection('groceries').stream()
    items = []
    for doc in groceries_ref:
        item = doc.to_dict()
        item['id'] = doc.id
        items.append(item)
    return json.dumps(items, default=str)


# ── Run the server ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting OurBrain MCP server...")
    mcp.run(transport='stdio')

