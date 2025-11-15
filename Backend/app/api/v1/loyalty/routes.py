from fastapi import APIRouter, HTTPException, Depends, status, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.loyalty import schemas
from app.api.v1.loyalty.service import loyalty_service

router = APIRouter(prefix="/loyalty", tags=["Loyalty Program"])
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

@router.get("/me", response_model=schemas.UserLoyaltyResponse, status_code=status.HTTP_200_OK)
async def get_my_loyalty_status(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    cognito_sub = current_user.get("sub")
    result = loyalty_service.get_user_loyalty_status(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error")
        )
    
    return result["loyalty"]

@router.get("/tiers", response_model=schemas.LoyaltyTiersListResponse, status_code=status.HTTP_200_OK)
async def get_all_loyalty_tiers(db: Session = Depends(get_db)):
    result = loyalty_service.get_all_tiers(db=db)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.get("/tiers/{tier_id}", response_model=schemas.LoyaltyTierResponse, status_code=status.HTTP_200_OK)
async def get_tier_details(tier_id: int, db: Session = Depends(get_db)):
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
    cognito_sub = current_user.get("sub")
    result = loyalty_service.get_point_history(db=db, cognito_sub=cognito_sub, limit=limit)
    
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
    cognito_sub = current_user.get("sub")
    result = loyalty_service.expire_points_for_user(db=db, cognito_sub=cognito_sub)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result