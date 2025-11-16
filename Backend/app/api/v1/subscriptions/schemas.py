# Autor: [Tu nombre]
# Fecha: 17/11/2025
# Descripción: Schemas de validación y serialización para el módulo de suscripciones.

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal


# ============ SUBSCRIPTION CREATION ============

class CreateSubscriptionRequest(BaseModel):
    """
    Schema para crear una nueva suscripción.
    Requiere que el usuario tenga un fitness profile y un método de pago guardado.
    """
    payment_method_id: int = Field(..., description="ID del método de pago guardado a usar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method_id": 1
            }
        }


# ============ SUBSCRIPTION RESPONSE ============

class SubscriptionResponse(BaseModel):
    """Schema de respuesta completo para una suscripción"""
    subscription_id: int
    user_id: int
    profile_id: int
    payment_method_id: int
    subscription_status: str
    start_date: date
    end_date: Optional[date] = None
    next_delivery_date: date
    auto_renew: bool
    price: Decimal
    last_payment_date: Optional[date] = None
    failed_payment_attempts: int
    
    # Info adicional
    plan_name: Optional[str] = Field(None, description="Nombre del plan fitness")
    payment_method_last_four: Optional[str] = Field(None, description="Últimos 4 dígitos de la tarjeta")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "subscription_id": 1,
                "user_id": 1,
                "profile_id": 1,
                "payment_method_id": 1,
                "subscription_status": "active",
                "start_date": "2024-11-17",
                "end_date": None,
                "next_delivery_date": "2024-12-17",
                "auto_renew": True,
                "price": 499.00,
                "last_payment_date": "2024-11-17",
                "failed_payment_attempts": 0,
                "plan_name": "BeStrong",
                "payment_method_last_four": "4242"
            }
        }


# ============ SUBSCRIPTION SUMMARY ============

class SubscriptionSummary(BaseModel):
    """Schema simplificado con resumen de la suscripción"""
    is_active: bool
    subscription_status: Optional[str] = None
    next_delivery_date: Optional[date] = None
    price: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_active": True,
                "subscription_status": "active",
                "next_delivery_date": "2024-12-17",
                "price": 499.00
            }
        }


# ============ UPDATE SUBSCRIPTION ============

class UpdateSubscriptionRequest(BaseModel):
    """Schema para actualizar método de pago de la suscripción"""
    payment_method_id: int = Field(..., description="Nuevo ID del método de pago")
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method_id": 2
            }
        }


# ============ GENERIC RESPONSES ============

class MessageResponse(BaseModel):
    """Respuesta genérica con mensaje"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación exitosa"
            }
        }


# ============ SUBSCRIPTION HISTORY ============

class SubscriptionOrderHistory(BaseModel):
    """Schema para el historial de órdenes de suscripción"""
    order_id: int
    order_date: date
    total_amount: Decimal
    order_status: str
    tracking_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class SubscriptionHistoryResponse(BaseModel):
    """Respuesta con historial completo de órdenes de suscripción"""
    subscription: SubscriptionResponse
    orders: list[SubscriptionOrderHistory]
    total_orders: int
    total_spent: Decimal
    
    class Config:
        json_schema_extra = {
            "example": {
                "subscription": {
                    "subscription_id": 1,
                    "subscription_status": "active",
                    "next_delivery_date": "2024-12-17",
                    "price": 499.00
                },
                "orders": [],
                "total_orders": 3,
                "total_spent": 1497.00
            }
        }