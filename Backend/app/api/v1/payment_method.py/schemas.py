from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.models.enum import PaymentType
import re

class CreatePaymentMethodRequest(BaseModel):
    payment_type: PaymentType
    provider_ref: str = Field(..., description="Token o referencia del proveedor (Stripe/PayPal)")
    last_four: str = Field(..., min_length=4, max_length=4, description="Últimos 4 dígitos para identificación")
    expiration_date: Optional[str] = Field(None, description="Fecha de expiración (MM/YY)")
    is_default: bool = False
    
    @field_validator('last_four')
    def validate_last_four(cls, v):
        if not v.isdigit():
            raise ValueError('Los últimos 4 dígitos deben ser numéricos')
        return v
    
    @field_validator('expiration_date')
    def validate_expiration(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{2}/\d{2}$', v):
            raise ValueError('Formato de fecha de expiración inválido (debe ser MM/YY)')
        return v

class PaymentMethodResponse(BaseModel):
    payment_id: int
    user_id: int
    payment_type: str
    last_four: str
    expiration_date: Optional[str] = None
    is_default: bool
    
    class Config:
        from_attributes = True

class PaymentMethodListResponse(BaseModel):
    success: bool
    payment_methods: list[PaymentMethodResponse]
    total: int

class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None