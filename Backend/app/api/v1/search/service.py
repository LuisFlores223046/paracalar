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
        Busca y filtra productos con múltiples criterios.
        Retorna (productos, total_count)
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
        
        # Obtener total antes de paginar
        total = db_query.count()
        
        # Paginación
        products = db_query.offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def get_available_categories(db: Session) -> List[str]:
        """Obtiene todas las categorías únicas de productos activos"""
        from sqlalchemy import distinct
        
        categories = db.query(distinct(Product.category)).filter(
            Product.is_active == True
        ).all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        return sorted(category_list)
    
    @staticmethod
    def get_available_filters(db: Session) -> dict:
        """
        Obtiene todos los filtros disponibles (categorías, actividades, objetivos)
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