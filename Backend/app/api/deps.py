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
    
    TODO: Implementar la validación del token JWT aquí.
    Por ahora es un placeholder que necesita ser completado
    con la lógica de validación de JWT/Cognito.
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe.
    
    Returns:
        User: El usuario autenticado.
    """
    token = credentials.credentials
    
    # TODO: Validar el token JWT/Cognito aquí
    # Ejemplo de lo que deberías hacer:
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     user_id: int = payload.get("sub")
    #     if user_id is None:
    #         raise credentials_exception
    # except JWTError:
    #     raise credentials_exception
    
    # Por ahora, placeholder - debes implementar la validación real
    # Esto es solo para que compile
    user_id = 1  # Temporal - obtener del token
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
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
