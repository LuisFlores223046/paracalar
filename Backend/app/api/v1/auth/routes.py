# Autor: Gabriel Vilchis
# Fecha: 09/11/2025
# Descripción:
# Este archivo define el router principal del módulo de autenticación (Auth) de la API,
# implementado con FastAPI. Su propósito es manejar el registro de usuarios,
# confirmación de email, inicio de sesión, cierre de sesión, recuperación y
# restablecimiento de contraseñas utilizando AWS Cognito como proveedor de identidad.
from fastapi import (
    APIRouter, 
    HTTPException, 
    Depends, 
    UploadFile, 
    status, 
    Form, 
    Security
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from app.api.v1.auth.service import cognito_service
from app.api.v1.auth import schemas
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.database import get_db


router = APIRouter(prefix="/auth", tags=["Authentication"])

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

@router.post("/signup", response_model=schemas.SignUpResponse, status_code=status.HTTP_201_CREATED)
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
    Autor: Gabriel Vilchis
    Registra un nuevo usuario en AWS Cognito y la base de datos local.

    Espera los datos del usuario como campos de formulario (multipart/form-data),
    permitiendo la subida opcional de una imagen de perfil.

    Parámetros de formulario:
    - **first_name (str)**: Nombre del usuario.
    - **last_name (str)**: Apellido del usuario.
    - **email (str)**: Email (Username) del usuario.
    - **password (str)**: Contraseña (debe cumplir los requisitos).
    - **gender (Optional[str])**: Género ('M', 'F', 'prefer_not_say').
    - **birth_date (Optional[str])**: Fecha de nacimiento (formato ISO 8601).
    - **profile_image (Optional[UploadFile])**: Archivo de imagen de perfil para subir.

    Retorna:
    - `schemas.SignUpResponse`: Resultado de la operación, incluyendo el `user_sub` y `user_id`.
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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

    image_bytes = await profile_image.read() if profile_image else None

    result = cognito_service.sign_up(db=db, user_data=user_data, profile_image=image_bytes)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    
    return result

@router.post(
    "/confirm", 
    response_model=schemas.MessageResponse, 
    status_code=status.HTTP_200_OK
)
async def confirm_signup(data: schemas.ConfirmSignUpRequest):
    """
    Autor: Gabriel Vilchis
    Confirma una cuenta de usuario pendiente utilizando el código de verificación
    enviado al email del usuario.

    Args:
        data (`schemas.ConfirmSignUpRequest`): Objeto con el email del usuario y el código de 6 dígitos.

    Returns:
        `schemas.MessageResponse`: Mensaje de éxito o error de la confirmación.
    """
    result = cognito_service.confirm_sign_up(data.email, data.code)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result

@router.post("/resend-code", response_model=schemas.MessageResponse)
async def resend_code(data: schemas.ResendCodeRequest):
    """
    Autor: Gabriel Vilchis
    Solicita a Cognito el reenvío de un código de confirmación de registro
    a un email que aún no ha sido verificado.

    Args:
        data (`schemas.ResendCodeRequest`): Objeto que contiene el email del usuario.

    Returns:
        `schemas.MessageResponse`: Mensaje de éxito o error.
    """
    result = cognito_service.resend_confirmation_code(data.email)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result

@router.post("/login", response_model=schemas.TokenResponse)
async def login(credentials: schemas.SignInRequest):
    """
    Autor: Gabriel Vilchis
    Autentica al usuario usando email y contraseña.

    Si las credenciales son válidas, devuelve los tokens JWT de acceso (`access_token`),
    ID (`id_token`) y refresco (`refresh_token`).

    Args:
        credentials (`schemas.SignInRequest`): Objeto con el email y la contraseña.

    Returns:
        `schemas.TokenResponse`: Objeto que contiene los tokens JWT.
    """
    result = cognito_service.sign_in(credentials.email, credentials.password)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result["error"])
    
    # El servicio devuelve un dict, lo usamos para poblar el schema de respuesta
    return schemas.TokenResponse(
        success=True,
        access_token=result["access_token"],
        id_token=result["id_token"],
        refresh_token=result.get("refresh_token"),
        expires_in=result["expires_in"],
        token_type="Bearer"
    )

@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_access_token(data: schemas.RefreshTokenRequest):
    """
    Autor: Gabriel Vilchis
    Obtiene un nuevo Access Token e ID Token utilizando un Refresh Token.

    Esto permite mantener la sesión del usuario sin obligarlo a iniciar sesión nuevamente.

    Args:
        data (`schemas.RefreshTokenRequest`): Objeto que contiene el `refresh_token`.

    Returns:
        `schemas.TokenResponse`: Un nuevo Access Token, ID Token y el Refresh Token original.
    """
    result = cognito_service.refresh_token(data.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.get("error"))
    
    return schemas.TokenResponse(
        success=True,
        access_token=result["access_token"],
        id_token=result["id_token"],
        refresh_token=data.refresh_token, # Reutiliza el mismo refresh token
        expires_in=result["expires_in"],
        token_type="Bearer"
    )

@router.post("/logout", response_model=schemas.MessageResponse)
async def logout(token: str = Depends(get_token_from_header)):
    """
    Autor: Gabriel Vilchis
    Cierra la sesión del usuario en AWS Cognito, invalidando el Access Token.

    El Access Token se obtiene automáticamente de la cabecera 'Authorization' (Bearer Token)
    a través de la dependencia `get_token_from_header`.

    Args:
        token (str): El Access Token del usuario.

    Returns:
        `schemas.MessageResponse`: Mensaje de éxito del cierre de sesión.
    """
    result = cognito_service.sign_out(token)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result

@router.post("/forgot-password", response_model=schemas.MessageResponse)
async def forgot_password(data: schemas.ForgotPasswordRequest):
    """
    Autor: Gabriel Vilchis
    Solicita el inicio del proceso de recuperación de contraseña.

    Cognito envía un código de verificación al email del usuario asociado a la cuenta.

    Args:
        data (`schemas.ForgotPasswordRequest`): Objeto que contiene el email del usuario.

    Returns:
        `schemas.MessageResponse`: Mensaje de éxito o error.
    """
    result = cognito_service.forgot_password(data.email)
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result

@router.post("/confirm-forgot-password", response_model=schemas.MessageResponse)
async def confirm_forgot_password(data: schemas.ConfirmForgotPasswordRequest):
    """
    Autor: Gabriel Vilchis
    Confirma el restablecimiento de la contraseña utilizando el código de verificación
    enviado previamente y establece la nueva contraseña.

    Args:
        data (`schemas.ConfirmForgotPasswordRequest`): Objeto con email, código de verificación y la nueva contraseña.

    Returns:
        `schemas.MessageResponse`: Mensaje de éxito o error.
    """
    result = cognito_service.confirm_forgot_password(
        data.email, data.code, data.new_password
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result

@router.post("/change-password", response_model=schemas.MessageResponse)
async def change_password(
    data: schemas.ChangePasswordRequest,
    token: str = Depends(get_token_from_header)
):
    """
    Autor: Luis Flores
    Cambia la contraseña del usuario autenticado.
    
    Requiere autenticación y la contraseña actual.
    
    Args:
        data (schemas.ChangePasswordRequest): Contraseña actual y nueva.
        token (str): Token de autenticación del usuario.
    
    Returns:
        schemas.MessageResponse: Mensaje de éxito o error.
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