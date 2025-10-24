import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
from pydantic import ValidationError
import json
from main.models import MenuItem, Customer, Order, Rating
from dotenv import load_dotenv
import os

load_dotenv()

# Get variables
mongo_url = os.getenv('MONGO_URI')
google_api_key = os.getenv('GOOGLE_API_KEY')
sheet_url = os.getenv('G_SHEET_URI')
db_name = os.getenv('DB_NAME')


# --- Setup Google Sheets ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
gs_client = gspread.authorize(creds)
spreadsheet = gs_client.open_by_url(sheet_url)
client = MongoClient(mongo_url)
db = client[db_name]

# --- Helper Function ---
def import_sheet_with_schema(sheet_name, collection, schema_class):
    ws = spreadsheet.worksheet(sheet_name)
    rows = ws.get_all_records()
    docs = []
    
    for row in rows:
        # Custom type fixing per known schema field
        if sheet_name == "menu":
            try:
                row["price"] = float(row.get("price", 0))
                row["isVegetarian"] = str(row.get("isVegetarian", "")).lower() in ("true", "1", "yes")
                row["availability"] = str(row.get("availability", "")).lower() in ("true", "1", "yes")
                # Parse lists
                if isinstance(row.get("ingredients"), str):
                    row["ingredients"] = [i.strip() for i in row["ingredients"].split(",") if i.strip()]
                if isinstance(row.get("tags"), str):
                    try:
                        row["tags"] = json.loads(row["tags"])
                    except:
                        row["tags"] = []
            except Exception as e:
                print("Menu item parsing error:", e)
        elif sheet_name == "customers":
            try:
                row["loyalty_points"] = int(row.get("loyalty_points", 0))
            except Exception:
                row["loyalty_points"] = 0
            # Always cast phone to string
            if "phone" in row:
                row["phone"] = str(row["phone"])

        elif sheet_name == "orders":
            if isinstance(row.get("menu_item_ids"), str):
                row["menu_item_ids"] = [i.strip() for i in row["menu_item_ids"].split(",") if i.strip()]
            try: row["total_price"] = float(row.get("total_price", 0))
            except Exception: row["total_price"] = 0
        elif sheet_name == "ratings":
            try: row["rating"] = int(row.get("rating", 0))
            except Exception: row["rating"] = 0

        # Validate using Pydantic schema
        try:
            valid_doc = schema_class(**row).dict()
            docs.append(valid_doc)
        except ValidationError as ve:
            print(f"Validation failed for row in {sheet_name}: {ve}")

    if docs:
        result = collection.insert_many(docs)
        print(f"{sheet_name}: Inserted {len(result.inserted_ids)} documents.")
    else:
        print(f"No valid docs for {sheet_name}")

# --- Import all collections ---
collections_and_schemas = {
    "menu": (db["menu"], MenuItem),
    "customers": (db["customers"], Customer),
    "orders": (db["orders"], Order),
    "ratings": (db["ratings"], Rating)
}

for sheet_name, (collection, schema) in collections_and_schemas.items():
    import_sheet_with_schema(sheet_name, collection, schema)

print("Import complete!")
