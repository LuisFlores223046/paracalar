# Autor: Lizbeth Barajas
# Fecha: 11-11-25
# Descripción: Esquemas de Pydantic para los métodos de pago en la API.

from pydantic import BaseModel, Field
from typing import Optional

"""
Schema para crear un Setup Intent (para guardar nueva tarjeta)
"""
class SetupIntentResponse(BaseModel):
    success: bool
    client_secret: str = Field(..., description="Client secret para usar en Stripe.js")
    setup_intent_id: str = Field(..., description="ID del Setup Intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "client_secret": "seti_1Abc...XYZ_secret_123",
                "setup_intent_id": "seti_1Abc...XYZ"
            }
        }

"""
Schema para guardar un payment method después del Setup Intent
"""
class SavePaymentMethodRequest(BaseModel):
    payment_method_id: str = Field(..., description="ID del payment method de Stripe (pm_xxxxx)")
    is_default: bool = Field(False, description="Establecer como método de pago por defecto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method_id": "pm_1234567890abcdef",
                "is_default": True
            }
        }

"""
Schema de respuesta para el metodo de pago
"""
class PaymentMethodResponse(BaseModel):
    payment_id: int
    user_id: int
    payment_type: str
    last_four: str
    expiration_date: Optional[str] = None
    is_default: bool
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "payment_id": 1,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "payment_type": "credit_card",
                "last_four": "4532",
                "expiration_date": "12/29",
                "is_default": True
            }
        }

"""
Schema de listado de metodos de pago
"""
class PaymentMethodListResponse(BaseModel):
    success: bool
    payment_methods: list[PaymentMethodResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "payment_methods": [
                    {
                        "payment_id": 1,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "payment_type": "credit_card",
                        "last_four": "4532",
                        "expiration_date": "12/29",
                        "is_default": True
                    }
                ],
                "total": 1
            }
        }

"""
Schema genérico para respuestas con mensaje
"""
class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None