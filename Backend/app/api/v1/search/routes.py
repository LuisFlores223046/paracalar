# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 15-11-25
# Descripción: Rutas para el servicio de busqueda y filtrado

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.api.deps import get_db
from app.api.v1.search import schemas
from app.api.v1.search.service import SearchService

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedResponse)
def search_products(
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    fitness_objective: Optional[str] = Query(None, description="Filtrar por objetivo fitness"),
    physical_activity: Optional[str] = Query(None, description="Filtrar por actividad física"),
    min_price: Optional[float] = Query(None, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, description="Precio máximo"),
    is_active: bool = Query(True, description="Solo productos activos"),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas

    Descripción: Busca y filtra productos con múltiples criterios.
    
    **Parámetros de búsqueda:**
    - **query**: Busca en nombre, descripción, marca y categoría
    
    **Filtros disponibles:**
    - **category**: Categoría exacta (ej: "Proteínas")
    - **fitness_objective**: Objetivo fitness (ej: "muscle_gain")
    - **physical_activity**: Actividad física (ej: "weightlifting")
    - **min_price** y **max_price**: Rango de precios
    - **is_active**: Mostrar solo productos activos
    
    **Paginación:**
    - **page**: Número de página (default: 1)
    - **limit**: Items por página (default: 10, max: 100)
    """
    skip = (page - 1) * limit
    
    products, total = SearchService.search_and_filter_products(
        db=db,
        query=query,
        skip=skip,
        limit=limit,
        category=category,
        fitness_objective=fitness_objective,
        physical_activity=physical_activity,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active
    )
    
    # Convertir a ProductListResponse
    items = []
    for product in products:
        primary_image = None
        if product.product_images:
            primary = next((img for img in product.product_images if img.is_primary), None)
            primary_image = primary.image_path if primary else product.product_images[0].image_path
        
        items.append(schemas.ProductListResponse(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            average_rating=product.average_rating,
            brand=product.brand,
            category=product.category,
            primary_image=primary_image
        ))
    
    total_pages = math.ceil(total / limit)
    
    return schemas.PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/filters")
def get_available_filters(db: Session = Depends(get_db)):
    """
    Autor: Lizbeth Barajas
    
    Descripción: Obtiene todos los filtros disponibles para búsqueda.
    
    Parámetros: 
        Base de datos
        
    Retorna:
    - **categories**: Lista de categorías
    - **physical_activities**: Lista de actividades físicas
    - **fitness_objectives**: Lista de objetivos fitness
    """
    return SearchService.get_available_filters(db)