# Autor: Lizbeth Barajas
# Fecha: 11-11-25
# Desripcion: Maneja las rutas API del módulo de método de pago propocionando endpoints
#             para consultar, registrar, eliminar y configurar tarjetas mediante la integración con Stripe.

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.payment_method import schemas
from app.api.v1.payment_method.service import payment_method_service

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

"""Verifica el token JWT y devuelve el payload del usuario"""
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

@router.get("", response_model=schemas.PaymentMethodListResponse, status_code=status.HTTP_200_OK)
async def get_my_payment_methods(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Obtiene todos los métodos de pago del usuario autenticado, incluyendo 
                 únicamente tarjetas registradas.

    Parámetros:
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado obtenida desde el token JWT.

    Retorna:
        dict: Resultado que incluye la lista de métodos de pago y su conteo total.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.get_user_payment_methods(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.get("/{payment_id}", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_200_OK)
async def get_payment_method(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Obtiene un método de pago específico perteneciente al usuario, buscando por
                 su identificador único.

    Parámetros:
        payment_id (int): Identificador del método de pago a consultar.
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Objeto del método de pago encontrado.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.get_payment_method_by_id(
        db=db,
        cognito_sub=cognito_sub,
        payment_id=payment_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["payment_method"]

@router.post("/setup-intent", response_model=schemas.SetupIntentResponse, status_code=status.HTTP_200_OK)
async def create_setup_intent(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Crea un Setup Intent de Stripe para que el frontend pueda capturar los datos
                 de una tarjeta y vincularla con el usuario.

    Parámetros:
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Información necesaria para el frontend, incluyendo client_secret y setup_intent_id.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.create_setup_intent(
        db=db,
        cognito_sub=cognito_sub
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.post("/save", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def save_payment_method(
    save_data: schemas.SavePaymentMethodRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Guarda un método de pago en la base de datos tras completar un Setup Intent
                 exitoso en Stripe.

    Parámetros:
        save_data (SavePaymentMethodRequest): Datos enviados desde el frontend, incluyendo
            el ID del método de pago y si será predeterminado.
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Objeto del método de pago almacenado.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.save_payment_method_from_setup(
        db=db,
        cognito_sub=cognito_sub,
        payment_method_id=save_data.payment_method_id,
        is_default=save_data.is_default
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["payment_method"]

@router.delete("/{payment_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
async def delete_payment_method(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Elimina un método de pago del usuario, removiéndolo tanto de la base de datos
                 como de Stripe si aplica.

    Parámetros:
        payment_id (int): Identificador del método de pago a eliminar.
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Mensaje confirmando la eliminación exitosa.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.delete_payment_method(
        db=db,
        cognito_sub=cognito_sub,
        payment_id=payment_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.patch("/{payment_id}/set-default", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_200_OK)
async def set_default_payment_method(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción: Establece un método de pago del usuario como la tarjeta predeterminada,
                 removiendo la marca de predeterminado de cualquier otro método existente.

    Parámetros:
        payment_id (int): Identificador del método de pago a establecer como predeterminado.
        db (Session): Sesión activa de la base de datos.
        current_user (dict): Información del usuario autenticado.

    Retorna:
        dict: Objeto del método de pago actualizado como predeterminado.
    """
    cognito_sub = current_user.get("sub")
    
    result = payment_method_service.set_default_payment_method(
        db=db,
        cognito_sub=cognito_sub,
        payment_id=payment_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["payment_method"]
