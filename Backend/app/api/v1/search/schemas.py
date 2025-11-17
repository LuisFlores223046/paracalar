# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 15-11-25
# Descripción: Esquemas Pydantic para el módulo de búsqueda

from pydantic import BaseModel, Field
from typing import List, Optional

# ============ PRODUCT LIST RESPONSE ============
class ProductListResponse(BaseModel):
    """Schema simplificado para listado de productos"""
    product_id: int
    name: str
    brand: str
    category: str
    price: float
    stock: int
    average_rating: Optional[float]
    primary_image: Optional[str] = None

    class Config:
        from_attributes = True


# ============ PAGINATION ============
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[ProductListResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ============ SEARCH FILTERS ============
class SearchFilters(BaseModel):
    """Filtros disponibles para búsqueda"""
    query: Optional[str] = None
    category: Optional[str] = None
    fitness_objective: Optional[str] = None
    physical_activity: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: bool = True