from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============ CART ITEM SCHEMAS ============
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class CartItemAdd(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemProductInfo(BaseModel):
    """Información del producto en el carrito"""
    product_id: int
    name: str
    price: float
    stock: int
    image_path: Optional[str] = None  
    brand: Optional[str] = None

    class Config:
        from_attributes = True


class CartItemResponse(BaseModel):
    cart_item_id: int  
    cart_id: int
    product_id: int
    quantity: int
    added_at: datetime
    updated_at: datetime
    product: CartItemProductInfo
    subtotal: float  

    class Config:
        from_attributes = True


# ============ SHOPPING CART SCHEMAS ============
class ShoppingCartResponse(BaseModel):
    cart_id: int
    user_id: int
    items: List[CartItemResponse] = []
    total_items: int  
    total_price: float 
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """Resumen rápido del carrito"""
    total_items: int
    total_price: float
