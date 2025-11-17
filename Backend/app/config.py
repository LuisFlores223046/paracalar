# Autor: Gabriel Vilchis
# Fecha: 09/11/2025
# Descripción:
# Este archivo define la clase Settings utilizando Pydantic Settings para la carga
# y gestión centralizada de variables de entorno provenientes del archivo .env.
# Su propósito es centralizar parámetros sensibles y configuraciones relacionadas
# con la base de datos, AWS, Cognito, S3, JWT, Stripe y PayPal.

import os
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
    JWT_SECRET_KEY: str  # Obligatorio para compatibilidad
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
    #BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    BACKEND_CORS_ORIGINS: List[str] = []
    APP_URL: str # "https://frontend.d34s9corpodswj.amplifyapp.com"
     # En lugar de se el local host, debe de ser la url del frontend para que funcione las redirecciones
    # de success y cancel
    #APP_URL: str = "http://localhost:8000"
    #APP_URL: str = "https://frontend.d34s9corpodswj.amplifyapp.com/"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def print_debug_info(self):
        """
        Método para imprimir información de debug SOLO en desarrollo.
        NO llamar en producción por seguridad.
        
        Uso: Establece DEBUG=True en .env para activar
        """
        if self.DEBUG:
            print("CONFIGURACIÓN DE DEBUG - BeFit API")
            print(f"App Name: {self.APP_NAME}")
            print(f"Version: {self.APP_VERSION}")
            print(f"App URL: {self.APP_URL}")
            print(f"CORS Origins: {self.BACKEND_CORS_ORIGINS}")
            print("\n--- AWS Configuración ---")
            print(f"AWS Region: {self.AWS_REGION}")
            print(f"S3 Bucket: {self.S3_BUCKET_NAME}")
            print(f"AWS Access Key configurada: {'✓' if self.AWS_ACCESS_KEY_ID else '✗'}")
            print(f"AWS Secret Key configurada: {'✓' if self.AWS_SECRET_ACCESS_KEY else '✗'}")
            print("\n--- Cognito Configuración ---")
            print(f"Cognito Region: {self.COGNITO_REGION}")
            print(f"User Pool ID: {self.COGNITO_USER_POOL_ID}")
            print(f"Client ID: {self.COGNITO_CLIENT_ID}")
            print("\n--- JWT Configuración ---")
            print(f"JWT Algorithm: {self.JWT_ALGORITHM}")
            print(f"Token Expire (min): {self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES}")
            print(f"JWT Secret Key configurada: {'✓' if self.JWT_SECRET_KEY else '✗'}")
            print("\n--- Pagos Configuración ---")
            print(f"Stripe API Key configurada: {'✓' if self.STRIPE_API_KEY else '✗'}")
            print(f"Stripe Secret Key configurada: {'✓' if self.STRIPE_SECRET_KEY else '✗'}")
            print(f"Stripe Webhook Secret configurada: {'✓' if self.STRIPE_WEBHOOK_SECRET else '✗'}")
            print(f"PayPal Client ID configurada: {'✓' if self.PAYPAL_CLIENT_ID else '✗'}")
            print(f"PayPal Client Secret configurada: {'✓' if self.PAYPAL_CLIENT_SECRET else '✗'}")
            print(f"PayPal API URL: {self.PAYPAL_API_BASE_URL}")
            print("\n--- Base de Datos ---")
            # Mostrar solo el inicio de la URL por seguridad
            db_preview = self.DATABASE_URL[:30] + "..." if len(self.DATABASE_URL) > 30 else self.DATABASE_URL
            print(f"Database URL: {db_preview}")
            print("RECUERDA: Desactiva DEBUG en producción")


# Instancia global de configuración
settings = Settings()

# Debug solo si está en modo desarrollo
settings.print_debug_info()