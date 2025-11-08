from fastapi import (
    APIRouter, 
    HTTPException, 
    Depends, 
    UploadFile, 
    File, 
    status, 
    Form, 
    Security
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.v1.auth.service import cognito_service
from app.api.v1.auth import schemas
from app.core.database import get_db
from app.models.enum import UserRole

router = APIRouter()
security = HTTPBearer()


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """Extrae el token del header Authorization"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(token: str = Depends(get_token_from_header)) -> Dict:
    """
    Verifica el token JWT y devuelve el payload del usuario.
    
    Args:
        token: Token JWT del header
        
    Returns:
        Payload del usuario decodificado
        
    Raises:
        HTTPException: Si el token es inválido
    """
    payload = cognito_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Agregar información de rol
    user_role = payload.get("custom:role")
    is_admin = user_role == UserRole.ADMIN.value
    payload["is_admin"] = is_admin
    
    return payload


# ============ ENDPOINTS DE REGISTRO ============

@router.post(
    "/signup", 
    response_model=schemas.SignUpResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)
async def register_user(
    db: Session = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    gender: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None), 
    profile_image: Optional[UploadFile] = None
):
    """
    Registra un nuevo usuario.
    
    Acepta datos de formulario (multipart/form-data) y una imagen opcional.
    Envía un código de verificación al email del usuario.
    """
    try:
        user_data = schemas.SignUpRequest(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            gender=gender,
            birth_date=birth_date,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=e.errors()
        )

    image_bytes = await profile_image.read() if profile_image else None

    result = cognito_service.sign_up(
        db=db, 
        user_data=user_data, 
        profile_image=image_bytes
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result.get("error")
        )
    
    return result


@router.post(
    "/confirm", 
    response_model=schemas.MessageResponse, 
    status_code=status.HTTP_200_OK,
    tags=["Authentication"]
)
async def confirm_signup(data: schemas.ConfirmSignUpRequest):
    """
    Confirma el registro de usuario con el código del email.
    
    El código es enviado automáticamente al email del usuario al registrarse.
    """
    result = cognito_service.confirm_sign_up(data.email, data.code)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result["error"]
        )
    
    return result


@router.post(
    "/resend-code", 
    response_model=schemas.MessageResponse,
    tags=["Authentication"]
)
async def resend_code(data: schemas.ResendCodeRequest):
    """
    Reenvía el código de confirmación a un email.
    
    Útil si el código original expiró o no llegó.
    """
    result = cognito_service.resend_confirmation_code(data.email)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result["error"]
        )
    
    return result


# ============ ENDPOINTS DE SESIÓN ============

@router.post(
    "/login", 
    response_model=schemas.TokenResponse,
    tags=["Authentication"]
)
async def login(credentials: schemas.SignInRequest):
    """
    Inicia sesión y obtiene tokens JWT.
    
    Retorna:
    - access_token: Para autenticar peticiones a la API
    - id_token: Contiene información del usuario
    - refresh_token: Para renovar el access_token
    """
    result = cognito_service.sign_in(credentials.email, credentials.password)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=result["error"]
        )
    
    return schemas.TokenResponse(
        success=True,
        access_token=result["access_token"],
        id_token=result["id_token"],
        refresh_token=result.get("refresh_token"),
        expires_in=result["expires_in"],
        token_type="Bearer"
    )


@router.post(
    "/refresh", 
    response_model=schemas.TokenResponse,
    tags=["Authentication"]
)
async def refresh_access_token(data: schemas.RefreshTokenRequest):
    """
    Refresca el Access Token usando un Refresh Token.
    
    Cuando el access_token expira, usa este endpoint con el refresh_token
    para obtener nuevos tokens sin necesidad de volver a hacer login.
    """
    result = cognito_service.refresh_token(data.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=result.get("error")
        )
    
    return schemas.TokenResponse(
        success=True,
        access_token=result["access_token"],
        id_token=result["id_token"],
        refresh_token=data.refresh_token,  # Reutiliza el mismo refresh token
        expires_in=result["expires_in"],
        token_type="Bearer"
    )


@router.post(
    "/logout", 
    response_model=schemas.MessageResponse,
    tags=["Authentication"]
)
async def logout(token: str = Depends(get_token_from_header)):
    """
    Cierra la sesión del usuario (invalida el access token globalmente).
    
    Requiere token de autenticación en el header:
    Authorization: Bearer <access_token>
    """
    result = cognito_service.sign_out(token)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result["error"]
        )
    
    return result


# ============ ENDPOINTS DE RECUPERACIÓN DE CONTRASEÑA ============

@router.post(
    "/forgot-password", 
    response_model=schemas.MessageResponse,
    tags=["Password Management"]
)
async def forgot_password(data: schemas.ForgotPasswordRequest):
    """
    Inicia el flujo de recuperación de contraseña.
    
    Envía un código de verificación al email del usuario.
    """
    result = cognito_service.forgot_password(data.email)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result["error"]
        )
    
    return result


@router.post(
    "/confirm-forgot-password", 
    response_model=schemas.MessageResponse,
    tags=["Password Management"]
)
async def confirm_forgot_password(data: schemas.ConfirmForgotPasswordRequest):
    """
    Establece una nueva contraseña usando el código de recuperación.
    
    El código es enviado al email mediante el endpoint /forgot-password.
    """
    result = cognito_service.confirm_forgot_password(
        data.email, data.code, data.new_password
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=result["error"]
        )
    
    return result


@router.post(
    "/change-password",
    response_model=schemas.MessageResponse,
    tags=["Password Management"]
)
async def change_password(
    data: schemas.ChangePasswordRequest,
    token: str = Depends(get_token_from_header)
):
    """
    Cambia la contraseña del usuario autenticado.
    
    Requiere autenticación y la contraseña actual.
    """
    result = cognito_service.change_password(
        token, data.old_password, data.new_password
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


# ============ ENDPOINT DE INFORMACIÓN DE USUARIO ============

@router.get(
    "/me",
    tags=["User Info"]
)
async def get_my_info(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado.
    
    Requiere token de autenticación en el header.
    Retorna el payload decodificado del token.
    """
    return {
        "success": True,
        "user": current_user
    }