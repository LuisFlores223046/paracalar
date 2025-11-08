from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.models.user import User, UserRole

# Security scheme
security = HTTPBearer()


def get_db():
    """
    Dependencia para obtener la sesión de base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia para obtener el usuario actual autenticado.
    """
    token = credentials.credentials
    
    # ⚠️ TEMPORAL: Crear usuario admin por defecto
    user = db.query(User).filter(User.email == "admin@befit.com").first()
    
    if not user:
        # Crear usuario admin temporal
        user = User(
            email="admin@befit.com",
            first_name="Admin",
            last_name="BeFit",
            role=UserRole.ADMIN,  # ← ROL ADMIN
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que requiere que el usuario sea administrador.
    
    Args:
        current_user: Usuario actual obtenido de get_current_user
    
    Raises:
        HTTPException: Si el usuario no es administrador.
    
    Returns:
        User: El usuario administrador.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para realizar esta acción"
        )
    
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependencia para obtener el usuario actual si está autenticado,
    o None si no lo está.
    
    Útil para endpoints que funcionan tanto con usuarios autenticados
    como no autenticados (pero con diferente comportamiento).
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
