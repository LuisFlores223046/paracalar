from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.payment_method import schemas
from app.api.v1.payment_method.service import payment_method_service

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])
security = HTTPBearer()

def get_token_from_header(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
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

@router.get("", response_model=schemas.PaymentMethodListResponse, status_code=status.HTTP_200_OK)
async def get_my_payment_methods(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
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

@router.post("", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_data: schemas.CreatePaymentMethodRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    result = payment_method_service.create_payment_method(
        db=db,
        cognito_sub=cognito_sub,
        payment_type=payment_data.payment_type,
        provider_ref=payment_data.provider_ref,
        last_four=payment_data.last_four,
        expiration_date=payment_data.expiration_date,
        is_default=payment_data.is_default
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