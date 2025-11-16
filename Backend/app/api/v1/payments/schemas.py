# Autor: Lizbeth Barajas
# Fecha: 14-11-25
# Descripción: Esquemas de Pydantic para el procesamiento del pago (checkout) en la API.

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

"""
Schema para resumen de checkout
"""
class CheckoutSummaryRequest(BaseModel):
    address_id: int = Field(..., description="ID de dirección")
    coupon_code: Optional[str] = Field(None, description="Opcional - Cupón")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address_id": 1,
                "coupon_code": None
            }
        }

"""
Schema para checkout en stripe
"""
class StripeCheckoutRequest(BaseModel):
    address_id: int = Field(..., description="ID de dirección")
    payment_method_id: Optional[int] = Field(None, description="ID de método de pago guardado")
    coupon_code: Optional[str] = Field(None, description="Opcional - Cupón")
    subscription_id: Optional[int] = Field(None, description="Opcional - Subscripción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address_id": 1,
                "payment_method_id": 1,
                "coupon_code": None,
                "subscription_id": None
            }
        }

"""
Schema para el checkout de PayPal
"""
class PayPalCheckoutRequest(BaseModel):
    address_id: int = Field(..., description="ID de dirección")
    coupon_code: Optional[str] = Field(None, description="Opcional - Cupón")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address_id": 1,
                "coupon_code": None
            }
        }

"""
Schema de captura de Paypal - despues de approval
"""
class PayPalCaptureRequest(BaseModel):
    paypal_order_id: str = Field(..., description="ID orden paypal")
    address_id: int = Field(..., description="ID de dirección")
    coupon_code: Optional[str] = Field(None, description="Opcional - Cupón")
    
    class Config:
        json_schema_extra = {
            "example": {
                "paypal_order_id": "5O190127TN364715T",
                "address_id": 1,
                "coupon_code": None
            }
        }

"""
Schema de respuesta de pago
"""
class PaymentResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[int] = None
    paypal_order_id: Optional[str] = None
    paypal_approval_url: Optional[str] = None
    stripe_session_id: Optional[str] = None
    stripe_checkout_url: Optional[str] = None
    total_amount: Optional[Decimal] = None
    points_earned: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Sesión de pago creada",
                "stripe_session_id": "cs_test_123",
                "stripe_checkout_url": "https://checkout.stripe.com/...",
                "total_amount": 1650.00,
                "points_earned": 330
            }
        }

"""
Schema de resumen de checkout completo
"""
class CheckoutSummary(BaseModel):
    subtotal: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    items_count: int
    points_to_earn: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "subtotal": 1500.00,
                "shipping_cost": 150.00,
                "discount_amount": 0.00,
                "total_amount": 1650.00,
                "items_count": 3,
                "points_to_earn": 330
            }
        }

"""
Schema genérico para respuestas con mensaje
"""
class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

"""
Schema de webhook de stripe (uso interno)
"""
class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "evt_test_webhook",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_123",
                        "payment_intent": "pi_test_123"
                    }
                }
            }
        }