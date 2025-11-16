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
from app.api.v1.address import schemas
from app.api.v1.address.service import address_service

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

"""
Obtiene todas las direcciones del usuario
"""
@router.get("", response_model=schemas.AddressListResponse, status_code=status.HTTP_200_OK)
async def get_all_addresses(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.get_user_addresses(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

"""
Obtiene una direccion específica por id
"""
@router.get("/{address_id}", response_model=schemas.AddressResponse, status_code=status.HTTP_200_OK)
async def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.get_address_by_id(db=db, cognito_sub=cognito_sub, address_id=address_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["address"]

"""
Crea una nueva direccion
"""
@router.post("", response_model=schemas.AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: schemas.CreateAddressRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.create_address(
        db=db,
        cognito_sub=cognito_sub,
        address_name=address_data.address_name,
        address_line1=address_data.address_line1,
        address_line2=address_data.address_line2,
        country=address_data.country,
        state=address_data.state,
        city=address_data.city,
        zip_code=address_data.zip_code,
        recipient_name=address_data.recipient_name,
        phone_number=address_data.phone_number,
        is_default=address_data.is_default
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["address"]

"""
Actualiza una direccion existente
"""
@router.put("/{address_id}", response_model=schemas.AddressResponse, status_code=status.HTTP_200_OK)
async def update_address(
    address_id: int,
    address_data: schemas.UpdateAddressRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.update_address(
        db=db,
        cognito_sub=cognito_sub,
        address_id=address_id,
        address_name=address_data.address_name,
        address_line1=address_data.address_line1,
        address_line2=address_data.address_line2,
        country=address_data.country,
        state=address_data.state,
        city=address_data.city,
        zip_code=address_data.zip_code,
        recipient_name=address_data.recipient_name,
        phone_number=address_data.phone_number,
        is_default=address_data.is_default
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["address"]

"""
Elimina una direccion
"""
@router.delete("/{address_id}", response_model=schemas.MessageResponse, status_code=status.HTTP_200_OK)
async def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.delete_address(db=db, cognito_sub=cognito_sub, address_id=address_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

"""
Establece una direccion como predeterminada
"""
@router.patch("/{address_id}/set-default", response_model=schemas.AddressResponse, status_code=status.HTTP_200_OK)
async def set_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = address_service.set_default_address(db=db, cognito_sub=cognito_sub, address_id=address_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["address"]
