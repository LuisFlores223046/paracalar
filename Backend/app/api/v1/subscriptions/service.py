# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 17/11/2025
# Descripción: Servicio de lógica de negocio para gestión de suscripciones,
#              cobros recurrentes, selección de productos y manejo de estados.

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, List
from datetime import date, timedelta
from decimal import Decimal

from app.models.subscription import Subscription
from app.models.user import User
from app.models.fitness_profile import FitnessProfile
from app.models.payment_method import PaymentMethod
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.address import Address
from app.models.enum import SubscriptionStatus, OrderStatus, PaymentType
from app.services.stripe_service import stripe_service


class SubscriptionService:
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Servicio para gestión completa de suscripciones mensuales.
                 Maneja creación, actualización, pausado, cancelación y cobros automáticos.
    """
    
    # Precio fijo mensual de la suscripción
    MONTHLY_SUBSCRIPTION_PRICE = Decimal("499.00")
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: int,
        payment_method_id: int
    ) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Crea una nueva suscripción para un usuario.
                     Requiere que el usuario tenga un fitness profile y un método de pago válido.
                     Realiza el primer cobro inmediatamente al crear la suscripción.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario que solicita la suscripción.
            payment_method_id (int): ID del método de pago guardado a utilizar.
        Retorna:
            Dict: Diccionario con success, message, subscription y first_order_id si fue exitoso.
                  En caso de error retorna success=False y error con el mensaje.
        """
        try:
            # Verificar que el usuario existe y está activo
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Verificar que no tiene suscripción activa
            existing_sub = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.subscription_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED])
            ).first()
            
            if existing_sub:
                return {"success": False, "error": "El usuario ya tiene una suscripción activa"}
            
            # Verificar que tiene fitness profile
            fitness_profile = db.query(FitnessProfile).filter(
                FitnessProfile.user_id == user_id
            ).first()
            
            if not fitness_profile:
                return {"success": False, "error": "El usuario debe completar el test de posicionamiento primero"}
            
            # Verificar que el método de pago existe y pertenece al usuario
            payment_method = db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.payment_id == payment_method_id,
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
                )
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no válido o no encontrado"}
            
            # Crear la suscripción
            today = date.today()
            next_month = today + timedelta(days=30)
            
            new_subscription = Subscription(
                user_id=user_id,
                profile_id=fitness_profile.profile_id,
                payment_method_id=payment_method_id,
                subscription_status=SubscriptionStatus.ACTIVE,
                start_date=today,
                next_delivery_date=next_month,
                auto_renew=True,
                price=SubscriptionService.MONTHLY_SUBSCRIPTION_PRICE,
                last_payment_date=None,  # Se actualizará con el primer cobro
                failed_payment_attempts=0
            )
            
            db.add(new_subscription)
            db.flush()
            
            # Realizar el primer cobro inmediatamente
            first_charge_result = SubscriptionService._process_subscription_charge(
                db=db,
                subscription=new_subscription,
                user=user
            )
            
            if not first_charge_result.get("success"):
                db.rollback()
                return {
                    "success": False,
                    "error": f"Error en el primer cobro: {first_charge_result.get('error')}"
                }
            
            db.commit()
            db.refresh(new_subscription)
            
            return {
                "success": True,
                "message": "Suscripción creada exitosamente",
                "subscription": new_subscription,
                "first_order_id": first_charge_result.get("order_id")
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al crear suscripción: {str(e)}"}
    
    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Obtiene la suscripción activa o existente del usuario.
                     Incluye información adicional como nombre del plan y últimos 4 dígitos de la tarjeta.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario del cual se consulta la suscripción.
        Retorna:
            Dict: Diccionario con success, has_subscription, subscription, plan_name y payment_last_four.
        """
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if not subscription:
                return {
                    "success": True,
                    "has_subscription": False,
                    "subscription": None
                }
            
            # Obtener info adicional
            plan_name = None
            if subscription.fitness_profile and subscription.fitness_profile.attributes:
                plan_name = subscription.fitness_profile.attributes.get("recommended_plan")
            
            payment_last_four = None
            if subscription.payment_method:
                payment_last_four = subscription.payment_method.last_four
            
            return {
                "success": True,
                "has_subscription": True,
                "subscription": subscription,
                "plan_name": plan_name,
                "payment_last_four": payment_last_four
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error al obtener suscripción: {str(e)}"}
    
    @staticmethod
    def pause_subscription(db: Session, user_id: int) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Pausa una suscripción activa del usuario.
                     Durante el pausado no se realizarán cobros ni envíos.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario cuya suscripción se pausará.
        Retorna:
            Dict: Diccionario con success, message y subscription si fue exitoso.
        """
        try:
            subscription = db.query(Subscription).filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.subscription_status == SubscriptionStatus.ACTIVE
                )
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No se encontró suscripción activa"}
            
            subscription.subscription_status = SubscriptionStatus.PAUSED
            db.commit()
            db.refresh(subscription)
            
            return {
                "success": True,
                "message": "Suscripción pausada exitosamente",
                "subscription": subscription
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al pausar suscripción: {str(e)}"}
    
    @staticmethod
    def resume_subscription(db: Session, user_id: int) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Reanuda una suscripción pausada, reactivando el ciclo de cobros y envíos.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario cuya suscripción se reanudará.
        Retorna:
            Dict: Diccionario con success, message y subscription si fue exitoso.
        """
        try:
            subscription = db.query(Subscription).filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.subscription_status == SubscriptionStatus.PAUSED
                )
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No se encontró suscripción pausada"}
            
            subscription.subscription_status = SubscriptionStatus.ACTIVE
            db.commit()
            db.refresh(subscription)
            
            return {
                "success": True,
                "message": "Suscripción reanudada exitosamente",
                "subscription": subscription
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al reanudar suscripción: {str(e)}"}
    
    @staticmethod
    def cancel_subscription(db: Session, user_id: int) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Cancela permanentemente una suscripción del usuario.
                     Esta acción es definitiva y requiere crear una nueva suscripción para reactivar.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario cuya suscripción se cancelará.
        Retorna:
            Dict: Diccionario con success y message indicando el resultado de la operación.
        """
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.subscription_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED])
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No se encontró suscripción para cancelar"}
            
            subscription.subscription_status = SubscriptionStatus.CANCELLED
            subscription.end_date = date.today()
            subscription.auto_renew = False
            
            db.commit()
            db.refresh(subscription)
            
            return {
                "success": True,
                "message": "Suscripción cancelada exitosamente",
                "subscription": subscription
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al cancelar suscripción: {str(e)}"}
    
    @staticmethod
    def update_payment_method(
        db: Session,
        user_id: int,
        new_payment_method_id: int
    ) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Actualiza el método de pago asociado a una suscripción activa.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario propietario de la suscripción.
            new_payment_method_id (int): ID del nuevo método de pago a asociar.
        Retorna:
            Dict: Diccionario con success y message indicando el resultado.
        """
        try:
            # Obtener suscripción activa
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.subscription_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED])
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No se encontró suscripción activa"}
            
            # Verificar que el nuevo método de pago existe y pertenece al usuario
            new_payment_method = db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.payment_id == new_payment_method_id,
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
                )
            ).first()
            
            if not new_payment_method:
                return {"success": False, "error": "Método de pago no válido o no encontrado"}
            
            # Actualizar método de pago
            subscription.payment_method_id = new_payment_method_id
            db.commit()
            db.refresh(subscription)
            
            return {
                "success": True,
                "message": "Método de pago actualizado exitosamente",
                "subscription": subscription
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al actualizar método de pago: {str(e)}"}
    
    @staticmethod
    def get_subscription_history(db: Session, user_id: int) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Obtiene el historial completo de órdenes generadas por la suscripción del usuario.
                     Incluye totales gastados y cantidad de órdenes.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            user_id (int): ID del usuario del cual se obtendrá el historial.
        Retorna:
            Dict: Diccionario con subscription, orders, total_orders y total_spent.
        """
        try:
            # Obtener suscripción
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No se encontró suscripción"}
            
            # Obtener todas las órdenes de la suscripción
            orders = db.query(Order).filter(
                Order.subscription_id == subscription.subscription_id
            ).order_by(Order.order_date.desc()).all()
            
            total_orders = len(orders)
            total_spent = sum(order.total_amount for order in orders)
            
            return {
                "success": True,
                "subscription": subscription,
                "orders": orders,
                "total_orders": total_orders,
                "total_spent": total_spent
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error al obtener historial: {str(e)}"}
    
    @staticmethod
    def _select_products_for_subscription(
        db: Session,
        fitness_profile: FitnessProfile
    ) -> List[Product]:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Selecciona hasta 3 productos personalizados basándose en el perfil fitness del usuario.
                     Prioriza productos que coincidan con el plan recomendado y objetivos fitness.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            fitness_profile (FitnessProfile): Perfil fitness del usuario con atributos y recomendaciones.
        Retorna:
            List[Product]: Lista de hasta 3 productos seleccionados para la suscripción.
        """
        attributes = fitness_profile.attributes or {}
        recommended_plan = attributes.get("recommended_plan", "")
        
        # Buscar productos que coincidan con el plan recomendado
        selected_products = []
        
        if recommended_plan:
            products = db.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.stock > 0,
                    Product.name.ilike(f"%{recommended_plan}%")
                )
            ).limit(3).all()
            
            selected_products.extend(products)
        
        # Si no se encontraron suficientes productos por nombre, buscar por objetivos
        if len(selected_products) < 3:
            fitness_objectives = attributes.get("fitness_objectives", [])
            
            additional_products = db.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.stock > 0,
                    Product.fitness_objectives.contains(fitness_objectives)
                )
            ).limit(3 - len(selected_products)).all()
            
            selected_products.extend(additional_products)
        
        return selected_products[:3]  # Máximo 3 productos por suscripción
    
    @staticmethod
    def _process_subscription_charge(
        db: Session,
        subscription: Subscription,
        user: User
    ) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: Procesa el cobro mensual de una suscripción y crea la orden correspondiente.
                     Realiza el cargo a través de Stripe, selecciona productos personalizados,
                     crea la orden y actualiza el inventario.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
            subscription (Subscription): Objeto de suscripción a cobrar.
            user (User): Usuario propietario de la suscripción.
        Retorna:
            Dict: Diccionario con success, order_id y message si fue exitoso.
                  En caso de error, incluye el mensaje de error.
        """
        try:
            # Verificar que tiene stripe_customer_id
            if not user.stripe_customer_id:
                return {"success": False, "error": "Usuario no tiene customer ID de Stripe"}
            
            # Obtener payment method
            payment_method = subscription.payment_method
            if not payment_method or not payment_method.provider_ref:
                return {"success": False, "error": "Método de pago no válido"}
            
            # Seleccionar productos
            products = SubscriptionService._select_products_for_subscription(
                db, subscription.fitness_profile
            )
            
            if not products:
                return {"success": False, "error": "No se pudieron seleccionar productos para la suscripción"}
            
            # Obtener dirección predeterminada del usuario
            default_address = db.query(Address).filter(
                and_(
                    Address.user_id == user.user_id,
                    Address.is_default == True
                )
            ).first()
            
            if not default_address:
                # Si no tiene default, tomar la primera
                default_address = db.query(Address).filter(
                    Address.user_id == user.user_id
                ).first()
            
            if not default_address:
                return {"success": False, "error": "Usuario no tiene dirección de envío registrada"}
            
            # Realizar cobro con Stripe
            charge_result = stripe_service.create_payment_intent_with_saved_card(
                amount=int(subscription.price * 100),  # Convertir a centavos
                currency="mxn",
                customer_id=user.stripe_customer_id,
                payment_method_id=payment_method.provider_ref,
                description=f"Suscripción mensual BeFit - {date.today().strftime('%B %Y')}",
                metadata={
                    "subscription_id": str(subscription.subscription_id),
                    "user_id": str(user.user_id)
                }
            )
            
            if not charge_result.get("success"):
                # Incrementar intentos fallidos
                subscription.failed_payment_attempts += 1
                
                # Si falla 3 veces, pausar la suscripción
                if subscription.failed_payment_attempts >= 3:
                    subscription.subscription_status = SubscriptionStatus.PAUSED
                
                db.commit()
                return {
                    "success": False,
                    "error": f"Error en el cobro: {charge_result.get('error')}"
                }
            
            # Crear la orden
            subtotal = sum(product.price for product in products)
            
            new_order = Order(
                user_id=user.user_id,
                address_id=default_address.address_id,
                payment_id=payment_method.payment_id,
                subscription_id=subscription.subscription_id,
                is_subscription=True,
                order_status=OrderStatus.PAID,
                subtotal=subtotal,
                discount_amount=Decimal("0.00"),
                shipping_cost=Decimal("0.00"),  # Envío gratis en suscripciones
                total_amount=subscription.price,
                points_earned=int(subscription.price / 5)  # 1 punto por cada $5
            )
            
            db.add(new_order)
            db.flush()
            
            # Crear order items
            for product in products:
                order_item = OrderItem(
                    order_id=new_order.order_id,
                    product_id=product.product_id,
                    quantity=1,
                    unit_price=product.price,
                    subtotal=product.price
                )
                db.add(order_item)
                
                # Reducir stock
                product.stock -= 1
            
            # Actualizar suscripción
            subscription.last_payment_date = date.today()
            subscription.failed_payment_attempts = 0  # Resetear intentos fallidos
            
            db.commit()
            db.refresh(new_order)
            
            return {
                "success": True,
                "order_id": new_order.order_id,
                "message": "Cobro procesado exitosamente"
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error procesando cobro: {str(e)}"}
    
    @staticmethod
    def process_due_subscriptions(db: Session) -> Dict:
        """
        Autor: Luis Flores y Lizbeth Barajas
        Descripción: CRON JOB - Procesa todas las suscripciones que tienen cobro pendiente hoy.
                     Esta función debe ejecutarse diariamente a medianoche para gestionar
                     los cobros automáticos y actualizar las fechas de próxima entrega.
        Parámetros:
            db (Session): Sesión de base de datos de SQLAlchemy.
        Retorna:
            Dict: Diccionario con success y results detallando total procesado,
                  exitosos, fallidos y lista de errores.
        """
        try:
            today = date.today()
            
            # Obtener suscripciones activas que tienen cobro hoy
            due_subscriptions = db.query(Subscription).filter(
                and_(
                    Subscription.subscription_status == SubscriptionStatus.ACTIVE,
                    Subscription.next_delivery_date <= today
                )
            ).all()
            
            results = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for subscription in due_subscriptions:
                user = subscription.user
                
                charge_result = SubscriptionService._process_subscription_charge(
                    db=db,
                    subscription=subscription,
                    user=user
                )
                
                results["total_processed"] += 1
                
                if charge_result.get("success"):
                    results["successful"] += 1
                    # Actualizar próxima fecha de entrega (+30 días)
                    subscription.next_delivery_date = today + timedelta(days=30)
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "subscription_id": subscription.subscription_id,
                        "user_id": subscription.user_id,
                        "error": charge_result.get("error")
                    })
            
            db.commit()
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Error procesando suscripciones: {str(e)}"
            }


subscription_service = SubscriptionService()