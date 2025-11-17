# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 17/11/2025
# Descripción: Schemas de validación y serialización para el módulo de suscripciones.
#              Define los modelos Pydantic para request/response de la API.

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal


# ============ SUBSCRIPTION CREATION ============

class CreateSubscriptionRequest(BaseModel):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Schema para crear una nueva suscripción.
                 Requiere que el usuario tenga un fitness profile y un método de pago guardado.
    Atributos:
        payment_method_id (int): ID del método de pago guardado a usar para los cobros recurrentes.
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
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Schema de respuesta completo para una suscripción.
                 Incluye toda la información relevante de la suscripción activa.
    Atributos:
        subscription_id (int): Identificador único de la suscripción.
        user_id (int): ID del usuario propietario.
        profile_id (int): ID del perfil fitness asociado.
        payment_method_id (int): ID del método de pago utilizado.
        subscription_status (str): Estado actual (active, paused, cancelled).
        start_date (date): Fecha de inicio de la suscripción.
        end_date (Optional[date]): Fecha de finalización, si aplica.
        next_delivery_date (date): Próxima fecha de entrega programada.
        auto_renew (bool): Indica si se renueva automáticamente.
        price (Decimal): Precio mensual de la suscripción.
        last_payment_date (Optional[date]): Fecha del último pago exitoso.
        failed_payment_attempts (int): Número de intentos de cobro fallidos.
        plan_name (Optional[str]): Nombre del plan fitness recomendado.
        payment_method_last_four (Optional[str]): Últimos 4 dígitos de la tarjeta.
    """
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
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Schema simplificado con resumen de la suscripción.
                 Útil para mostrar información básica en headers o dashboards.
    Atributos:
        is_active (bool): Indica si el usuario tiene una suscripción activa.
        subscription_status (Optional[str]): Estado de la suscripción.
        next_delivery_date (Optional[date]): Próxima fecha de entrega.
        price (Optional[Decimal]): Precio mensual.
    """
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
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Schema para actualizar método de pago de la suscripción.
    Atributos:
        payment_method_id (int): Nuevo ID del método de pago a asociar.
    """
    payment_method_id: int = Field(..., description="Nuevo ID del método de pago")
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method_id": 2
            }
        }


# ============ GENERIC RESPONSES ============

class MessageResponse(BaseModel):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Respuesta genérica con mensaje de éxito o error.
    Atributos:
        success (bool): Indica si la operación fue exitosa.
        message (Optional[str]): Mensaje descriptivo de éxito.
        error (Optional[str]): Mensaje de error si la operación falló.
    """
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
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Schema para el historial de órdenes de suscripción.
                 Representa una orden individual dentro del historial.
    Atributos:
        order_id (int): ID único de la orden.
        order_date (date): Fecha en que se realizó la orden.
        total_amount (Decimal): Monto total pagado en la orden.
        order_status (str): Estado de la orden (paid, shipped, delivered, etc).
        tracking_number (Optional[str]): Número de rastreo del envío.
    """
    order_id: int
    order_date: date
    total_amount: Decimal
    order_status: str
    tracking_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class SubscriptionHistoryResponse(BaseModel):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Respuesta con historial completo de órdenes de suscripción.
                 Incluye la información de la suscripción y todas sus órdenes generadas.
    Atributos:
        subscription (SubscriptionResponse): Información completa de la suscripción.
        orders (list[SubscriptionOrderHistory]): Lista de todas las órdenes generadas.
        total_orders (int): Cantidad total de órdenes realizadas.
        total_spent (Decimal): Monto total gastado en todas las órdenes.
    """
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