from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.api.v1.cart import schemas


class CartService:
    """Servicio para gestión del carrito de compras"""
    
    @staticmethod
    def get_or_create_cart(db: Session, user_id: int) -> ShoppingCart:
        """
        Obtiene el carrito del usuario o lo crea si no existe
        """
        cart = db.query(ShoppingCart).options(
            joinedload(ShoppingCart.cart_items).joinedload(CartItem.product)  # ✅ Usar cart_items
        ).filter(ShoppingCart.user_id == user_id).first()
        
        if not cart:
            cart = ShoppingCart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        return cart
    
    @staticmethod
    def get_cart(db: Session, user_id: int) -> ShoppingCart:
        """
        Obtiene el carrito completo del usuario con todos los items
        """
        cart = db.query(ShoppingCart).options(
            joinedload(ShoppingCart.cart_items).joinedload(CartItem.product).joinedload(Product.product_images)  # ✅ Usar cart_items y product_images
        ).filter(ShoppingCart.user_id == user_id).first()
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrito no encontrado"
            )
        
        return cart
    
    @staticmethod
    def add_item_to_cart(
        db: Session,
        user_id: int,
        item_data: schemas.CartItemAdd
    ) -> CartItem:
        """
        Agrega un producto al carrito o actualiza la cantidad si ya existe
        """
        # Obtener o crear carrito
        cart = CartService.get_or_create_cart(db, user_id)
        
        # Verificar que el producto existe y está activo
        product = db.query(Product).filter(
            and_(
                Product.product_id == item_data.product_id,
                Product.is_active == True
            )
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado o no disponible"
            )
        
        # Verificar stock disponible
        if product.stock < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {product.stock}"
            )
        
        # Verificar si el item ya existe en el carrito
        existing_item = db.query(CartItem).filter(
            and_(
                CartItem.cart_id == cart.cart_id,
                CartItem.product_id == item_data.product_id
            )
        ).first()
        
        if existing_item:
            # Actualizar cantidad
            new_quantity = existing_item.quantity + item_data.quantity
            
            if product.stock < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente. Disponible: {product.stock}, en carrito: {existing_item.quantity}"
                )
            
            existing_item.quantity = new_quantity
            db.commit()
            db.refresh(existing_item)
            
            return existing_item
        else:
            # Crear nuevo item
            cart_item = CartItem(
                cart_id=cart.cart_id,
                product_id=item_data.product_id,
                quantity=item_data.quantity
            )
            
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)
            
            return cart_item
    
    @staticmethod
    def update_cart_item(
        db: Session,
        user_id: int,
        cart_item_id: int,  # ✅ Nombre correcto
        update_data: schemas.CartItemUpdate
    ) -> CartItem:
        """
        Actualiza la cantidad de un item en el carrito
        """
        # Obtener el item y verificar que pertenece al usuario
        cart_item = db.query(CartItem).join(ShoppingCart).filter(
            and_(
                CartItem.cart_item_id == cart_item_id,  # ✅ Usar cart_item_id
                ShoppingCart.user_id == user_id
            )
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item no encontrado en el carrito"
            )
        
        # Verificar stock disponible
        product = db.query(Product).filter(
            Product.product_id == cart_item.product_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        if product.stock < update_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {product.stock}"
            )
        
        # Actualizar cantidad
        cart_item.quantity = update_data.quantity
        db.commit()
        db.refresh(cart_item)
        
        return cart_item
    
    @staticmethod
    def remove_item_from_cart(
        db: Session,
        user_id: int,
        cart_item_id: int  # ✅ Nombre correcto
    ) -> bool:
        """
        Elimina un item del carrito
        """
        cart_item = db.query(CartItem).join(ShoppingCart).filter(
            and_(
                CartItem.cart_item_id == cart_item_id,  # ✅ Usar cart_item_id
                ShoppingCart.user_id == user_id
            )
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item no encontrado en el carrito"
            )
        
        db.delete(cart_item)
        db.commit()
        
        return True
    
    @staticmethod
    def clear_cart(db: Session, user_id: int) -> bool:
        """
        Vacía completamente el carrito del usuario
        """
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.user_id == user_id
        ).first()
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrito no encontrado"
            )
        
        # Eliminar todos los items
        db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()
        db.commit()
        
        return True
    
    @staticmethod
    def get_cart_summary(db: Session, user_id: int) -> dict:
        """
        Obtiene un resumen rápido del carrito (total items y precio)
        """
        cart = CartService.get_cart(db, user_id)
        
        total_items = sum(item.quantity for item in cart.cart_items)  # ✅ Usar cart_items
        total_price = sum(item.quantity * item.product.price for item in cart.cart_items)
        
        return {
            "total_items": total_items,
            "total_price": round(total_price, 2)
        }
    
    @staticmethod
    def validate_cart_stock(db: Session, user_id: int) -> dict:
        """
        Valida que todos los productos en el carrito tengan stock suficiente.
        Retorna información sobre productos sin stock o con stock insuficiente.
        """
        cart = CartService.get_cart(db, user_id)
        
        issues = []
        
        for item in cart.cart_items:  # ✅ Usar cart_items
            product = item.product
            
            if not product.is_active:
                issues.append({
                    "cart_item_id": item.cart_item_id,  # ✅ Usar cart_item_id
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "issue": "Producto no disponible",
                    "requested": item.quantity,
                    "available": 0
                })
            elif product.stock < item.quantity:
                issues.append({
                    "cart_item_id": item.cart_item_id,  # ✅ Usar cart_item_id
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "issue": "Stock insuficiente",
                    "requested": item.quantity,
                    "available": product.stock
                })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
