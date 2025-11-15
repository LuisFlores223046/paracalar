from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class CreateAddressRequest(BaseModel):
    address_name: Optional[str] = Field(None, max_length=50)
    address_line1: str = Field(..., min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    country: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    zip_code: str = Field(..., min_length=4, max_length=10)
    recipient_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=15)
    is_default: bool = False
    
    @field_validator('phone_number')
    def validate_phone(cls, v):
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Número de teléfono inválido')
        return v
    
    @field_validator('zip_code')
    def validate_zip(cls, v):
        if not re.match(r'^[A-Za-z0-9\s-]{4,10}$', v):
            raise ValueError('Código postal inválido')
        return v

class UpdateAddressRequest(BaseModel):
    address_name: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=4, max_length=10)
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    is_default: Optional[bool] = None
    
    @field_validator('phone_number')
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Número de teléfono inválido')
        return v
    
    @field_validator('zip_code')
    def validate_zip(cls, v):
        if v is None:
            return v
        if not re.match(r'^[A-Za-z0-9\s-]{4,10}$', v):
            raise ValueError('Código postal inválido')
        return v

class AddressResponse(BaseModel):
    address_id: int
    user_id: int
    address_name: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    country: str
    state: str
    city: str
    zip_code: str
    recipient_name: str
    phone_number: str
    is_default: bool
    
    class Config:
        from_attributes = True

class AddressListResponse(BaseModel):
    success: bool
    addresses: list[AddressResponse]
    total: int

class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None