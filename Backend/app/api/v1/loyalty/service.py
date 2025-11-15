from sqlalchemy.orm import Session
from typing import Dict
from datetime import date, timedelta
from app.models.user import User
from app.models.user_loyalty import UserLoyalty
from app.models.loyalty_tier import LoyaltyTier
from app.models.point_history import PointHistory

class LoyaltyService:
    
    def get_user_loyalty_status(self, db: Session, cognito_sub: str) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(UserLoyalty.user_id == user.user_id).first()
            
            if not user_loyalty:
                tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
                
                user_loyalty = UserLoyalty(
                    user_id=user.user_id,
                    tier_id=tier_1.tier_id,
                    total_points=0,
                    tier_achieved_date=date.today(),
                    last_points_update=date.today(),
                    points_expiration_date=None
                )
                db.add(user_loyalty)
                db.commit()
                db.refresh(user_loyalty)
            
            current_tier = user_loyalty.loyalty_tier
            
            points_to_next = None
            next_tier_level = None
            
            next_tier = db.query(LoyaltyTier).filter(
                LoyaltyTier.tier_level > current_tier.tier_level
            ).order_by(LoyaltyTier.tier_level).first()
            
            if next_tier:
                points_to_next = next_tier.min_points_required - user_loyalty.total_points
                next_tier_level = next_tier.tier_level
            
            current_benefits = {
                "monthly_coupons": current_tier.monthly_coupons_count,
                "coupon_discount": current_tier.coupon_discount_percentage,
            }
            
            if current_tier.free_shipping_threshold == 0:
                current_benefits["free_shipping"] = "Envío gratis en todas las compras"
            elif current_tier.free_shipping_threshold > 0:
                current_benefits["free_shipping"] = f"Envío gratis en compras mayores a ${current_tier.free_shipping_threshold}"
            else:
                current_benefits["free_shipping"] = "No incluido"
            
            return {
                "success": True,
                "loyalty": {
                    "loyalty_id": user_loyalty.loyalty_id,
                    "user_id": user_loyalty.user_id,
                    "total_points": user_loyalty.total_points,
                    "tier_level": current_tier.tier_level,
                    "tier_achieved_date": user_loyalty.tier_achieved_date,
                    "last_points_update": user_loyalty.last_points_update,
                    "points_expiration_date": user_loyalty.points_expiration_date,
                    "points_to_next_tier": points_to_next,
                    "next_tier_level": next_tier_level,
                    "current_benefits": current_benefits
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener estado de lealtad: {str(e)}"}
    
    def add_points(self, db: Session, loyalty_id: int, points: int, order_id: int) -> Dict:
        try:
            user_loyalty = db.query(UserLoyalty).filter(UserLoyalty.loyalty_id == loyalty_id).first()
            
            if not user_loyalty:
                return {"success": False, "error": "Información de lealtad no encontrada"}
            
            if user_loyalty.points_expiration_date is None:
                current_tier = user_loyalty.loyalty_tier
                if current_tier.tier_level == 1:
                    user_loyalty.points_expiration_date = date.today() + timedelta(days=180)
            
            user_loyalty.total_points += points
            user_loyalty.last_points_update = date.today()
            
            history_entry = PointHistory(
                loyalty_id=loyalty_id,
                order_id=order_id,
                points_change=points,
                event_type="earned",
                event_date=date.today()
            )
            db.add(history_entry)
            
            self._check_tier_upgrade(db, user_loyalty)
            
            db.commit()
            db.refresh(user_loyalty)
            
            return {
                "success": True,
                "new_total": user_loyalty.total_points,
                "points_added": points,
                "expiration_date": user_loyalty.points_expiration_date
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al agregar puntos: {str(e)}"}
    
    def expire_points_for_user(self, db: Session, cognito_sub: str) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(UserLoyalty.user_id == user.user_id).first()
            
            if not user_loyalty:
                return {"success": False, "error": "Información de programa de puntos no encontrada"}
            
            if not user_loyalty.points_expiration_date:
                return {
                    "success": True,
                    "points_expired": 0,
                    "new_total": user_loyalty.total_points,
                    "tier_reset": False,
                    "new_tier_level": user_loyalty.loyalty_tier.tier_level,
                    "message": "Usuario no tiene puntos o no tiene fecha de expiración establecida"
                }
            
            today = date.today()
            if user_loyalty.points_expiration_date > today:
                return {
                    "success": True,
                    "points_expired": 0,
                    "message": f"Los puntos no han expirado aún. Expiran el {user_loyalty.points_expiration_date}"
                }
            
            points_before = user_loyalty.total_points
            if points_before > 0:
                expiration_record = PointHistory(
                    loyalty_id=user_loyalty.loyalty_id,
                    order_id=None,
                    points_change=-points_before,
                    event_type="expired",
                    event_date=today
                )
                db.add(expiration_record)
            
            user_loyalty.total_points = 0
            user_loyalty.last_points_update = today
            user_loyalty.points_expiration_date = None
            
            tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
            tier_changed = user_loyalty.tier_id != tier_1.tier_id
            user_loyalty.tier_id = tier_1.tier_id
            user_loyalty.tier_achieved_date = today
            
            db.commit()
            
            return {
                "success": True,
                "points_expired": points_before,
                "new_total": 0,
                "tier_reset": tier_changed,
                "new_tier_level": 1
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al expirar puntos: {str(e)}"}
    
    def expire_all_points(self, db: Session) -> Dict:
        try:
            today = date.today()
            
            expired_loyalties = db.query(UserLoyalty).filter(
                UserLoyalty.points_expiration_date.isnot(None),
                UserLoyalty.points_expiration_date <= today
            ).all()
            
            users_affected = 0
            total_expired_points = 0
            
            tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
            
            for user_loyalty in expired_loyalties:
                if user_loyalty.total_points > 0:
                    expiration_record = PointHistory(
                        loyalty_id=user_loyalty.loyalty_id,
                        order_id=None,
                        points_change=-user_loyalty.total_points,
                        event_type="expired",
                        event_date=today
                    )
                    db.add(expiration_record)
                    
                    total_expired_points += user_loyalty.total_points
                    users_affected += 1
                
                user_loyalty.total_points = 0
                user_loyalty.last_points_update = today
                user_loyalty.points_expiration_date = None
                user_loyalty.tier_id = tier_1.tier_id
                user_loyalty.tier_achieved_date = today
            
            db.commit()
            
            return {
                "success": True,
                "users_affected": users_affected,
                "total_expired_points": total_expired_points
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error en proceso de expiración batch: {str(e)}"}
    
    def _check_tier_upgrade(self, db: Session, user_loyalty: UserLoyalty) -> Dict:
        try:
            current_tier = user_loyalty.loyalty_tier
            
            highest_tier = db.query(LoyaltyTier).filter(
                LoyaltyTier.min_points_required <= user_loyalty.total_points
            ).order_by(LoyaltyTier.tier_level.desc()).first()
            
            if highest_tier and highest_tier.tier_level > current_tier.tier_level:
                user_loyalty.tier_id = highest_tier.tier_id
                user_loyalty.tier_achieved_date = date.today()
                return {"upgraded": True, "new_tier": highest_tier.tier_level}
            
            return {"upgraded": False}
        except Exception as e:
            return {"upgraded": False, "error": str(e)}
    
    def get_all_tiers(self, db: Session) -> Dict:
        try:
            tiers = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).all()
            
            return {"success": True, "tiers": tiers}
        except Exception as e:
            return {"success": False, "error": f"Error al obtener niveles de lealtad: {str(e)}"}
    
    def get_tier_by_id(self, db: Session, tier_id: int) -> Dict:
        try:
            tier = db.query(LoyaltyTier).filter(LoyaltyTier.tier_id == tier_id).first()
            
            if not tier:
                return {"success": False, "error": "Nivel no encontrado"}
            
            return {"success": True, "tier": tier}
        except Exception as e:
            return {"success": False, "error": f"Error al obtener nivel: {str(e)}"}
    
    def get_point_history(self, db: Session, cognito_sub: str, limit: int = 50) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(UserLoyalty.user_id == user.user_id).first()
            
            if not user_loyalty:
                return {"success": False, "error": "Información de programa de puntos no encontrada"}
            
            history = db.query(PointHistory).filter(
                PointHistory.loyalty_id == user_loyalty.loyalty_id
            ).order_by(PointHistory.event_date.desc()).limit(limit).all()
            
            return {
                "success": True,
                "history": history,
                "total": len(history)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener historial: {str(e)}"}

loyalty_service = LoyaltyService()