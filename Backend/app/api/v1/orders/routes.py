# Autor: Lizbeth Barajas
# Fecha: 14-11-25
# Descripción: Routes para modulo de ordenes

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    Query
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.orders import schemas
from app.api.v1.orders.service import order_service

router = APIRouter()

security = HTTPBearer()

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


@router.get("", response_model=schemas.OrderListResponse, status_code=status.HTTP_200_OK)
async def get_my_orders(
    limit: int = Query(50, ge=1, le=100, description="Número de pedidos a retornar"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene todos los pedidos pertenecientes al usuario autenticado usando
        paginación y devuelve los más recientes primero.

    Parámetros:
        limit (int): Cantidad máxima de pedidos a mostrar.
        offset (int): Cantidad de pedidos a omitir (paginación).
        db (Session): Conexión activa a la base de datos.
        current_user (Dict): Información decodificada del usuario autenticado.

    Retorna:
        Dict: Lista de pedidos y total encontrado.
    """
    cognito_sub = current_user.get("sub")
    
    result = order_service.get_user_orders(
        db=db,
        cognito_sub=cognito_sub,
        limit=limit,
        offset=offset
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result


@router.get("/{order_id}", response_model=schemas.OrderDetailResponse, status_code=status.HTTP_200_OK)
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene un pedido específico perteneciente al usuario, incluyendo
        detalles de productos, dirección y totales.

    Parámetros:
        order_id (int): ID del pedido a consultar.
        db (Session): Conexión activa a la base de datos.
        current_user (Dict): Payload validado del usuario autenticado.

    Retorna:
        Dict: Pedido detallado si existe, de lo contrario error 404.
    """
    cognito_sub = current_user.get("sub")
    
    result = order_service.get_order_by_id(
        db=db,
        cognito_sub=cognito_sub,
        order_id=order_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["order"]


@router.get("/subscription/all", response_model=schemas.OrderListResponse, status_code=status.HTTP_200_OK)
async def get_subscription_orders(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene únicamente los pedidos marcados como suscripciones que 
        pertenecen al usuario autenticado.

    Parámetros:
        db (Session): Conexión a la base de datos.
        current_user (Dict): Payload del usuario autenticado.

    Retorna:
        Dict: Lista de pedidos de suscripción.
    """
    cognito_sub = current_user.get("sub")
    
    result = order_service.get_subscription_orders(
        db=db,
        cognito_sub=cognito_sub
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result


@router.post("/{order_id}/cancel", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: int,
    cancel_data: schemas.CancelOrderRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Cancela un pedido del usuario siempre que no haya sido enviado. También 
        restaura inventario y actualiza el estado de la orden.

    Parámetros:
        order_id (int): ID del pedido a cancelar.
        cancel_data (CancelOrderRequest): Razón de cancelación.
        db (Session): Conexión a la base de datos.
        current_user (Dict): Información del usuario autenticado.

    Retorna:
        Dict: Resultado de la cancelación.
    """
    cognito_sub = current_user.get("sub")
    
    result = order_service.cancel_order(
        db=db,
        cognito_sub=cognito_sub,
        order_id=order_id,
        reason=cancel_data.reason
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result


@router.get("/{order_id}/status", status_code=status.HTTP_200_OK)
async def get_order_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene el estado actual de un pedido perteneciente al usuario. Incluye 
        número de rastreo si está disponible.

    Parámetros:
        order_id (int): ID del pedido a consultar.
        db (Session): Conexión activa a la base de datos.
        current_user (Dict): Payload del usuario autenticado.

    Retorna:
        Dict: Estado del pedido y datos básicos de seguimiento.
    """
    cognito_sub = current_user.get("sub")
    
    result = order_service.get_order_status(
        db=db,
        cognito_sub=cognito_sub,
        order_id=order_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result
