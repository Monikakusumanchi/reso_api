from pymongo import MongoClient
from faker import Faker
from bson import ObjectId
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os
import time
from google import genai
from bson import ObjectId
import random

load_dotenv()

# Get variables
mongo_url = os.getenv('MONGO_URI')
google_api_key = os.getenv('GOOGLE_API_KEY')
sheet_url = os.getenv('G_SHEET_URI')
db_name = os.getenv('DB_NAME')

client = MongoClient(mongo_url)
db = client[db_name]
menu_collection = db["menu"]
# Authenticate with your Gemini API key
client = genai.Client(api_key=google_api_key)  # Replace with your API key!
model_name = "gemini-2.5-flash"

def generate_gemini_review(client, model_name, name, description):
    prompt = (
        f"Write a realistic, 1-2 sentence customer review for the restaurant menu item \"{name}\" "
        f"described as \"{description}\". The review should sound natural and mention the item's qualities."
    )
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        print("Gemini response:", response.text)
        # The returned object may differ, but use .text if available, otherwise try extracting result directly
        review_text = response.text if hasattr(response, 'text') else str(response)
        return review_text
    except Exception as e:
        print(f"Gemini error for '{name}':", e)
        return "Tasty and well made!"  # fallback/default

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
gs_client = gspread.authorize(creds)
# Open your Google Sheet by URL or title
spreadsheet = gs_client.open_by_url(sheet_url)

fake = Faker()

# Read menu items (get full objects for reference)
menu_items = list(menu_collection.find())

# 1. Customers sheet
customers_data = [['_id','name','email','phone','joined','loyalty_points']]
customers = []
for _ in range(30):
    cid = str(ObjectId())
    name = fake.name()
    email = fake.email()
    phone = fake.msisdn()[:10]
    joined = fake.date_between('-2y','today').isoformat()
    loyalty_points = random.randint(0, 100)
    customers.append({'_id': cid, 'name': name, 'email': email, 'phone': phone, 'joined': joined, 'loyalty_points': loyalty_points})
    customers_data.append([cid, name, email, phone, joined, loyalty_points])

# Write customers sheet
try:
    spreadsheet.add_worksheet(title="customers", rows="50", cols="6")
except Exception:  # If already exists
    pass
customers_ws = spreadsheet.worksheet("customers")
customers_ws.update('A1', customers_data)

# 2. Orders sheet
orders_data = [['_id', 'customer_id', 'menu_item_ids', 'total_price', 'order_time', 'status']]
orders = []
for _ in range(50):
    oid = str(ObjectId())
    cust = random.choice(customers)
    item_ids = [str(random.choice(menu_items)['_id']) for _ in range(random.randint(1, 4))]
    total_price = sum([random.choice(menu_items)['price'] for _ in item_ids])
    order_time = fake.date_time_this_year().isoformat()
    status = random.choice(['Delivered', 'Pending', 'Cancelled'])
    orders.append({'_id': oid, 'customer_id': cust['_id'], 'menu_item_ids': item_ids, 'total_price': total_price, 'order_time': order_time, 'status': status})
    orders_data.append([oid, cust['_id'], ','.join(item_ids), total_price, order_time, status])

try:
    spreadsheet.add_worksheet(title="orders", rows="60", cols="6")
except Exception:
    pass
orders_ws = spreadsheet.worksheet("orders")
orders_ws.update('A1', orders_data)

# 3. Ratings sheet
ratings_data = [['_id', 'menu_item_id', 'customer_id', 'rating', 'review', 'created_at']]
for _ in range(100):
    rid = str(ObjectId())
    menu_item = random.choice(menu_items)
    menu_item_id = str(menu_item['_id'])
    cust = random.choice(customers)
    rating = random.randint(1, 5)
    review = generate_gemini_review(client, model_name, menu_item["name"], menu_item.get("description", ""))
    created_at = fake.date_time_this_year().isoformat()
    ratings_data.append([rid, menu_item_id, cust['_id'], rating, review, created_at])
    time.sleep(10)  # Respect rate limits!

try:
    spreadsheet.add_worksheet(title="ratings", rows="120", cols="6")
except Exception:
    pass

ratings_ws = spreadsheet.worksheet("ratings")
ratings_ws.update('A1', ratings_data)

print("Dummy data sheets created!")
