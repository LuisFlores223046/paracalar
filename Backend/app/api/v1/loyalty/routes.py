# Autor: Lizbeth Barajas y Gabriel Vilchis
# Fecha: 12-11-25
# Descripción: Rutas para el módulo de lealtad, incluyendo consulta de puntos,
#              niveles, historial y generación de cupones mensuales.

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    Query
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.loyalty import schemas
from app.api.v1.loyalty.service import loyalty_service

router = APIRouter()

security = HTTPBearer()

"""Extrae el token del header Authorization"""
def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def get_current_user(token: str = Depends(get_token_from_header)) -> Dict:
    from app.api.v1.auth.service import cognito_service
    
    payload = cognito_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.get("/me", response_model=schemas.UserLoyaltyResponse, status_code=status.HTTP_200_OK)
async def get_my_loyalty_status(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene el estado de lealtad del usuario actual, incluyendo puntos,
        nivel de lealtad y progreso al siguiente tier.

    Parámetros:
        db (Session): Sesión activa de base de datos.
        current_user (dict): Payload del usuario autenticado.

    Retorna:
        dict: Datos del estado de lealtad del usuario.
    """
    cognito_sub = current_user.get("sub")
    
    result = loyalty_service.get_user_loyalty_status(
        db=db,
        cognito_sub=cognito_sub
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["loyalty"]

@router.get("/tiers", response_model=schemas.LoyaltyTiersListResponse, status_code=status.HTTP_200_OK)
async def get_all_loyalty_tiers(
    db: Session = Depends(get_db)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene la información de todos los niveles de lealtad,
        incluyendo requisitos y beneficios.

    Parámetros:
        db (Session): Sesión activa de base de datos.

    Retorna:
        dict: Lista de niveles de lealtad disponibles.
    """
    result = loyalty_service.get_all_tiers(db=db)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.get("/tiers/{tier_id}", response_model=schemas.LoyaltyTierResponse, status_code=status.HTTP_200_OK)
async def get_tier_details(
    tier_id: int,
    db: Session = Depends(get_db)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene la información detallada de un nivel de lealtad específico.

    Parámetros:
        tier_id (int): Identificador del tier.
        db (Session): Sesión activa de base de datos.

    Retorna:
        dict: Datos completos del nivel solicitado.
    """
    result = loyalty_service.get_tier_by_id(db=db, tier_id=tier_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["tier"]

@router.get("/me/history", response_model=List[schemas.PointHistoryResponse], status_code=status.HTTP_200_OK)
async def get_my_point_history(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene el historial de puntos del usuario autenticado, limitado por un número máximo.

    Parámetros:
        limit (int): Cantidad máxima de registros a obtener.
        db (Session): Sesión activa de base de datos.
        current_user (dict): Payload del usuario autenticado.

    Retorna:
        list: Historial de puntos del usuario.
    """
    cognito_sub = current_user.get("sub")
    
    result = loyalty_service.get_point_history(
        db=db,
        cognito_sub=cognito_sub,
        limit=limit
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["history"]

@router.post("/me/expire-points", response_model=schemas.ExpirePointsResponse, status_code=status.HTTP_200_OK)
async def expire_my_points(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Procesa la expiración de puntos del usuario actual. Puede ser usado
        manualmente o por procesos automáticos del sistema.

    Parámetros:
        db (Session): Sesión activa de base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Resultado de la expiración de puntos.
    """
    cognito_sub = current_user.get("sub")
    
    result = loyalty_service.expire_points_for_user(
        db=db,
        cognito_sub=cognito_sub
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result


@router.post("/{user_id}/coupons/generate", 
             status_code=status.HTTP_201_CREATED,
             response_model=list[str] 
)
def create_monthly_coupons(user_id: int, db: Session = Depends(get_db)):
    """
    Autor: Gabriel Vilchis

    Descripción:
        Genera los cupones mensuales correspondientes al tier del usuario especificado.

    Parámetros:
        user_id (int): ID del usuario para el cual se generarán los cupones.
        db (Session): Sesión activa de base de datos.

    Retorna:
        dict: Mensaje de éxito y lista de códigos generados.
    """
    try:
        generated_codes = loyalty_service.generate_monthly_coupons_for_user(db, user_id)
        return {"message": "Coupons generated successfully", "codes": generated_codes}
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during coupon generation.")
