# Autor: Luis Flores
# Fecha: 12/11/2025
# Descripción: Funciones de dependencia de FastAPI para la autenticación de usuarios y verificación de roles.

import os
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.models.enum import UserRole
from app.api.v1.auth.service import cognito_service

# Security scheme
security = HTTPBearer()


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Autor: Luis Flores
    Descripción: Extrae el token del header Authorization.
    Parámetros:
        credentials (HTTPAuthorizationCredentials): Credenciales obtenidas del header.
    Retorna:
        str: El token extraído.
    Excepciones:
        HTTPException: Si no se proporcionan credenciales.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Autor: Luis Flores
    Descripción: Dependencia para obtener el usuario actual autenticado.
                 Verifica el token JWT con Cognito y obtiene el usuario de la base de datos.
    Parámetros:
        token (str): Token JWT del header Authorization (inyectado por Depends).
        db (Session): Sesión de base de datos (inyectado por Depends).
    Retorna:
        User: El objeto de usuario autenticado y activo.
    Excepciones:
        HTTPException: Si el token es inválido, el usuario no existe o la cuenta está desactivada.
    """

    # Verificar token con Cognito
    payload = cognito_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener cognito_sub del payload
    cognito_sub = payload.get('sub')
    
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta identificador de usuario",
        )
    
    # Buscar usuario en la base de datos por cognito_sub
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_44_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos"
        )
    
    # Verificar que la cuenta esté activa
    if not user.account_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario está desactivada"
        )
    
    return user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Autor: Luis Flores
    Descripción: Dependencia que requiere que el usuario actual sea administrador.
                 En DEV_MODE, permite el acceso a cualquier usuario.
    Parámetros:
        current_user (User): Usuario actual obtenido de get_current_user.
    Retorna:
        User: El objeto de usuario (si es admin o si está en DEV_MODE).
    Excepciones:
        HTTPException: Si el usuario no es administrador (y no está en DEV_MODE).
    """

    if os.getenv("DEV_MODE") == "true":
        print("************************************************************")
        print("ADVERTENCIA: DEV_MODE activo. Saltando verificación de admin.")
        print(f"Usuario '{current_user.email}' tratado como ADMIN.")
        print("************************************************************")
        return current_user # Devuelve el usuario actual, sea admin o no

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción"
        )
    
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Autor: Luis Flores
    Descripción: Dependencia para obtener el usuario actual si está autenticado,
                 o None si no lo está. No lanza errores si falla la autenticación.
    Parámetros:
        credentials (Optional[HTTPAuthorizationCredentials]): Credenciales opcionales del header.
        db (Session): Sesión de base de datos (inyectado por Depends).
    Retorna:
        Optional[User]: El objeto de usuario autenticado y activo, o None si no hay
                        credenciales válidas.
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = cognito_service.verify_token(token)
        
        if not payload:
            return None
        
        cognito_sub = payload.get('sub')
        if not cognito_sub:
            return None
        
        user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
        
        if not user or not user.account_status:
            return None
        
        return user
    except Exception:
        return None