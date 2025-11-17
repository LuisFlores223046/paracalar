# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 15/11/25
# Descripción: Servicio para búsqueda avanzada y filtrado de productos, incluyendo categorías,
#              actividades físicas, objetivos fitness, rangos de precio y combinación de filtros.

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional, Tuple
from fastapi import HTTPException, status

from app.models.product import Product
from app.api.v1.search import schemas


class SearchService:
    """Servicio para búsqueda y filtrado de productos"""
    
    @staticmethod
    def search_and_filter_products(
        db: Session,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
        category: Optional[str] = None,
        physical_activity: Optional[str] = None,
        fitness_objective: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: bool = True
    ) -> Tuple[List[Product], int]:
        """
        Autor: Luis Flores y Lizbeth Barajas

        Descripción:
            Realiza una búsqueda avanzada de productos aplicando múltiples filtros como texto,
            categoría, actividad física, objetivos fitness, rango de precios y estado de actividad.
            Incluye paginación y devuelve el total sin paginar.

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            query (str | None): Texto de búsqueda para nombre, descripción, marca o categoría.
            skip (int): Número de registros a omitir para paginación.
            limit (int): Número máximo de registros a devolver.
            category (str | None): Categoría específica a filtrar.
            physical_activity (str | None): Actividad física asociada al producto.
            fitness_objective (str | None): Objetivo fitness asociado al producto.
            min_price (float | None): Precio mínimo permitido.
            max_price (float | None): Precio máximo permitido.
            is_active (bool): Estado del producto (activo/inactivo).

        Retorna:
            Tuple[List[Product], int]: Lista de productos filtrados y total de coincidencias.
        """

        db_query = db.query(Product).options(
            joinedload(Product.product_images)
        )
        
        # Filtro de activos
        if is_active is not None:
            db_query = db_query.filter(Product.is_active == is_active)
        
        # Búsqueda por texto
        if query:
            search_filter = or_(
                Product.name.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%"),
                Product.brand.ilike(f"%{query}%"),
                Product.category.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
        
        # Filtro por categoría
        if category:
            db_query = db_query.filter(Product.category == category)
        
        # Filtro por actividad física
        if physical_activity:
            db_query = db_query.filter(
                Product.physical_activities.contains([physical_activity])
            )
        
        # Filtro por objetivo fitness
        if fitness_objective:
            db_query = db_query.filter(
                Product.fitness_objectives.contains([fitness_objective])
            )
        
        # Filtros de precio
        if min_price is not None:
            db_query = db_query.filter(Product.price >= min_price)
        
        if max_price is not None:
            db_query = db_query.filter(Product.price <= max_price)

        if min_price and max_price and min_price > max_price:
            raise HTTPException(400, "min_price no puede ser mayor que max_price")
        
        # Obtener total antes de paginar
        total = db_query.count()
        
        # Paginación
        products = db_query.offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def get_available_categories(db: Session) -> List[str]:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene todas las categorías disponibles entre los productos activos,
            eliminando duplicados y regresando el listado ordenado.

        Parámetros:
            db (Session): Sesión activa de la base de datos.

        Retorna:
            List[str]: Lista ordenada de categorías únicas.
        """
        from sqlalchemy import distinct
        
        categories = db.query(distinct(Product.category)).filter(
            Product.is_active == True
        ).all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        return sorted(category_list)
    
    @staticmethod
    def get_available_filters(db: Session) -> dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene los filtros dinámicos disponibles para productos activos, incluyendo categorías,
            actividades físicas y objetivos fitness. Los resultados son únicos y ordenados.

        Parámetros:
            db (Session): Sesión activa de la base de datos.

        Retorna:
            dict: Diccionario con listas de categorías, actividades físicas y objetivos fitness.
        """

        # Categorías
        categories = SearchService.get_available_categories(db)
        
        # Actividades físicas únicas
        activities_query = db.query(Product.physical_activities).filter(
            Product.is_active == True
        ).all()
        
        activities = set()
        for row in activities_query:
            if row[0]:  # Si no es None
                activities.update(row[0])
        
        # Objetivos fitness únicos
        objectives_query = db.query(Product.fitness_objectives).filter(
            Product.is_active == True
        ).all()
        
        objectives = set()
        for row in objectives_query:
            if row[0]:  # Si no es None
                objectives.update(row[0])
        
        return {
            "categories": categories,
            "physical_activities": sorted(list(activities)),
            "fitness_objectives": sorted(list(objectives))
        }