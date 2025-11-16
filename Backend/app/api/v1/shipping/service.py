# Autor: Gabriel Vilchis
# Fecha: 12/11/2025
# Descripción: Este servicio contiene la lógica de negocio para la gestión de pedidos
# (shipping). Incluye métodos para crear nuevas órdenes, validar el stock de productos,
# calcular los totales de la orden, generar números de rastreo simulados, y obtener
# los detalles de rastreo de un pedido existente.
import random, string
from typing import Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.api.v1.shipping.schemas import CreateOrder, OrderTrackingResponse
from app.models.order import Order as OrderModel
from app.models.order_item import OrderItem as OrderItemModel
from app.models.product import Product as ProductModel
from app.models.enum import OrderStatus
from app.models.cart_item import CartItem as CartItemModel
from app.models.shopping_cart import ShoppingCart as ShoppingCartModel

class ShippingService:
    """
    Autor; Gabriel Vilchis
    Clase de servicio que encapsula la lógica de negocio para la creación y gestión
    de pedidos (órdenes de compra).
    """
    def create_order_db(db: Session, order_in: CreateOrder) -> OrderModel:
        # Genero un numero de rastreo de pedido simulado
        tracking_number = ShippingService.generate_tracking_number()
        total_subtotal = Decimal("0.0")
        order_item_models = [] # lista para guardar los items del carrito
        # obtiene el carrito del usuario
        cart = db.query(ShoppingCartModel).filter(ShoppingCartModel.user_id == order_in.user_id).first()

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene un carrito"
            )
    
        cart_items = db.query(CartItemModel).filter(
            CartItemModel.cart_id == cart.cart_id
        ).all()

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El carrito está vacío"
            )
        
        for cart_item in cart_items:
            product = cart_item.product

            # verifica el stock de los productos
            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para el producto: {product.name} | Solcitados: {cart_item.quantity} | Disponibles: {product.stock}"
                )
            
            # calcula el subtotal del item
            item_subtotal = product.price * cart_item.quantity
            total_subtotal += item_subtotal

            new_order_item = OrderItemModel(
                product=product,
                quantity=cart_item.quantity,
                unit_price=product.price, # usa el precio del producto en la bd
                subtotal=item_subtotal
            )
            order_item_models.append(new_order_item)
            # Reduce el stock del producto comprado
            product.stock -= cart_item.quantity 

            # En esta parte, faltaria la logica de los cupones y del coste del envio
            # shiiping_cost =
            # discount_amount =
            # total_amount = total_subtotal + shipping_cost - dicount-amount
        
        new_order = OrderModel(
            user_id=order_in.user_id,
            address_id=order_in.address_id,
            payment_id=order_in.payment_id,
            order_date=date.today(),
            order_status=OrderStatus.PENDING, # estado inicial del ENUM
            subtotal=total_subtotal,
            shipping_cost=10, # valores provisional
            discount_amount=10, # valor provisional
            total_amount=10, # valor provisional
            tracking_number=tracking_number
        )
            
        new_order.order_items = order_item_models

        try:
            db.add(new_order)
            for cart_item in cart_items:
                db.delete(cart_item)
            db.commit()
            db.refresh(new_order) # Obtiene new_order.order_id
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No se pudo crear el pedido: {e}"
            )
        print(f"Pedido: {new_order.order_id} creado en la BD")

        return new_order
    
    @staticmethod
    def generate_tracking_number():
        """
        Autor: Gabriel Vilchis
        Método utilitario para generar un número de rastreo de pedido simulado.

        Returns:
            str: Una cadena alfanumérica única (Ej: AB1234567890).
        """
        letters = "".join(random.choices(string.ascii_uppercase, k=2))
        numbers = "".join(random.choices(string.digits, k=10))
        return f"{letters}{numbers}"
    
    def get_details(db: Session, pedido_id: int) -> Optional[OrderTrackingResponse]:
        """
        Autor: Gabriel Vilchis
        Obtiene los detalles clave para el rastreo de un pedido específico.

        Realiza consultas a la base de datos para obtener el estado del pedido,
        el número de rastreo y una lista de los nombres de los productos incluidos.

        Args:
            db (Session): Sesión de SQLAlchemy.
            pedido_id (int): El ID único del pedido a consultar.

        Returns:
            Optional[OrderTrackingResponse]: Los detalles de rastreo si el pedido existe, o `None` si no se encuentra.
        """
        order = db.query(OrderModel).filter(OrderModel.order_id == pedido_id).first()

        if not order:
            return None
        
        product_names_qry = db.query(ProductModel.name). \
            join(OrderItemModel, ProductModel.product_id == OrderItemModel.product_id). \
            filter(OrderItemModel.order_id == pedido_id)
        
        product_names = [name for (name,) in product_names_qry.all()]

        
        return OrderTrackingResponse(
            order_id=order.order_id,
            tracking_number=order.tracking_number,
            total_amount=float(order.total_amount),
            order_status=order.order_status.value, # valor str del enum de status
            product_names=product_names
        )
    
shipping_service = ShippingService()