# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Schemas de validación y serialización para productos y reseñas.
#              Define las estructuras de datos para productos, imágenes y reseñas.

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ PRODUCT IMAGE SCHEMAS ============

class ProductImageBase(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema base para imágenes de productos.
    """
    image_path: str = Field(..., description="URL de la imagen en S3")
    is_primary: bool = Field(default=False, description="Indica si es la imagen principal")


class ProductImageCreate(ProductImageBase):
    """
    Autor: Luis Flores
    Descripción: Schema para crear una nueva imagen de producto.
    """
    pass


class ProductImageResponse(ProductImageBase):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta para una imagen de producto.
    """
    image_id: int
    product_id: int

    class Config:
        from_attributes = True


# ============ PRODUCT SCHEMAS ============

class ProductBase(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema base con campos comunes de productos.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción detallada del producto")
    brand: str = Field(..., min_length=1, max_length=100, description="Marca del producto")
    category: str = Field(..., min_length=1, max_length=100, description="Categoría del producto")
    physical_activities: List[str] = Field(
        default_factory=list,
        description="Lista de actividades físicas relacionadas (ej: ['weightlifting', 'crossfit'])"
    )
    fitness_objectives: List[str] = Field(
        default_factory=list,
        description="Lista de objetivos fitness (ej: ['muscle_gain', 'weight_loss'])"
    )
    nutritional_value: str = Field(..., description="Información nutricional del producto")
    price: float = Field(..., gt=0, description="Precio del producto (debe ser mayor a 0)")
    stock: int = Field(default=0, ge=0, description="Cantidad en inventario (mayor o igual a 0)")


class ProductCreate(ProductBase):
    """
    Autor: Luis Flores
    Descripción: Schema para crear un nuevo producto.
                 Incluye opcionalmente las imágenes del producto.
    """
    product_images: Optional[List[ProductImageCreate]] = Field(
        default=[],
        description="Lista de imágenes del producto"
    )


class ProductUpdate(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema para actualizar un producto existente.
                 Todos los campos son opcionales, solo se actualizan los proporcionados.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    physical_activities: Optional[List[str]] = None
    fitness_objectives: Optional[List[str]] = None
    nutritional_value: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = Field(None, description="Estado de activación del producto")


class ProductResponse(ProductBase):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta completo para un producto.
                 Incluye toda la información del producto, imágenes y metadatos.
    """
    product_id: int
    average_rating: Optional[float] = Field(None, description="Rating promedio del producto (1-5)")
    is_active: bool = Field(..., description="Indica si el producto está activo")
    created_at: datetime
    updated_at: datetime
    product_images: List[ProductImageResponse] = Field(
        default=[],
        description="Lista de todas las imágenes del producto"
    )

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema simplificado para listado de productos.
                 Contiene solo la información esencial para mostrar en listas o grillas.
    """
    product_id: int
    name: str
    brand: str
    category: str
    price: float
    stock: int
    average_rating: Optional[float] = Field(None, description="Rating promedio (1-5)")
    primary_image: Optional[str] = Field(None, description="URL de la imagen principal")

    class Config:
        from_attributes = True


# ============ REVIEW SCHEMAS ============

class ReviewBase(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema base para reseñas de productos.
    """
    rating: int = Field(..., ge=1, le=5, description="Calificación del producto (1-5 estrellas)")
    review_text: Optional[str] = Field(None, description="Texto de la reseña (opcional)")


class ReviewCreate(ReviewBase):
    """
    Autor: Luis Flores
    Descripción: Schema para crear una nueva reseña.
    """
    pass


class ReviewUpdate(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema para actualizar una reseña existente.
                 Ambos campos son opcionales.
    """
    rating: Optional[int] = Field(None, ge=1, le=5, description="Nueva calificación (1-5)")
    review_text: Optional[str] = Field(None, description="Nuevo texto de la reseña")


class ReviewResponse(ReviewBase):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta completo para una reseña.
                 Incluye información del usuario y metadatos de la reseña.
    """
    review_id: int
    product_id: int
    user_id: int
    date_created: datetime
    updated_at: datetime
    user_name: Optional[str] = Field(None, description="Nombre completo del usuario que hizo la reseña")

    class Config:
        from_attributes = True