# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Schemas de validación y serialización para el módulo de carrito de compras.
#              Define las estructuras de datos para items del carrito, resúmenes y respuestas.

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============ CART ITEM SCHEMAS ============

class CartItemBase(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema base para items del carrito con campos comunes.
    """
    product_id: int
    quantity: int = Field(..., ge=1, description="Cantidad del producto (mínimo 1)")


class CartItemAdd(CartItemBase):
    """
    Autor: Luis Flores
    Descripción: Schema para agregar un item al carrito.
    """
    pass


class CartItemUpdate(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema para actualizar la cantidad de un item en el carrito.
    """
    quantity: int = Field(..., ge=1, description="Nueva cantidad del producto (mínimo 1)")


class CartItemProductInfo(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema con información básica del producto dentro del carrito.
                 Incluye datos necesarios para mostrar el item en la UI.
    """
    product_id: int
    name: str
    price: float
    stock: int
    image_path: Optional[str] = Field(None, description="URL de la imagen principal del producto")
    brand: Optional[str] = Field(None, description="Marca del producto")

    class Config:
        from_attributes = True


class CartItemResponse(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta completo para un item del carrito.
                 Incluye toda la información del item más los detalles del producto.
    """
    cart_item_id: int
    cart_id: int
    product_id: int
    quantity: int
    added_at: datetime
    updated_at: datetime
    product: CartItemProductInfo
    subtotal: float = Field(..., description="Subtotal calculado (cantidad × precio)")

    class Config:
        from_attributes = True


# ============ SHOPPING CART SCHEMAS ============

class ShoppingCartResponse(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta completo para el carrito de compras.
                 Incluye todos los items, totales calculados y metadatos.
    """
    cart_id: int
    user_id: int
    items: List[CartItemResponse] = Field(default=[], description="Lista de items en el carrito")
    total_items: int = Field(..., description="Cantidad total de items en el carrito")
    total_price: float = Field(..., description="Precio total del carrito")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema con resumen rápido del carrito.
                 Útil para mostrar en badges o indicadores del carrito.
    """
    total_items: int = Field(..., description="Cantidad total de items")
    total_price: float = Field(..., description="Precio total del carrito")