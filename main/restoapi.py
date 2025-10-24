from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from typing import Dict
from fastapi import Body
from typing import Dict
from dotenv import load_dotenv
import os
from main.models import MenuItem, Customer, Order, Rating


load_dotenv()

# Get variables
mongo_url = os.getenv('MONGO_URI')
google_api_key = os.getenv('GOOGLE_API_KEY')
secret_key = os.getenv('G_SHEET_URI')
db_name = os.getenv('DB_NAME')

app = FastAPI()

client = MongoClient(mongo_url)
db = client[db_name]
menu_collection = db["menu"]
customers_collection = db["customers"]
orders_collection = db["orders"]
ratings_collection = db["ratings"]

# Helper to convert ObjectId to string
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@app.post("/menu/")
async def add_menu_item(item: MenuItem):
    item_dict = item.dict()
    result = menu_collection.insert_one(item_dict)
    return {"id": str(result.inserted_id)}

@app.put("/menu/{item_id}")
async def update_menu_item(item_id: str, item: MenuItem):
    result = menu_collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": item.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"msg": "Item updated"}

@app.delete("/menu/{item_id}")
async def delete_menu_item(item_id: str):
    result = menu_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"msg": "Item deleted"}

@app.delete("/{collection_name}/")
async def delete_items(collection_name: str, filter: Dict = Body(...)):
    """
    Delete multiple documents from a collection based on a filter.
    Example usage for customers:
      DELETE /customers/
      { "loyalty_points": { "$lte": 10 } }
    """
    # Helper: Map string to actual pymongo collection
    COLLECTION_MAP = {
        "menu": menu_collection,
        "customers": customers_collection,
        "orders": orders_collection,
        "ratings": ratings_collection
    }
    collection = COLLECTION_MAP.get(collection_name)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    result = collection.delete_many(filter)
    return {"deleted_count": result.deleted_count}


@app.post("/customers/")
async def add_customer(customer: Customer):
    doc = customer.dict()
    result = customers_collection.insert_one(doc)
    return {"id": str(result.inserted_id)}

@app.put("/customers/{cust_id}")
async def update_customer(cust_id: str, customer: Customer):
    result = customers_collection.update_one(
        {"_id": ObjectId(cust_id)},
        {"$set": customer.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"msg": "Customer updated"}

@app.delete("/customers/{cust_id}")
async def delete_customer(cust_id: str):
    result = customers_collection.delete_one({"_id": ObjectId(cust_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"msg": "Customer deleted"}


@app.post("/orders/")
async def add_order(order: Order):
    doc = order.dict()
    result = orders_collection.insert_one(doc)
    return {"id": str(result.inserted_id)}

@app.put("/orders/{order_id}")
async def update_order(order_id: str, order: Order):
    result = orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": order.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"msg": "Order updated"}

@app.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    result = orders_collection.delete_one({"_id": ObjectId(order_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"msg": "Order deleted"}

@app.post("/ratings/")
async def add_rating(rating: Rating):
    doc = rating.dict()
    result = ratings_collection.insert_one(doc)
    return {"id": str(result.inserted_id)}

@app.put("/ratings/{rating_id}")
async def update_rating(rating_id: str, rating: Rating):
    result = ratings_collection.update_one(
        {"_id": ObjectId(rating_id)},
        {"$set": rating.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"msg": "Rating updated"}

@app.delete("/ratings/{rating_id}")
async def delete_rating(rating_id: str):
    result = ratings_collection.delete_one({"_id": ObjectId(rating_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"msg": "Rating deleted"}

# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
