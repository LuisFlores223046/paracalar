from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models.enum import Gender

"""
Schema para actualizar info de usuario
"""
class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Juan",
                "last_name": "Pérez",
                "gender": "M",
                "date_of_birth": "1990-01-15"
            }
        }

"""
Schema de respuesta para el perfil de usuario
"""
class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture: Optional[str] = None
    role: str
    account_status: bool
    auth_type: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "usuario@example.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "gender": "M",
                "date_of_birth": "1990-01-15",
                "profile_picture": "https://bucket.s3.region.amazonaws.com/profile_images/user_id/image.jpg",
                "role": "USER",
                "account_status": True,
                "auth_type": "EMAIL",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

"""
Schema para respuesta de cambio de foto
"""
class ProfileImageResponse(BaseModel):
    success: bool
    message: str
    profile_picture_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Imagen de perfil actualizada correctamente",
                "profile_picture_url": "https://bucket.s3.region.amazonaws.com/profile_images/user_id/image.jpg"
            }
        }

"""
Schema de respuesta para eliminacion de cuenta
"""
class DeleteAccountResponse(BaseModel):
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Cuenta eliminada correctamente"
            }
        }

"""
Schema de respuesta info basica de perfil
"""
class BasicProfileResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    profile_picture: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "usuario@example.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "profile_picture": "https://bucket.s3.region.amazonaws.com/profile_images/user_id/image.jpg"
            }
        }

"""
Schema genérico para respuestas con mensaje
"""
class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None