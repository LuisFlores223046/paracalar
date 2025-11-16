# Autor: Lizbeth Barajas
# Fecha: 14-11-25
# Descripción: Esquemas de Pydantic para las ordenes en la API.

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

"""
Schema de respuesta para los items en la orden
"""
class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    
    class Config:
        from_attributes = True

"""
Schema de respuesta para la orden
"""
class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    address_id: int
    payment_id: int
    is_subscription: bool
    order_date: datetime
    order_status: str
    tracking_number: Optional[str] = None
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    points_earned: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "order_id": 123,
                "user_id": 1,
                "address_id": 1,
                "payment_id": 1,
                "is_subscription": False,
                "order_date": "2024-11-10T10:30:00Z",
                "order_status": "PAID",
                "tracking_number": None,
                "subtotal": 1500.00,
                "discount_amount": 0.00,
                "shipping_cost": 150.00,
                "total_amount": 1650.00,
                "points_earned": 330
            }
        }

"""
Schema de orden con items
"""
class OrderDetailResponse(BaseModel):
    order_id: int
    user_id: int
    is_subscription: bool
    order_date: datetime
    order_status: str
    tracking_number: Optional[str] = None
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    points_earned: int
    
    shipping_address: dict
    
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "order_id": 123,
                "user_id": 1,
                "is_subscription": False,
                "order_date": "2024-11-10T10:30:00Z",
                "order_status": "PAID",
                "tracking_number": None,
                "subtotal": 1500.00,
                "discount_amount": 0.00,
                "shipping_cost": 150.00,
                "total_amount": 1650.00,
                "points_earned": 330,
                "shipping_address": {
                    "recipient_name": "Juan Perez",
                    "address_line1": "Calle Ejemplo 1234",
                    "city": "Ciudad JuÃ¡rez",
                    "state": "Chihuahua",
                    "zip_code": "32000",
                    "phone_number": "6561234567"
                },
                "items": [
                    {
                        "order_item_id": 1,
                        "product_id": 1,
                        "product_name": "Proteina Whey",
                        "quantity": 2,
                        "unit_price": 750.00,
                        "subtotal": 1500.00
                    }
                ]
            }
        }

"""
Schema de lista de ordenes
"""
class OrderListResponse(BaseModel):
    success: bool
    orders: List[OrderResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "orders": [],
                "total": 0
            }
        }

"""
Schema para cancelar orden
"""
class CancelOrderRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Razon de la cancelaciÃ³n")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "ComprÃ© por error"
            }
        }

"""
Schema genérico para respuestas con mensaje
"""
class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None