from app.core.database import SessionLocal
from app.models.loyalty_tier import LoyaltyTier
from decimal import Decimal

def seed_loyalty_tiers():
    db = SessionLocal()
    
    try:
        # Verificar si ya existen tiers
        existing = db.query(LoyaltyTier).count()
        if existing > 0:
            print(f"⚠️  Ya existen {existing} niveles de lealtad")
            return
        
        # Nivel 1: Bronce
        tier1 = LoyaltyTier(
            tier_level=1,
            min_points_required=0,
            points_multiplier=Decimal('1.0'),
            free_shipping_threshold=Decimal('1000.0'),
            monthly_coupons_count=1,
            coupon_discount_percentage=5
        )
        
        # Nivel 2: Plata
        tier2 = LoyaltyTier(
            tier_level=2,
            min_points_required=500,
            points_multiplier=Decimal('1.5'),
            free_shipping_threshold=Decimal('500.0'),
            monthly_coupons_count=2,
            coupon_discount_percentage=10
        )
        
        # Nivel 3: Oro
        tier3 = LoyaltyTier(
            tier_level=3,
            min_points_required=1500,
            points_multiplier=Decimal('2.0'),
            free_shipping_threshold=Decimal('0.0'),  # Envío gratis siempre
            monthly_coupons_count=3,
            coupon_discount_percentage=15
        )
        
        db.add_all([tier1, tier2, tier3])
        db.commit()
        
        print("✅ Niveles de lealtad creados exitosamente:")
        print("   - Nivel 1 (Bronce): 0+ puntos")
        print("   - Nivel 2 (Plata): 500+ puntos")
        print("   - Nivel 3 (Oro): 1500+ puntos")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_loyalty_tiers()