from pydantic_settings import BaseSettings
from typing import Optional


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
    
    # ============ APLICACIÓN ============
    APP_NAME: str = "BeFit API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============ CORS ============
    CORS_ORIGINS: list = ["*"]  # En producción, especificar dominios
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()