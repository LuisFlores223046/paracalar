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
    Extrae el token del header Authorization.
    
    Raises:
        HTTPException: Si no se proporcionan credenciales
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
    Dependencia para obtener el usuario actual autenticado.
    
    Verifica el token JWT con Cognito y obtiene el usuario de la base de datos.
    
    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
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
            status_code=status.HTTP_404_NOT_FOUND,
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
    Dependencia que requiere que el usuario sea administrador.
    
    Args:
        current_user: Usuario actual obtenido de get_current_user
    
    Raises:
        HTTPException: Si el usuario no es administrador
    
    Returns:
        Usuario administrador
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
    Dependencia para obtener el usuario actual si está autenticado,
    o None si no lo está.
    
    Útil para endpoints que funcionan tanto con usuarios autenticados
    como no autenticados (pero con diferente comportamiento).
    
    Args:
        credentials: Credenciales opcionales del header
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado o None
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