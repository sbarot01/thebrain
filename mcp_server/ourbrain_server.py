import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json
from mcp.server.fastmcp import FastMCP
import voyageai
import chromadb


# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize Firebase
SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ── Voyage AI for embedding queries ────────────────────────────────
# We load the key from the same secrets.json the rest of the project uses.
SECRETS_PATH = "/Users/sagar/dev/TheBrain/secrets.json"
with open(SECRETS_PATH) as f:
    _secrets = json.load(f)
voyage_client = voyageai.Client(api_key=_secrets["VOYAGE_API_KEY"])

# ── ChromaDB for semantic meal search ──────────────────────────────
# Connects to the existing index built in Phase 3.
CHROMA_PATH = "/Users/sagar/dev/TheBrain/notebooks/ourbrain_chroma"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
meals_collection = chroma_client.get_collection("meals")

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

# ── Tool 5: Semantic meal search ───────────────────────────────────
@mcp.tool()
def search_meals_semantically(query: str, n_results: int = 3) -> str:
    """Search meals by semantic similarity for fuzzy/qualitative queries.
    
    Use this tool when the user asks about meals using descriptive language
    that doesn't match exact database fields, such as:
      - "something light and fresh"
      - "comfort food for a cold night"
      - "quick weeknight dinner ideas"
      - "meals similar to bibimbap" (when bibimbap isn't a structured filter)
    
    For exact filters (cuisine='Vietnamese', protein='chicken'), prefer the
    get_meals tool instead. This tool is best for vibes-based queries where
    structured filters wouldn't capture the intent.
    
    Returns the top n_results most semantically similar meals, with each
    meal's name, similarity distance (lower = more similar), and the indexed
    text chunk used for matching.
    """
    # Embed the query with the same model used during indexing
    query_vector = voyage_client.embed([query], model="voyage-2").embeddings[0]
    
    # Query ChromaDB
    results = meals_collection.query(
        query_embeddings=[query_vector],
        n_results=n_results
    )
    
    # Reformat into a clean list of dicts (matches the Phase 3 helper)
    meals = []
    for i in range(len(results["documents"][0])):
        meals.append({
            "name": results["metadatas"][0][i].get("name"),
            "distance": round(results["distances"][0][i], 4),
            "chunk": results["documents"][0][i]
        })
    
    return json.dumps(meals, default=str)


# ── Run the server ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting OurBrain MCP server...")
    mcp.run(transport='stdio')

