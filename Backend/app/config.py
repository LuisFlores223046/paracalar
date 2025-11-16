# Autor: Luis & Gabriel
# Fecha: 16/11/2025
# Descripción:
# Configuración centralizada usando Pydantic Settings para variables de entorno.
# Gestiona parámetros de AWS Cognito, S3, base de datos, Stripe, PayPal y CORS.

import os
import json
from typing import Optional, List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Cargar variables de entorno
load_dotenv()

class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno del archivo .env
    """
    
    # ============ APLICACIÓN ============
    APP_NAME: str = "BeFit API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============ BASE DE DATOS ============
    DATABASE_URL: str  # Obligatorio
    
    # ============ AWS ============
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str  # Obligatorio
    AWS_SECRET_ACCESS_KEY: str  # Obligatorio
    
    # ============ AWS COGNITO ============
    COGNITO_REGION: str  # Obligatorio
    COGNITO_USER_POOL_ID: str  # Obligatorio
    COGNITO_CLIENT_ID: str  # Obligatorio
    
    # ============ AWS S3 ============
    S3_BUCKET_NAME: str  # Obligatorio
    
    # ============ JWT ============
    # Si usan Cognito para auth, pueden dejar JWT_SECRET_KEY como opcional
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "RS256"  # RS256 para Cognito, HS256 para JWT manual
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============ STRIPE ============
    STRIPE_API_KEY: str  # Obligatorio
    STRIPE_SECRET_KEY: str  # Obligatorio
    STRIPE_WEBHOOK_SECRET: str  # Obligatorio para validar webhooks
    
    # ============ PAYPAL ============
    PAYPAL_CLIENT_ID: str  # Obligatorio
    PAYPAL_CLIENT_SECRET: str  # Obligatorio
    PAYPAL_API_BASE_URL: str  # Obligatorio
    
    # ============ CORS ============
    # Se guarda como string JSON en .env y se convierte a lista
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:8000"]'
    
    # ============ APPLICATION URL ============
    APP_URL: str = "http://localhost:3000" 

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Convierte el string JSON de CORS_ORIGINS a una lista de strings.
        Permite configurar CORS desde el .env de forma flexible.
        """
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            # Fallback en caso de error
            return ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignora variables extras en el .env
        
    def print_debug_info(self):
        """
        Método para imprimir información de debug SOLO en desarrollo.
        NO llamar en producción por seguridad.
        """
        if self.DEBUG:
            print("=" * 50)
            print("CONFIGURACIÓN DE DEBUG")
            print("=" * 50)
            print(f"App Name: {self.APP_NAME}")
            print(f"Version: {self.APP_VERSION}")
            print(f"Database URL: {self.DATABASE_URL}")
            print(f"AWS Region: {self.AWS_REGION}")
            print(f"Cognito Region: {self.COGNITO_REGION}")
            print(f"Cognito User Pool ID: {self.COGNITO_USER_POOL_ID}")
            print(f"Cognito Client ID: {self.COGNITO_CLIENT_ID}")
            print(f"S3 Bucket: {self.S3_BUCKET_NAME}")
            print(f"JWT Algorithm: {self.JWT_ALGORITHM}")
            print(f"CORS Origins: {self.CORS_ORIGINS}")
            # NO imprimir keys secretas por seguridad
            print(f"Stripe API Key configurada: {'✓' if self.STRIPE_API_KEY else '✗'}")
            print(f"PayPal Client ID configurada: {'✓' if self.PAYPAL_CLIENT_ID else '✗'}")
            print("=" * 50)


# Instancia global de configuración
settings = Settings()

# Debug solo si está en modo desarrollo
settings.print_debug_info()