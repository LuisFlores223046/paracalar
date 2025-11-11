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
    Obtiene el carrito completo del usuario autenticado.
    
    Retorna:
    - Lista de items en el carrito
    - Información de cada producto
    - Total de items y precio total
    """
    cart = CartService.get_cart(db, current_user.user_id)
    
    # Preparar respuesta con cálculos
    items_response = []
    total_items = 0
    total_price = 0.0
    
    for item in cart.cart_items:  # ✅ Usar cart_items
        # Obtener imagen principal del producto
        primary_image = None
        if item.product.product_images:  # ✅ Usar product_images
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
            cart_item_id=item.cart_item_id,  # ✅ Usar cart_item_id correcto
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
    Obtiene un resumen rápido del carrito (útil para el badge del icono).
    
    Retorna:
    - Total de items
    - Precio total
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
    Agrega un producto al carrito.
    
    Si el producto ya existe en el carrito, incrementa la cantidad.
    Verifica que haya stock suficiente antes de agregar.
    
    Body:
    ```json
    {
        "product_id": 1,
        "quantity": 2
    }
    ```
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
    if cart_item.product.product_images:  # ✅ Usar product_images
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
        cart_item_id=cart_item.cart_item_id,  # ✅ Usar cart_item_id
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
    cart_item_id: int,  # ✅ Nombre correcto del parámetro
    update_data: schemas.CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la cantidad de un item en el carrito.
    
    Verifica que haya stock suficiente antes de actualizar.
    
    Body:
    ```json
    {
        "quantity": 3
    }
    ```
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
    if cart_item.product.product_images:  # ✅ Usar product_images
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
        cart_item_id=cart_item.cart_item_id,  # ✅ Usar cart_item_id
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
    cart_item_id: int,  # ✅ Nombre correcto
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un item del carrito.
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
    Vacía completamente el carrito.
    
    Útil después de confirmar un pago o cuando el usuario quiere empezar de nuevo.
    """
    CartService.clear_cart(db, current_user.user_id)
    return None


@router.get("/validate")
def validate_cart_stock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Valida que todos los productos en el carrito tengan stock suficiente.
    
    Útil para llamar antes de proceder al checkout.
    
    Retorna:
    ```json
    {
        "valid": true/false,
        "issues": [
            {
                "cart_item_id": 1,
                "product_id": 5,
                "product_name": "Producto X",
                "issue": "Stock insuficiente",
                "requested": 10,
                "available": 5
            }
        ]
    }
    ```
    """
    validation = CartService.validate_cart_stock(db, current_user.user_id)
    return validation
