from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

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

class UserLoyaltyResponse(BaseModel):
    loyalty_id: int
    user_id: int
    total_points: int
    tier_level: int
    tier_achieved_date: date
    last_points_update: date
    points_expiration_date: Optional[date] = None
    points_to_next_tier: Optional[int] = None
    next_tier_level: Optional[int] = None
    current_benefits: dict
    
    class Config:
        from_attributes = True

class PointHistoryResponse(BaseModel):
    point_history_id: int
    loyalty_id: int
    order_id: Optional[int] = None
    points_change: int
    event_type: str
    event_date: date
    
    class Config:
        from_attributes = True

class LoyaltyTiersListResponse(BaseModel):
    success: bool
    tiers: List[LoyaltyTierResponse]

class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class ExpirePointsResponse(BaseModel):
    success: bool
    points_expired: int
    new_total: int
    tier_reset: bool
    new_tier_level: int
    message: Optional[str] = None

class AddPointsResponse(BaseModel):
    success: bool
    new_total: int
    points_added: int
    expiration_date: Optional[date] = None