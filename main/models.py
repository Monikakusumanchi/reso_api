from pydantic import BaseModel
from typing import List, Optional

class Customer(BaseModel):
    name: str
    email: str
    phone: str
    joined: Optional[str] = None
    loyalty_points: Optional[int] = 0

class MenuItem(BaseModel):
    name: str
    price: float
    description: str
    category: Optional[str] = ""
    isVegetarian: Optional[bool] = True
    ingredients: Optional[List[str]] = []
    availability: Optional[bool] = True
    image: Optional[str] = ""
    tags: Optional[List[str]] = []

class Order(BaseModel):
    customer_id: str
    menu_item_ids: List[str]
    total_price: float
    order_time: Optional[str] = None
    status: Optional[str] = "Pending"

class Rating(BaseModel):
    menu_item_id: str
    customer_id: str
    rating: int
    review: Optional[str] = ""
    created_at: Optional[str] = None
