from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    status,
    Security
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.user_profile import schemas
from app.api.v1.user_profile.service import user_profile_service

router = APIRouter()

security = HTTPBearer()

"""Extrae el token del header Authorization"""
def get_token_from_header(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

"""
Verifica el token JWT y devuelve el payload del usuario.
Reutiliza la función de auth para mantener consistencia.
"""
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
Obtiene el perfil completo del usuario autenticado
"""
@router.get("/me", response_model=schemas.UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = user_profile_service.get_user_profile(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["user"]

"""
Obtiene informacion basica del perfil
"""
@router.get("/me/basic", response_model=schemas.BasicProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_basic_profile(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = user_profile_service.get_basic_profile(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["user"]

"""
Actualiza la informacion del perfil del usuario
"""
@router.put("/me", response_model=schemas.UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    profile_data: schemas.UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = user_profile_service.update_user_profile(
        db=db,
        cognito_sub=cognito_sub,
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["user"]

"""
Actualiza la imagen de perfil del usuario
"""
@router.put("/me/image", response_model=schemas.ProfileImageResponse, status_code=status.HTTP_200_OK)
async def update_profile_image(
    profile_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    # Validar que es una imagen
    if not profile_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen"
        )
    
    # Leer el contenido de la imagen
    image_content = await profile_image.read()
    
    result = user_profile_service.update_profile_image(
        db=db,
        cognito_sub=cognito_sub,
        image_content=image_content
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

"""
Elimina la cuenta del usuario (soft delete)
"""
@router.delete("/me", response_model=schemas.DeleteAccountResponse, status_code=status.HTTP_200_OK)
async def delete_my_account(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    
    result = user_profile_service.soft_delete_account(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result