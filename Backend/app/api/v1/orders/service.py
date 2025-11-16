# Autor: Lizbeth Barajas
# Fecha: 14-11-25
# Descripcion: Servicio encargado de gestionar las ordenes, desde su creación 
#              (que se llama en checkout), hasta las operaciones CRUD

from sqlalchemy.orm import Session
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, UTC
from app.models.user import User
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.address import Address
from app.models.product import Product
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.user_coupon import UserCoupon
from app.models.enum import OrderStatus
from app.api.v1.shipping.service import shipping_service

class OrderService:
    
    def create_order_from_cart(
        self,
        db: Session,
        user_id: int,
        address_id: int,
        payment_id: int,
        subtotal: Decimal,
        shipping_cost: Decimal,
        discount_amount: Decimal,
        total_amount: Decimal,
        order_status: OrderStatus = OrderStatus.PENDING,
        coupon_id: Optional[int] = None,
        subscription_id: Optional[int] = None
    ) -> Dict:
        """
        Autor: Lizbteh Barajas

        Descripción:
            Crea una orden a partir del carrito del usuario. Esta función es utilizada
            tanto por el flujo de pago con Stripe como por el flujo de PayPal.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            user_id (int): ID del usuario que realiza la compra.
            address_id (int): ID de la dirección seleccionada para el envío.
            payment_id (int): ID del método de pago utilizado.
            subtotal (Decimal): Monto subtotal antes de descuentos.
            shipping_cost (Decimal): Costo total del envío.
            discount_amount (Decimal): Monto de descuento aplicado.
            total_amount (Decimal): Total final a pagar después de descuentos.
            order_status (OrderStatus): Estado inicial de la orden (por defecto: PENDING).
            coupon_id (Optional[int]): ID del cupón utilizado, si aplica.
            subscription_id (Optional[int]): ID de suscripción si la compra corresponde a una.

        Retorna:
            Dict: Resultado con estado de éxito, la orden creada y los puntos generados.
        """
        try:
            cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).first()
            if not cart:
                return {"success": False, "error": "Carrito no encontrado"}
            
            cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
            if not cart_items:
                return {"success": False, "error": "El carrito está vacío"}
            
            # Valida productos y stock
            for cart_item in cart_items:
                product = db.query(Product).filter(
                    Product.product_id == cart_item.product_id
                ).first()
                
                if not product or not product.is_active:
                    return {"success": False, "error": f"Producto no disponible"}
                
                if product.stock < cart_item.quantity:
                    return {"success": False, "error": f"Stock insuficiente para {product.name}"}
            
            is_subscription = subscription_id is not None
            
            # Calcula puntos
            points_earned = int(total_amount / 5)
            
            # Genera tracking number
            tracking_number = shipping_service.generate_tracking_number()
            
            # Crea orden
            order = Order(
                user_id=user_id,
                address_id=address_id,
                payment_id=payment_id,
                coupon_id=coupon_id,
                subscription_id=subscription_id,
                is_subscription=is_subscription,
                order_date=datetime.now(UTC),
                order_status=order_status,
                tracking_number=tracking_number,
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                points_earned=points_earned
            )
            db.add(order)
            db.flush()
            
            # Crea order_items y actualiza stock
            for cart_item in cart_items:
                product = db.query(Product).filter(
                    Product.product_id == cart_item.product_id
                ).first()
                
                item_subtotal = product.price * cart_item.quantity
                
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    subtotal=item_subtotal
                )
                db.add(order_item)

                # Actualiza stock
                product.stock -= cart_item.quantity
            
            # Limpia carrito
            db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()
            
            if coupon_id:
                user_coupon = db.query(UserCoupon).filter(
                    UserCoupon.user_id == user_id,
                    UserCoupon.coupon_id == coupon_id,
                    UserCoupon.used_date.is_(None)  # Solo cupones no usados
                ).first()
                
                if user_coupon:
                    user_coupon.used_date = datetime.now(UTC).date()
                    user_coupon.order_id = order.order_id
            
            db.flush()
            
            return {
                "success": True,
                "order": order,
                "points_earned": points_earned
            }
        except Exception as e:
            return {"success": False, "error": f"Error al crear orden: {str(e)}"}
    
    def get_user_orders(
        self,
        db: Session,
        cognito_sub: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene todos los pedidos asociados a un usuario mediante su cognito_sub.
            Permite paginación y devuelve los pedidos más recientes primero.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.
            limit (int): Número máximo de órdenes a obtener.
            offset (int): Cantidad de órdenes a omitir para paginación.

        Retorna:
            Dict: Objeto con estado de éxito, lista de órdenes y total encontrado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Obtiene ordenes (mas reciente primero)
            orders = db.query(Order).filter(
                Order.user_id == user.user_id
            ).order_by(Order.order_date.desc()).limit(limit).offset(offset).all()
            
            return {
                "success": True,
                "orders": orders,
                "total": len(orders)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener pedidos: {str(e)}"}
    
    def get_order_by_id(self, db: Session, cognito_sub: str, order_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene los detalles completos de un pedido, incluyendo sus productos,
            precios, subtotales y dirección de envío asociada. Solo permite consultar
            órdenes pertenecientes al usuario autenticado.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.
            order_id (int): ID del pedido a consultar.

        Retorna:
            Dict: Información detallada del pedido e items, o mensaje de error.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            order = db.query(Order).filter(
                Order.order_id == order_id,
                Order.user_id == user.user_id
            ).first()
            
            if not order:
                return {"success": False, "error": "Pedido no encontrado"}
            
            # Obtiene ordenes con todos los items
            order_items = db.query(OrderItem).filter(
                OrderItem.order_id == order_id
            ).all()
            
            items_with_details = []
            for item in order_items:
                product = db.query(Product).filter(
                    Product.product_id == item.product_id
                ).first()
                
                items_with_details.append({
                    "order_item_id": item.order_item_id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else "Producto no disponible",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal)
                })
            
            # Obtiene direccion
            address = db.query(Address).filter(
                Address.address_id == order.address_id
            ).first()
            
            shipping_address = {
                "recipient_name": address.recipient_name,
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
                "country": address.country,
                "phone_number": address.phone_number
            }
            
            return {
                "success": True,
                "order": {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "is_subscription": order.is_subscription,
                    "order_date": order.order_date,
                    "order_status": order.order_status.value,
                    "tracking_number": order.tracking_number,
                    "subtotal": float(order.subtotal),
                    "discount_amount": float(order.discount_amount),
                    "shipping_cost": float(order.shipping_cost),
                    "total_amount": float(order.total_amount),
                    "points_earned": order.points_earned,
                    "shipping_address": shipping_address,
                    "items": items_with_details
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener pedido: {str(e)}"}
    
    def get_subscription_orders(self, db: Session, cognito_sub: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene únicamente los pedidos que corresponden a suscripciones del usuario.
            Filtra por órdenes marcadas como suscripción y las devuelve en orden cronológico
            descendente.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.

        Retorna:
            Dict: Lista de órdenes de suscripción y el total encontrado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Solo ordenes de suscripcion
            orders = db.query(Order).filter(
                Order.user_id == user.user_id,
                Order.is_subscription == True
            ).order_by(Order.order_date.desc()).all()
            
            return {
                "success": True,
                "orders": orders,
                "total": len(orders)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener pedidos de suscripción: {str(e)}"}
    
    def cancel_order(
        self,
        db: Session,
        cognito_sub: str,
        order_id: int
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Cancela un pedido siempre que este no haya sido enviado o entregado. Restaura
            el inventario de los productos asociados y actualiza el estado del pedido.
            En versiones futuras, se integrará la lógica de reembolsos con Stripe/PayPal.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.
            order_id (int): ID del pedido a cancelar.

        Retorna:
            Dict: Resultado de la cancelación y el pedido actualizado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            order = db.query(Order).filter(
                Order.order_id == order_id,
                Order.user_id == user.user_id
            ).first()
            
            if not order:
                return {"success": False, "error": "Pedido no encontrado"}
            
            # solo se puede cancelar antes de que sea enviado
            if order.order_status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
                return {
                    "success": False,
                    "error": f"No se puede cancelar un pedido con estado {order.order_status.value}"
                }
            
            # Restaura inventario
            order_items = db.query(OrderItem).filter(
                OrderItem.order_id == order_id
            ).all()

            for item in order_items:
                product = db.query(Product).filter(
                    Product.product_id == item.product_id
                ).first()
                if product:
                    product.stock += item.quantity
            
            # Estatus update
            order.order_status = OrderStatus.CANCELLED
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "message": "Pedido cancelado exitosamente",
                "order": order
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al cancelar pedido: {str(e)}"}
    
    def update_order_status(
        self,
        db: Session,
        order_id: int,
        new_status: OrderStatus,
        tracking_number: Optional[str] = None
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Actualiza el estado de un pedido. Utilizado tanto internamente por el sistema
            como por webhooks provenientes de procesadores de pago o sistemas externos.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            order_id (int): ID del pedido a actualizar.
            new_status (OrderStatus): Nuevo estado que se desea asignar.
            tracking_number (Optional[str]): Número de rastreo en caso de que aplique.

        Retorna:
            Dict: Resultado de la operación y el pedido actualizado.
        """
        try:
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return {"success": False, "error": "Pedido no encontrado"}
            
            order.order_status = new_status
            
            if tracking_number:
                order.tracking_number = tracking_number
            
            db.commit()
            db.refresh(order)
            
            return {
                "success": True,
                "order": order
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al actualizar estado: {str(e)}"}
    
    def get_order_status(self, db: Session, cognito_sub: str, order_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene únicamente información resumida del estado actual de un pedido
            perteneciente al usuario autenticado. Incluye número de rastreo y fecha.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.
            order_id (int): ID del pedido a consultar.

        Retorna:
            Dict: Estado actual del pedido, tracking y fecha de creación.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            order = db.query(Order).filter(
                Order.order_id == order_id,
                Order.user_id == user.user_id
            ).first()
            
            if not order:
                return {"success": False, "error": "Pedido no encontrado"}
            
            return {
                "success": True,
                "order_id": order.order_id,
                "order_status": order.order_status.value,
                "tracking_number": order.tracking_number,
                "order_date": order.order_date
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener estado del pedido: {str(e)}"}

order_service = OrderService()