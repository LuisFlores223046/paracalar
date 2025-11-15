from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.models.enum import PaymentType

class PaymentMethodService:
    
    def get_user_payment_methods(self, db: Session, cognito_sub: str) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            payment_methods = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).all()
            
            return {
                "success": True,
                "payment_methods": payment_methods,
                "total": len(payment_methods)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener métodos de pago: {str(e)}"}
    
    def get_payment_method_by_id(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            return {"success": True, "payment_method": payment_method}
        except Exception as e:
            return {"success": False, "error": f"Error al obtener método de pago: {str(e)}"}
    
    def create_payment_method(
        self, db: Session, cognito_sub: str, payment_type: PaymentType,
        provider_ref: str, last_four: str, expiration_date: Optional[str],
        is_default: bool = False
    ) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            if is_default:
                db.query(PaymentMethod).filter(
                    PaymentMethod.user_id == user.user_id,
                    PaymentMethod.is_default == True
                ).update({"is_default": False})
            
            new_payment_method = PaymentMethod(
                user_id=user.user_id,
                payment_type=payment_type,
                provider_ref=provider_ref,
                last_four=last_four,
                expiration_date=expiration_date,
                is_default=is_default
            )
            
            db.add(new_payment_method)
            db.commit()
            db.refresh(new_payment_method)
            
            return {"success": True, "message": "Método de pago agregado correctamente", "payment_method": new_payment_method}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al crear método de pago: {str(e)}"}

    def delete_payment_method(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            db.delete(payment_method)
            db.commit()
            
            return {"success": True, "message": "Método de pago eliminado correctamente"}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al eliminar método de pago: {str(e)}"}
    
    def set_default_payment_method(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_id != payment_id
            ).update({"is_default": False})
            
            payment_method.is_default = True
            db.commit()
            db.refresh(payment_method)
            
            return {"success": True, "message": "Método de pago establecido como predeterminado", "payment_method": payment_method}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al establecer método de pago predeterminado: {str(e)}"}

payment_method_service = PaymentMethodService()