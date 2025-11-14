# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Rutas API para gestión del carrito de compras. Incluye endpoints
#              para obtener, agregar, actualizar, eliminar items del carrito y 
#              validar stock disponible.

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.api.v1.cart import schemas
from app.api.v1.cart.service import CartService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=schemas.ShoppingCartResponse)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Obtiene el carrito completo del usuario autenticado con todos
                 sus items, información de productos y totales calculados.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos.
    Retorna:
        ShoppingCartResponse: Carrito con lista de items, total de items y precio total.
    """
    cart = CartService.get_cart(db, current_user.user_id)
    
    # Preparar respuesta con cálculos
    items_response = []
    total_items = 0
    total_price = 0.0
    
    for item in cart.cart_items:
        # Obtener imagen principal del producto
        primary_image = None
        if item.product.product_images:
            primary = next((img for img in item.product.product_images if img.is_primary), None)
            primary_image = primary.image_path if primary else item.product.product_images[0].image_path
        
        # Crear info del producto
        product_info = schemas.CartItemProductInfo(
            product_id=item.product.product_id,
            name=item.product.name,
            price=item.product.price,
            stock=item.product.stock,
            image_path=primary_image,
            brand=item.product.brand
        )
        
        # Calcular subtotal
        subtotal = item.quantity * item.product.price
        
        # Crear respuesta del item
        item_response = schemas.CartItemResponse(
            cart_item_id=item.cart_item_id,
            cart_id=item.cart_id,
            product_id=item.product_id,
            quantity=item.quantity,
            added_at=item.added_at,
            updated_at=item.updated_at,
            product=product_info,
            subtotal=round(subtotal, 2)
        )
        
        items_response.append(item_response)
        subtotal = item.quantity * item.product.price
        total_price += float(subtotal)
    
    return schemas.ShoppingCartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        items=items_response,
        total_items=total_items,
        total_price=round(total_price, 2),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.get("/summary", response_model=schemas.CartSummary)
def get_cart_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Obtiene un resumen rápido del carrito con total de items y precio.
                 Útil para mostrar en el badge del icono del carrito.
    Parámetros:
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        CartSummary: Total de items y precio total.
    """
    summary = CartService.get_cart_summary(db, current_user.user_id)
    return summary


@router.post("/add", response_model=schemas.CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    item_data: schemas.CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Agrega un producto al carrito del usuario. Si el producto ya existe,
                 incrementa la cantidad. Verifica stock disponible antes de agregar.
    Parámetros:
        item_data (CartItemAdd): Datos del item a agregar (product_id y quantity).
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        CartItemResponse: Item del carrito creado o actualizado con información del producto.
    """
    cart_item = CartService.add_item_to_cart(
        db=db,
        user_id=current_user.user_id,
        item_data=item_data
    )
    
    # Recargar con relaciones para la respuesta
    db.refresh(cart_item)
    
    # Preparar respuesta
    primary_image = None
    if cart_item.product.product_images:
        primary = next((img for img in cart_item.product.product_images if img.is_primary), None)
        primary_image = primary.image_path if primary else cart_item.product.product_images[0].image_path
    
    product_info = schemas.CartItemProductInfo(
        product_id=cart_item.product.product_id,
        name=cart_item.product.name,
        price=cart_item.product.price,
        stock=cart_item.product.stock,
        image_path=primary_image,
        brand=cart_item.product.brand
    )
    
    subtotal = cart_item.quantity * cart_item.product.price
    
    return schemas.CartItemResponse(
        cart_item_id=cart_item.cart_item_id,
        cart_id=cart_item.cart_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        added_at=cart_item.added_at,
        updated_at=cart_item.updated_at,
        product=product_info,
        subtotal=round(subtotal, 2)
    )


@router.put("/{cart_item_id}", response_model=schemas.CartItemResponse)
def update_cart_item(
    cart_item_id: int,
    update_data: schemas.CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Actualiza la cantidad de un item específico en el carrito.
                 Verifica que haya stock suficiente antes de actualizar.
    Parámetros:
        cart_item_id (int): ID del item del carrito a actualizar.
        update_data (CartItemUpdate): Nueva cantidad del item.
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        CartItemResponse: Item del carrito actualizado con información del producto.
    """
    cart_item = CartService.update_cart_item(
        db=db,
        user_id=current_user.user_id,
        cart_item_id=cart_item_id,
        update_data=update_data
    )
    
    # Recargar con relaciones
    db.refresh(cart_item)
    
    # Preparar respuesta
    primary_image = None
    if cart_item.product.product_images:
        primary = next((img for img in cart_item.product.product_images if img.is_primary), None)
        primary_image = primary.image_path if primary else cart_item.product.product_images[0].image_path
    
    product_info = schemas.CartItemProductInfo(
        product_id=cart_item.product.product_id,
        name=cart_item.product.name,
        price=cart_item.product.price,
        stock=cart_item.product.stock,
        image_path=primary_image,
        brand=cart_item.product.brand
    )
    
    subtotal = cart_item.quantity * cart_item.product.price
    
    return schemas.CartItemResponse(
        cart_item_id=cart_item.cart_item_id,
        cart_id=cart_item.cart_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        added_at=cart_item.added_at,
        updated_at=cart_item.updated_at,
        product=product_info,
        subtotal=round(subtotal, 2)
    )


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Elimina un item específico del carrito del usuario.
    Parámetros:
        cart_item_id (int): ID del item del carrito a eliminar.
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        None: Respuesta 204 No Content si la eliminación fue exitosa.
    """
    CartService.remove_item_from_cart(
        db=db,
        user_id=current_user.user_id,
        cart_item_id=cart_item_id
    )
    return None


@router.delete("/actions/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Vacía completamente el carrito del usuario, eliminando todos los items.
                 Útil después de confirmar un pago o cuando el usuario quiere empezar de nuevo.
    Parámetros:
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        None: Respuesta 204 No Content si la limpieza fue exitosa.
    """
    CartService.clear_cart(db, current_user.user_id)
    return None


@router.get("/validate")
def validate_cart_stock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Valida que todos los productos en el carrito tengan stock suficiente.
                 Útil para llamar antes de proceder al checkout.
    Parámetros:
        current_user (User): Usuario autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        dict: Resultado de validación con flag 'valid' y lista de 'issues' si existen problemas.
    """
    validation = CartService.validate_cart_stock(db, current_user.user_id)
    return validation