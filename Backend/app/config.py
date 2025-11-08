from pydantic_settings import BaseSettings
from typing import Optional, List
import json


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno
    """
    
    # ============ BASE DE DATOS ============
    DATABASE_URL: str = "sqlite:///./befit.db"
    
    # ============ AWS COGNITO ============
    COGNITO_REGION: str
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    
    # ============ AWS S3 ============
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET_NAME: str
    
    # ============ JWT ============
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECRET_KEY: Optional[str] = None  # Para JWT manual si lo usas
    
    # ============ PAYPAL ============
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_API_BASE_URL: Optional[str] = None
    
    # ============ STRIPE ============
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    
    # ============ APLICACIÓN ============
    APP_NAME: str = "BeFit API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============ CORS ============
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:8000"]'
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Convierte el string JSON de CORS_ORIGINS a una lista"""
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except:
            return ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Permitir campos extra si es necesario
        extra = "ignore"  # Esto ignora variables extras en el .env


# Instancia global de configuración
settings = Settings()