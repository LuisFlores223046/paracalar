# Autor: Lizbeth Barajas y Gabriel Vilchis
# Fecha: 15-11-2025
# Descripción: Servicio encargado de gestionar el programa de lealtad, puntos, tiers y cupones

from sqlalchemy.orm import Session
from typing import Dict
from datetime import date, timedelta
from app.models.user import User
from app.models.user_loyalty import UserLoyalty
from app.models.loyalty_tier import LoyaltyTier
from app.models.point_history import PointHistory
from app.models.user_coupon import UserCoupon
from app.models.coupon import Coupon
from decimal import Decimal
import random
import string

class LoyaltyService:
    
    def get_user_loyalty_status(self, db: Session, cognito_sub: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene toda la información del estado de lealtad del usuario, incluyendo puntos,
            tier actual, beneficios y puntos requeridos para el siguiente nivel.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.

        Retorna:
            Dict: Resultado de la operación con información completa del estado de lealtad.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(
                UserLoyalty.user_id == user.user_id
            ).first()
            
            # Si el usuario no tiene un record de puntos (usuarios nuevos) lo crea
            if not user_loyalty:
                tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
                
                user_loyalty = UserLoyalty(
                    user_id=user.user_id,
                    tier_id=tier_1.tier_id,
                    total_points=0,
                    tier_achieved_date=date.today(),
                    last_points_update=date.today(),
                    points_expiration_date=None  # Se establece cuando gana sus primeros puntos
                )
                db.add(user_loyalty)
                db.commit()
                db.refresh(user_loyalty)
            
            current_tier = user_loyalty.loyalty_tier
            
            # Calculo de auxiliares
            points_to_next = None
            next_tier_level = None
            
            next_tier = db.query(LoyaltyTier).filter(
                LoyaltyTier.tier_level > current_tier.tier_level
            ).order_by(LoyaltyTier.tier_level).first()
            
            if next_tier:
                points_to_next = next_tier.min_points_required - user_loyalty.total_points
                next_tier_level = next_tier.tier_level
            
            # Descripcion de beneficios actuales - tambien aux
            current_benefits = {
                "monthly_coupons": current_tier.monthly_coupons_count,
                "coupon_discount": current_tier.coupon_discount_percentage,
            }
            
            # envio gratis de tiers
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
        """
        Autor: Lizbeth Barajas

        Descripción:
            Agrega puntos al usuario cuando completa una orden e inserta un registro en el historial.
            Si el usuario está en tier 1 y es su primer acumulado, define la fecha de expiración.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            loyalty_id (int): Identificador del registro de lealtad del usuario.
            points (int): Puntos a agregar.
            order_id (int): Identificador de la orden asociada al evento.

        Retorna:
            Dict: Resultado de la operación, incluyendo el nuevo total de puntos y expiración.
        """
        try:
            user_loyalty = db.query(UserLoyalty).filter(
                UserLoyalty.loyalty_id == loyalty_id
            ).first()
            
            if not user_loyalty:
                return {"success": False, "error": "Información de lealtad no encontrada"}
            
            # Si no tiene fecha de expiracion establecida y esta en tier 1, establecerla
            if user_loyalty.points_expiration_date is None:
                current_tier = user_loyalty.loyalty_tier
                if current_tier.tier_level == 1:
                    # Establecer fecha de expiracion 6 meses desde hoy
                    user_loyalty.points_expiration_date = date.today() + timedelta(days=180)
            
            # Agregar puntos
            user_loyalty.total_points += points
            user_loyalty.last_points_update = date.today()
            
            # Crear registro en historial
            history_entry = PointHistory(
                loyalty_id=loyalty_id,
                order_id=order_id,
                points_change=points,
                event_type="earned",
                event_date=date.today()
            )
            db.add(history_entry)
            
            # Verificar si debe subir de tier
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
        """
        Autor: Lizbeth Barajas

        Descripción:
            Expira los puntos del usuario indicado, creando un registro en el historial y
            reiniciando su tier si corresponde. Se usa para pruebas o ejecución manual.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.

        Retorna:
            Dict: Información sobre puntos expirados, tier nuevo y resultado general.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(
                UserLoyalty.user_id == user.user_id
            ).first()
            
            if not user_loyalty:
                return {"success": False, "error": "Información de programa de puntos no encontrada"}
            
            # Verificar si tiene fecha de expiracion y si ya llego
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
            
            # Crear registro de expiracion en historial
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
            
            # Resetear puntos y tier al nivel 1
            tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
            tier_reset = user_loyalty.loyalty_tier.tier_level > 1
            
            user_loyalty.total_points = 0
            user_loyalty.last_points_update = today
            user_loyalty.points_expiration_date = None
            user_loyalty.tier_id = tier_1.tier_id
            user_loyalty.tier_achieved_date = today
            
            db.commit()
            db.refresh(user_loyalty)
            
            return {
                "success": True,
                "points_expired": points_before,
                "new_total": 0,
                "tier_reset": tier_reset,
                "new_tier_level": 1,
                "message": f"Se expiraron {points_before} puntos"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al expirar puntos: {str(e)}"}
    
    def expire_all_points(self, db: Session) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Proceso masivo que expira los puntos de todos los usuarios cuya fecha de expiración
            ya venció. Se usa en tareas programadas (cron job).

        Parámetros:
            db (Session): Sesión activa de la base de datos.

        Retorna:
            Dict: Estadísticas del proceso, incluyendo usuarios afectados y total de puntos expirados.
        """
        try:
            today = date.today()
            
            # Obtener todos los usuarios cuya fecha de expiracion ya paso
            expired_loyalties = db.query(UserLoyalty).filter(
                UserLoyalty.points_expiration_date.isnot(None),
                UserLoyalty.points_expiration_date <= today
            ).all()
            
            users_affected = 0
            total_expired_points = 0
            
            tier_1 = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).first()
            
            for user_loyalty in expired_loyalties:
                if user_loyalty.total_points > 0:
                    # Crear registro de expiracion
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
                
                # Resetear puntos y tier
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
        """
        Autor: Lizbeth Barajas

        Descripción:
            Verifica si el usuario debe subir de tier al superar el mínimo requerido de puntos.
            Actualiza el tier del usuario cuando corresponde.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            user_loyalty (UserLoyalty): Registro de lealtad del usuario.

        Retorna:
            Dict: Información sobre si hubo ascenso y el nuevo tier si aplica.
        """
        try:
            current_tier = user_loyalty.loyalty_tier
            
            # Encontrar el siguiente tier
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
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene toda la información de los niveles (tiers) registrados en el sistema.

        Parámetros:
            db (Session): Sesión activa de la base de datos.

        Retorna:
            Dict: Lista de niveles ordenados por su tier_level.
        """
        try:
            tiers = db.query(LoyaltyTier).order_by(LoyaltyTier.tier_level).all()
            
            return {
                "success": True,
                "tiers": tiers
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener niveles de lealtad: {str(e)}"}
    
    def get_tier_by_id(self, db: Session, tier_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene la información de un tier específico a partir de su ID.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            tier_id (int): Identificador del nivel de lealtad.

        Retorna:
            Dict: Información del tier solicitado o error si no existe.
        """
        try:
            tier = db.query(LoyaltyTier).filter(LoyaltyTier.tier_id == tier_id).first()
            
            if not tier:
                return {"success": False, "error": "Nivel no encontrado"}
            
            return {
                "success": True,
                "tier": tier
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener nivel: {str(e)}"}
    
    def get_point_history(self, db: Session, cognito_sub: str, limit: int = 50) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene el historial de movimientos de puntos de un usuario, ordenado por fecha.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.
            limit (int): Número máximo de registros a devolver.

        Retorna:
            Dict: Lista de eventos de puntos y total de registros obtenidos.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            user_loyalty = db.query(UserLoyalty).filter(
                UserLoyalty.user_id == user.user_id
            ).first()
            
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

    @staticmethod
    def generate_random_coupon_code(length: int = 6) -> str:
        """
        Autor: Gabriel Vilchis

        Descripción:
            Genera un código aleatorio compuesto de letras mayúsculas y dígitos.

        Parámetros:
            length (int): Longitud del código a generar. Por defecto es 6.

        Retorna:
            str: Código generado aleatoriamente.
        """
        characters = string.ascii_uppercase + string.digits
        # en produccion, verificar la unicidad del codigo
        return "".join(random.choice(characters) for _ in range(length))

    def generate_monthly_coupons_for_user(self, db: Session, user_id: int):
        """
        Autor: Gabriel Vilchis

        Descripción:
            Genera y asigna cupones al usuario según su nivel de lealtad. Los cupones incluyen
            fecha de inicio, expiración, valor de descuento y se registran como activos.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            user_id (int): Identificador del usuario al que se asignarán los cupones.

        Retorna:
            list[str]: Lista de códigos de cupones generados.
        """

        try:
            current_date = date.today()
            expiration_date = current_date + timedelta(days=30)
      
            user_loyalty = db.query(UserLoyalty).filter(UserLoyalty.user_id == user_id).first()
            
            if not user_loyalty:
                raise ValueError(f"No se encontro el perfil de lealtad para el usuario ID: {user_id}")
                
            tier_info = user_loyalty.loyalty_tier
            
            if not tier_info:
                raise ValueError("El perfil de lealtad no tiene un tier asociado.")

            # Usar los campos del modelo LoyaltyTier:
            num_coupons = tier_info.monthly_coupons_count # Nivel 1=1, Nivel 2=3, Nivel 3=5
            discount_percent = tier_info.coupon_discount_percentage # Nivel 1=5, Nivel 2=10, Nivel 3=15

            # El campo discount_value es Decimal(5, 2), por lo que 5% es 5.00
            discount_value = Decimal(discount_percent)
            
            generated_coupons = []
            
            for _ in range(num_coupons):
                coupon_code = LoyaltyService.generate_random_coupon_code() 
                
                new_coupon = Coupon(
                    coupon_code=coupon_code,
                    discount_value=discount_value,
                    start_date=current_date,
                    expiration_date=expiration_date,
                    is_active=True
                )
                
                db.add(new_coupon)
                db.flush()  # Para obtener el coupon_id

                user_coupon_assignment = UserCoupon(
                    user_id=user_id,
                    coupon_id=new_coupon.coupon_id,
                    used_date=None # Inicialmente no ha sido usado
                )
                
                db.add(user_coupon_assignment)
                generated_coupons.append(coupon_code)

            db.commit()
            
            print(f"Se generaron y asignaron {num_coupons} cupones al usuario ID {user_id} para el Tier {tier_info.tier_level}.")
                
            return generated_coupons
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al generar cupones: {str(e)}")
    
loyalty_service = LoyaltyService()