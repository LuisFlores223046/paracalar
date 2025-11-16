# Autor: Lizbeth Barajas
# Fecha: 14-11-2025
# Descripción: Servicio encargado de gestionar todo el flujo de procesamiento de pagos del sistema, manejo de tarjetas guardadas, 
#              creación de sesiones de pago, captura de pagos, y generación de órdenes asociadas
#              incluyendo cálculos de checkout, con integración con Stripe y PayPal

from sqlalchemy.orm import Session
from typing import Dict, Optional
from decimal import Decimal
from datetime import date
from app.models.user import User
from app.models.address import Address
from app.models.payment_method import PaymentMethod
from app.models.product import Product
from app.models.user_loyalty import UserLoyalty
from app.models.loyalty_tier import LoyaltyTier
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.coupon import Coupon
from app.models.user_coupon import UserCoupon
from app.models.enum import OrderStatus, PaymentType
import stripe
from app.services.stripe_service import stripe_service
from app.services.paypal_service import paypal_service
from app.api.v1.orders.service import order_service
from app.api.v1.loyalty.service import loyalty_service
from app.config import settings

class PaymentProcessService:
    
    def calculate_checkout_summary(
        self,
        db: Session,
        user_id: int,
        address_id: int,
        coupon_code: Optional[str] = None
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Calcula el resumen del checkout del carrito del usuario, incluyendo subtotal,
            envío, cupones, descuentos, total y puntos por ganar. Valida stock, dirección
            y reglas del programa de lealtad.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            user_id (int): ID del usuario dueño del carrito.
            address_id (int): ID de la dirección seleccionada para envío.
            coupon_code (str, opcional): Código de cupón a aplicar.

        Retorna:
            dict: Resultado del cálculo, incluyendo resumen y coupon_id si aplica.
        """
        try:
            cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).first()
            if not cart:
                return {"success": False, "error": "Carrito no encontrado"}
            
            cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
            if not cart_items:
                return {"success": False, "error": "El carrito está vacío"}
            
            # Valida direccion
            address = db.query(Address).filter(
                Address.address_id == address_id,
                Address.user_id == user_id
            ).first()
            if not address:
                return {"success": False, "error": "Dirección no encontrada"}
            
            # Calcula subtotal y checa stock
            subtotal = Decimal('0.00')
            for cart_item in cart_items:
                product = db.query(Product).filter(
                    Product.product_id == cart_item.product_id
                ).first()
                
                if not product or not product.is_active:
                    return {"success": False, "error": f"Producto no disponible"}
                
                if product.stock < cart_item.quantity:
                    return {"success": False, "error": f"Stock insuficiente para {product.name}"}
                
                subtotal += product.price * cart_item.quantity
            
            # Calculos de shipping (depende de loyalty tier)
            user_loyalty = db.query(UserLoyalty).filter(
                UserLoyalty.user_id == user_id
            ).first()
            
            shipping_cost = Decimal('150.00')  # Default shipping
            
            if user_loyalty:
                tier = db.query(LoyaltyTier).filter(
                    LoyaltyTier.tier_id == user_loyalty.tier_id
                ).first()
                
                if tier:
                    # Nivel 3: Envío gratis siempre (free_shipping_threshold = 0)
                    if tier.free_shipping_threshold == 0:
                        shipping_cost = Decimal('0.00')
                    # Nivel 2: Envío gratis si supera el threshold
                    elif tier.free_shipping_threshold > 0 and subtotal >= tier.free_shipping_threshold:
                        shipping_cost = Decimal('0.00')
                    # Nivel 1: Envío de $150 siempre
                    else:
                        shipping_cost = Decimal('150.00')
            
            # Calcula desceunto si hay cupon
            discount_amount = Decimal('0.00')
            coupon_id = None
            
            if coupon_code:
                # Verifica que el cupón exista y esté activo
                coupon = db.query(Coupon).filter(
                    Coupon.coupon_code == coupon_code,
                    Coupon.is_active == True
                ).first()
                
                if not coupon:
                    return {"success": False, "error": "Cupón no válido"}
                
                # Verifica que el cupón esté asignado al usuario
                user_coupon = db.query(UserCoupon).filter(
                    UserCoupon.user_id == user_id,
                    UserCoupon.coupon_id == coupon.coupon_id
                ).first()
                
                if not user_coupon:
                    return {"success": False, "error": "Este cupón no está asignado a tu cuenta"}
                
                # Verifica que el cupón no haya sido usado
                if user_coupon.used_date is not None:
                    return {"success": False, "error": "Este cupón ya ha sido utilizado"}
                
                # Valida fechas del cupón
                today = date.today()
                if coupon.expiration_date and coupon.expiration_date < today:
                    return {"success": False, "error": "El cupón ha expirado"}
              
                if coupon.start_date and coupon.start_date > today:
                    return {"success": False, "error": "El cupón aún no es válido"}
                
                # Calcula descuento (discount_value es porcentaje)
                discount_amount = subtotal * (coupon.discount_value / Decimal('100.00'))
                coupon_id = coupon.coupon_id
            
            # Total
            total_amount = subtotal + shipping_cost - discount_amount
            
            # Calculo de puntos
            points_to_earn = int(total_amount / 5)
            
            return {
                "success": True,
                "summary": {
                    "subtotal": float(subtotal),
                    "shipping_cost": float(shipping_cost),
                    "discount_amount": float(discount_amount),
                    "total_amount": float(total_amount),
                    "items_count": len(cart_items),
                    "points_to_earn": points_to_earn
                },
                "coupon_id": coupon_id
            }
        except Exception as e:
            return {"success": False, "error": f"Error al calcular resumen: {str(e)}"}
    
    async def create_stripe_checkout_session(
        self,
        db: Session,
        cognito_sub: str,
        address_id: int,
        payment_method_id: Optional[int] = None,
        coupon_code: Optional[str] = None,
        subscription_id: Optional[int] = None
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Crea una sesión de checkout en Stripe o procesa un pago usando una tarjeta guardada.
            Maneja metadatos y enlaces de retorno, así como cupones y suscripciones.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario en Cognito.
            address_id (int): Dirección utilizada para envío.
            payment_method_id (int, opcional): ID del método de pago guardado.
            coupon_code (str, opcional): Cupón aplicado en la compra.
            subscription_id (int, opcional): Identificador de suscripción.

        Retorna:
            dict: Resultado del proceso, incluyendo URL de Stripe o client secret.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Calcula checkout 
            summary_result = self.calculate_checkout_summary(
                db, user.user_id, address_id, coupon_code
            )
            if not summary_result.get("success"):
                return summary_result
            
            summary = summary_result["summary"]
            coupon_id = summary_result.get("coupon_id")
            total_amount = Decimal(str(summary["total_amount"]))
            
            # si es con pago guardado
            if payment_method_id:
                return await self._process_with_saved_card(
                    db=db,
                    user=user,
                    address_id=address_id,
                    payment_method_id=payment_method_id,
                    summary=summary,
                    coupon_id=coupon_id,
                    subscription_id=subscription_id
                )
            
            # si es con tarjeta nueva - nuevo checkout en stripe
            else:
                metadata = {
                    "user_id": str(user.user_id),
                    "cognito_sub": cognito_sub,
                    "address_id": str(address_id),
                }
                
                if coupon_code:
                    metadata["coupon_code"] = coupon_code
                
                if subscription_id:
                    metadata["subscription_id"] = str(subscription_id)
                
                stripe_session = stripe_service.create_checkout_session(
                    amount=int(total_amount * 100),
                    currency="mxn",
                    product_name="Compra BeFit",
                    success_url=f"{settings.APP_URL}/order-success?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{settings.APP_URL}/checkout",
                    metadata=metadata
                )
                
                if not stripe_session:
                    return {"success": False, "error": "Error al crear sesión de Stripe"}
                
                return {
                    "success": True,
                    "message": "Sesión de pago creada",
                    "stripe_session_id": stripe_session.get("id"),
                    "stripe_checkout_url": stripe_session.get("url"),
                    "total_amount": float(total_amount),
                    "points_earned": summary["points_to_earn"]
                }
                
        except Exception as e:
            return {"success": False, "error": f"Error en checkout: {str(e)}"}
    
    async def _process_with_saved_card(
        self,
        db: Session,
        user: User,
        address_id: int,
        payment_method_id: int,
        summary: dict,
        coupon_id: Optional[int],
        subscription_id: Optional[int]
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Procesa un pago directamente usando una tarjeta guardada del usuario en Stripe.
            Crea la orden inmediatamente si el pago es exitoso y asigna puntos de lealtad.

        Parámetros:
            db (Session): Sesión activa de base de datos.
            user (User): Instancia del usuario realizando la compra.
            address_id (int): Dirección seleccionada para envío.
            payment_method_id (int): ID del método de pago guardado.
            summary (dict): Resumen del checkout previamente calculado.
            coupon_id (int, opcional): ID del cupón aplicado.
            subscription_id (int, opcional): ID de la suscripción asociada.

        Retorna:
            dict: Resultado del proceso, incluyendo order_id y puntos generados.
        """
        try:
            saved_payment = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_method_id,
                PaymentMethod.user_id == user.user_id
            ).first()
            
            if not saved_payment:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            if not user.stripe_customer_id:
                return {"success": False, "error": "Usuario no tiene customer de Stripe"}
            
            # cargo a la tarjeta guardada
            total_amount = Decimal(str(summary["total_amount"]))
            
            payment_result = stripe_service.create_payment_intent_with_saved_card(
                amount=int(total_amount * 100),
                currency="mxn",
                customer_id=user.stripe_customer_id,
                payment_method_id=saved_payment.provider_ref,
                description=f"Orden BeFit - Usuario {user.user_id}",
                metadata={
                    "user_id": str(user.user_id),
                    "address_id": str(address_id)
                }
            )
            
            # Maneja casos donde se requiere autenticación adicional (3D Secure)
            if not payment_result.get('success'):
                if payment_result.get('requires_action'):
                    return {
                        "success": False,
                        "requires_action": True,
                        "client_secret": payment_result['client_secret'],
                        "error": "Requiere autenticación adicional"
                    }
                else:
                    return {
                        "success": False,
                        "error": payment_result.get('error', 'Error al procesar pago')
                    }
            
            order_result = order_service.create_order_from_cart(
                db=db,
                user_id=user.user_id,
                address_id=address_id,
                payment_id=saved_payment.payment_id,
                subtotal=Decimal(str(summary["subtotal"])),
                shipping_cost=Decimal(str(summary["shipping_cost"])),
                discount_amount=Decimal(str(summary["discount_amount"])),
                total_amount=total_amount,
                order_status=OrderStatus.PAID,
                coupon_id=coupon_id,
                subscription_id=subscription_id
            )
            
            if not order_result.get("success"):
                db.rollback()
                return order_result
            
            order = order_result["order"]
            points_earned = order_result["points_earned"]
            
            # Logica de puntos - loyalty program
            if points_earned > 0:
                user_loyalty = db.query(UserLoyalty).filter(
                    UserLoyalty.user_id == user.user_id
                ).first()
                
                if user_loyalty:
                    loyalty_service.add_points(
                        db=db,
                        loyalty_id=user_loyalty.loyalty_id,
                        points=points_earned,
                        order_id=order.order_id
                    )
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "message": "Pago procesado exitosamente",
                "order_id": order.order_id,
                "total_amount": float(total_amount),
                "points_earned": points_earned,
                "payment_intent_id": payment_result['payment_intent_id']
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al procesar pago: {str(e)}"}
    
    async def process_stripe_webhook(
        self,
        db: Session,
        session_id: str,
        payment_intent_id: str
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Maneja el webhook posterior a un pago exitoso de Stripe. Recupera la sesión,
            crea la orden correspondiente, guarda el método de pago y asigna puntos de
            lealtad si corresponde.

        Parámetros:
            db (Session): Sesión de base de datos.
            session_id (str): ID de la sesión de checkout en Stripe.
            payment_intent_id (str): ID del intent de pago asociado.

        Retorna:
            dict: Resultado del proceso con información de la orden generada.
        """
        try:
            session = stripe_service.retrieve_session(session_id)
            if not session:
                return {"success": False, "error": "Sesión no encontrada"}
            
            # Extrae metadata
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")
            address_id = metadata.get("address_id")
            coupon_code = metadata.get("coupon_code")
            subscription_id = metadata.get("subscription_id")
            
            if not user_id or not address_id:
                return {"success": False, "error": "Metadata incompleto en sesión"}
            
            user_id = int(user_id)
            address_id = int(address_id)
            subscription_id = int(subscription_id) if subscription_id else None
            
            # Calcula resumen otra vez para obtener info necesaria
            summary_result = self.calculate_checkout_summary(
                db, user_id, address_id, coupon_code
            )
            if not summary_result.get("success"):
                return summary_result
            
            summary = summary_result["summary"]
            coupon_id = summary_result.get("coupon_id")
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            payment_method_id = payment_intent.payment_method

            pm_data = stripe_service.get_payment_method(payment_method_id)

            if not pm_data["success"]:
                return {"success": False, "error": "No se pudo obtener sesión de Stripe durante webhook"}

            card = pm_data["payment_method"]["card"]

            last_four = card["last4"]
            exp_month = card["exp_month"]
            exp_year = card["exp_year"]

            # Verificar si ya existe un PaymentMethod
            existing_payment = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user_id,
                PaymentMethod.provider_ref == payment_method_id
            ).first()

            if existing_payment:
                payment_method_record = existing_payment
            else:
                funding_type = card.get('funding', 'credit')
                payment_type = (
                    PaymentType.DEBIT_CARD if funding_type == 'debit' 
                    else PaymentType.CREDIT_CARD
                )
                
                payment_method_record = PaymentMethod(
                    user_id=user_id,
                    payment_type=payment_type,
                    provider_ref=payment_method_id,
                    last_four=last_four,
                    expiration_date=f"{exp_month:02d}/{str(exp_year)[2:]}", # MM/YY
                    is_default=False
                )
                db.add(payment_method_record)
                db.flush()
            
            order_result = order_service.create_order_from_cart(
                db=db,
                user_id=user_id,
                address_id=address_id,
                payment_id=payment_method_record.payment_id,
                subtotal=Decimal(str(summary["subtotal"])),
                shipping_cost=Decimal(str(summary["shipping_cost"])),
                discount_amount=Decimal(str(summary["discount_amount"])),
                total_amount=Decimal(str(summary["total_amount"])),
                order_status=OrderStatus.PAID,
                coupon_id=coupon_id,
                subscription_id=subscription_id
            )
            
            if not order_result.get("success"):
                db.rollback()
                return order_result
            
            order = order_result["order"]
            points_earned = order_result["points_earned"]
            
            # Logica de puntos - loyalty program
            if points_earned > 0:
                user_loyalty = db.query(UserLoyalty).filter(
                    UserLoyalty.user_id == user_id
                ).first()
                
                if user_loyalty:
                    loyalty_result = loyalty_service.add_points(
                        db=db,
                        loyalty_id=user_loyalty.loyalty_id,
                        points=points_earned,
                        order_id=order.order_id
                    )
                    
                    if not loyalty_result.get("success"):
                        print(f"Error al agregar puntos: {loyalty_result.get('error')}")
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "message": "Pago procesado exitosamente",
                "order_id": order.order_id,
                "total_amount": float(summary["total_amount"]),
                "points_earned": points_earned
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error en webhook Stripe: {str(e)}"}
    
    async def initialize_paypal_checkout(
        self,
        db: Session,
        cognito_sub: str,
        address_id: int,
        coupon_code: Optional[str] = None
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Inicializa el proceso de pago con PayPal creando la orden y obteniendo la
            URL de aprobación que el usuario debe visitar para autorizar el pago.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario en Cognito.
            address_id (int): Dirección seleccionada para envío.
            coupon_code (str, opcional): Cupón aplicado al total.

        Retorna:
            dict: URL de aprobación de PayPal y datos del resumen.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == user.user_id).first()
            if not cart:
                return {"success": False, "error": "Carrito no encontrado"}
            
            cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
            if not cart_items:
                return {"success": False, "error": "El carrito está vacío"}
            
            # Calcula resumen
            summary_result = self.calculate_checkout_summary(
                db, user.user_id, address_id, coupon_code
            )
            if not summary_result.get("success"):
                return summary_result
            
            summary = summary_result["summary"]
            total_amount = Decimal(str(summary["total_amount"]))
            
            # Crea orden en paypal
            paypal_response = await paypal_service.create_order(
                amount=float(total_amount),
                currency="MXN"
            )
            
            # Extrae URL de aprobacion
            approval_url = None
            for link in paypal_response.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            if not approval_url:
                return {"success": False, "error": "No se pudo obtener URL de aprobación de PayPal"}
            
            return {
                "success": True,
                "message": "Checkout PayPal iniciado",
                "paypal_order_id": paypal_response.get("id"),
                "paypal_approval_url": approval_url,
                "total_amount": float(total_amount),
                "points_earned": summary["points_to_earn"]
            }
        except Exception as e:
            return {"success": False, "error": f"Error al inicializar PayPal: {str(e)}"}
    
    async def capture_paypal_payment(
        self,
        db: Session,
        cognito_sub: str,
        paypal_order_id: str,
        address_id: int,
        coupon_code: Optional[str] = None,
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Captura un pago autorizado en PayPal, genera la orden correspondiente,
            registra el método de pago y asigna puntos al usuario si corresponde.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario en Cognito.
            paypal_order_id (str): ID de la orden de PayPal aprobada.
            address_id (int): Dirección utilizada para envío.
            coupon_code (str, opcional): Cupón aplicado.

        Retorna:
            dict: Resultado del proceso, incluyendo ID de orden y puntos generados.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Captura pago
            capture_response = await paypal_service.capture_order(paypal_order_id)
            
            # Verifica estatus
            if capture_response.get("status") != "COMPLETED":
                return {"success": False, "error": "El pago de PayPal no se completó"}
            
            # Resumen
            summary_result = self.calculate_checkout_summary(
                db, user.user_id, address_id, coupon_code
            )
            if not summary_result.get("success"):
                return summary_result
            
            summary = summary_result["summary"]
            coupon_id = summary_result.get("coupon_id")
            
            # Crea registro
            paypal_payment = PaymentMethod(
                user_id=user.user_id,
                payment_type=PaymentType.PAYPAL,
                provider_ref=paypal_order_id,
                is_default=False
            )
            db.add(paypal_payment)
            db.flush()
            
            order_result = order_service.create_order_from_cart(
                db=db,
                user_id=user.user_id,
                address_id=address_id,
                payment_id=paypal_payment.payment_id,
                subtotal=Decimal(str(summary["subtotal"])),
                shipping_cost=Decimal(str(summary["shipping_cost"])),
                discount_amount=Decimal(str(summary["discount_amount"])),
                total_amount=Decimal(str(summary["total_amount"])),
                order_status=OrderStatus.PAID,
                coupon_id=coupon_id,
                subscription_id=None
            )
            
            if not order_result.get("success"):
                db.rollback()
                return order_result
            
            order = order_result["order"]
            points_earned = order_result["points_earned"]
            
            # Logica de puntos - loyalty program
            if points_earned > 0:
                user_loyalty = db.query(UserLoyalty).filter(
                    UserLoyalty.user_id == user.user_id
                ).first()
                
                if user_loyalty:
                    loyalty_result = loyalty_service.add_points(
                        db=db,
                        loyalty_id=user_loyalty.loyalty_id,
                        points=points_earned,
                        order_id=order.order_id
                    )
                    
                    if not loyalty_result.get("success"):
                        print(f"Error al agregar puntos: {loyalty_result.get('error')}")
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "message": "Pago PayPal procesado exitosamente",
                "order_id": order.order_id,
                "total_amount": float(summary["total_amount"]),
                "points_earned": points_earned
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al capturar pago PayPal: {str(e)}"}

payment_process_service = PaymentProcessService()
