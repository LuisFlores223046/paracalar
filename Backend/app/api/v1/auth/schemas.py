from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date
import re


# ============ REGISTRO DE USUARIO ============

class SignUpRequest(BaseModel):
    """Schema para registro de usuario"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    gender: Optional[str] = Field(None, pattern="^(M|F|prefer_not_say)$")
    birth_date: Optional[date] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Valida que la contraseña cumpla con requisitos de Cognito"""
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        
        if not any(char.islower() for char in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
            
        if not any(char.isupper() for char in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v) and not re.search(r'[^a-zA-Z0-9\s]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
           
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com",
                "password": "MiPassword123!",
                "first_name": "Juan",
                "last_name": "Pérez",
                "gender": "M",
                "birth_date": "1990-01-15"
            }
        }
    }


class SignUpResponse(BaseModel):
    """Respuesta de registro"""
    success: bool
    message: str
    user_sub: Optional[str] = None
    user_id: Optional[str] = None
    profile_image_url: Optional[str] = None


# ============ INICIO DE SESIÓN ============

class SignInRequest(BaseModel):
    """Schema para inicio de sesión"""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com",
                "password": "MiPassword123!"
            }
        }
    }


class TokenResponse(BaseModel):
    """Respuesta con tokens JWT"""
    success: bool
    access_token: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    error: Optional[str] = None


# ============ CONFIRMACIÓN ============

class ConfirmSignUpRequest(BaseModel):
    """Confirmación de registro con código"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com",
                "code": "123456"
            }
        }
    }


class ResendCodeRequest(BaseModel):
    """Reenvío de código de verificación"""
    email: EmailStr
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com"
            }
        }
    }


# ============ REFRESH TOKEN ============

class RefreshTokenRequest(BaseModel):
    """Renovación de token"""
    refresh_token: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ..."
            }
        }
    }


# ============ RECUPERACIÓN DE CONTRASEÑA ============

class ForgotPasswordRequest(BaseModel):
    """Solicitud de recuperación de contraseña"""
    email: EmailStr
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com"
            }
        }
    }


class ConfirmForgotPasswordRequest(BaseModel):
    """Confirmación de nueva contraseña"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Valida que la contraseña cumpla con requisitos"""
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(char.islower() for char in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com",
                "code": "123456",
                "new_password": "NuevaPassword123!"
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Cambio de contraseña estando autenticado"""
    old_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Valida que la contraseña cumpla con requisitos"""
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isupper() for char in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(char.islower() for char in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "old_password": "MiPassword123!",
                "new_password": "NuevaPassword456!"
            }
        }
    }


# ============ RESPUESTA GENÉRICA ============

class MessageResponse(BaseModel):
    """Respuesta con mensaje"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None