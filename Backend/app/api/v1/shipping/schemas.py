# Autor: Gabriel Vilchis
# Fecha: 12/11/2025
# Descripción: Este archivo define los esquemas (schemas) de Pydantic para la gestión
# de pedidos y órdenes en la API. Incluye modelos para la creación de órdenes, 
# la estructura de los items dentro de una orden y la respuesta completa de la API
# para el historial y el rastreo de pedidos.
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

class CreateOrderItem(BaseModel):
    # Solo un item del carrito esta dentro de una sola request para la creacion del pedido
    product_id: int
    quantity: int = Field(..., gt=0)

class CreateOrder(BaseModel):
    user_id: int
    address_id: int
    payment_id: int

# Esta es la respuesta que dara la API
class Order(BaseModel):
    order_id: int
    user_id: int
    address_id: int
    payment_id: int
    order_date: date
    order_status: str # Se convierte del enum
    tracking_number: Optional[str] = None
    subtotal: float
    discount_amount: float
    shipping_cost: float
    total_amount: float

    class Config:
        from_attributes = True

# Respuesta del endpoint de rastreo
class OrderTrackingResponse(BaseModel):
    order_id: int
    tracking_number: Optional[str]
    total_amount: float
    order_status: str
    product_names: List[str]