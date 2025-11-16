from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

"""
Schema de respuesta para el loyalty tier
"""
class LoyaltyTierResponse(BaseModel):
    tier_id: int
    tier_level: int
    min_points_required: int
    points_multiplier: Decimal
    free_shipping_threshold: Decimal
    monthly_coupons_count: int
    coupon_discount_percentage: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "tier_id": 2,
                "tier_level": 2,
                "min_points_required": 1000,
                "points_multiplier": 1.5,
                "free_shipping_threshold": 1000.00,
                "monthly_coupons_count": 3,
                "coupon_discount_percentage": 10
            }
        }

"""
Schema de respuesta para el loyalty del usuario
"""
class UserLoyaltyResponse(BaseModel):
    loyalty_id: int
    user_id: int
    total_points: int
    tier_level: int
    tier_achieved_date: date
    last_points_update: date
    points_expiration_date: Optional[date] = None
    points_to_next_tier: Optional[int] = None # Estos 3 son auxiliares
    next_tier_level: Optional[int] = None     # que no estan en los modelos
    current_benefits: dict                    # pero ayudan en las vistas (creo) (espero)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "loyalty_id": 1,
                "user_id": 1,
                "total_points": 1500,
                "tier_level": 2,
                "tier_achieved_date": "2024-06-15",
                "last_points_update": "2024-11-10",
                "points_expiration_date": "2025-05-10",
                "points_to_next_tier": 1500,
                "next_tier_level": 3,
                "current_benefits": {
                    "monthly_coupons": 3,
                    "coupon_discount": 10,
                    "free_shipping": "En compras mayores a $1000"
                }
            }
        }

"""
Schema de respuesta para entrada de puntos
"""
class PointHistoryResponse(BaseModel):
    point_history_id: int
    loyalty_id: int
    order_id: Optional[int] = None
    points_change: int
    event_type: str
    event_date: date
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "point_history_id": 1,
                "loyalty_id": 1,
                "order_id": 123,
                "points_change": 300,
                "event_type": "earned",
                "event_date": "2024-11-10"
            }
        }

"""
Schema de todos los tiers
"""
class LoyaltyTiersListResponse(BaseModel):
    success: bool
    tiers: List[LoyaltyTierResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "tiers": []
            }
        }

"""
Schema genérico para respuestas con mensaje
"""
class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

"""
Schema de respuesta para expiracion de puntos
"""
class ExpirePointsResponse(BaseModel):
    success: bool
    points_expired: int
    new_total: int
    tier_reset: bool
    new_tier_level: int
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "points_expired": 1500,
                "new_total": 0,
                "tier_reset": True,
                "new_tier_level": 1,
                "message": None
            }
        }

"""
Schema de respuesta para agregar puntos
"""
class AddPointsResponse(BaseModel):
    success: bool
    new_total: int
    points_added: int
    expiration_date: Optional[date] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "new_total": 500,
                "points_added": 500,
                "expiration_date": "2025-05-12"
            }
        }
