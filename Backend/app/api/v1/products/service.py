from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from typing import List, Optional, Tuple
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.category import Category
from app.models.product_image import ProductImage
from app.models.review import Review
from app.models.user import User
from app.api.v1.products import schemas


class ProductService:
    """Servicio para gestión de productos"""
    
    @staticmethod
    def get_all_products(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        category_id: Optional[int] = None,
        fitness_objective: Optional[str] = None,
        physical_activity: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: bool = True
    ) -> Tuple[List[Product], int]:
        """
        Obtiene todos los productos con filtros opcionales.
        Retorna (productos, total_count)
        """
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images)
        )
        
        # Filtros
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if fitness_objective:
            query = query.filter(Product.fitness_objective == fitness_objective)
        
        if physical_activity:
            query = query.filter(Product.physical_activity == physical_activity)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Obtener total antes de paginar
        total = query.count()
        
        # Paginación
        products = query.offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def search_products(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Busca productos por nombre, descripción o marca
        """
        search_filter = or_(
            Product.name.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
            Product.brand.ilike(f"%{query}%")
        )
        
        db_query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images)
        ).filter(
            and_(Product.is_active == True, search_filter)
        )
        
        total = db_query.count()
        products = db_query.offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Product:
        """Obtiene un producto por ID con todas sus relaciones"""
        product = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images),
            joinedload(Product.reviews)
        ).filter(Product.product_id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
        
        return product
    
    @staticmethod
    def get_related_products(
        db: Session,
        product_id: int,
        limit: int = 6
    ) -> List[Product]:
        """
        Obtiene productos relacionados basados en categoría y objetivo fitness
        """
        product = ProductService.get_product_by_id(db, product_id)
        
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.images)
        ).filter(
            and_(
                Product.product_id != product_id,
                Product.is_active == True,
                or_(
                    Product.category_id == product.category_id,
                    Product.fitness_objective == product.fitness_objective
                )
            )
        )
        
        return query.limit(limit).all()
    
    @staticmethod
    def create_product(
        db: Session,
        product_data: schemas.ProductCreate
    ) -> Product:
        """Crea un nuevo producto"""
        # ✅ Verificar que la categoría existe solo si se proporciona
        if product_data.category_id:
            category = db.query(Category).filter(
                Category.category_id == product_data.category_id
            ).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada"
                )
        
        # Verificar SKU único si se proporciona
        if product_data.sku:
            existing_product = db.query(Product).filter(
                Product.sku == product_data.sku
            ).first()
            
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El SKU ya existe"
                )
        
        # Crear producto
        product_dict = product_data.model_dump(exclude={'images'})
        db_product = Product(**product_dict)
        
        db.add(db_product)
        db.flush()  # Para obtener el product_id
        
        # Agregar imágenes si las hay
        if product_data.images:
            for idx, img_data in enumerate(product_data.images):
                img_dict = img_data.model_dump()
                img_dict['product_id'] = db_product.product_id
                img_dict['display_order'] = idx
                
                db_image = ProductImage(**img_dict)
                db.add(db_image)
        
        db.commit()
        db.refresh(db_product)
        
        return db_product
    
    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        product_data: schemas.ProductUpdate
    ) -> Product:
        """Actualiza un producto existente"""
        product = ProductService.get_product_by_id(db, product_id)
        
        # Verificar SKU único si se está actualizando
        if product_data.sku and product_data.sku != product.sku:
            existing_product = db.query(Product).filter(
                Product.sku == product_data.sku
            ).first()
            
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El SKU ya existe"
                )
        
        # Actualizar campos
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """Elimina un producto (soft delete)"""
        product = ProductService.get_product_by_id(db, product_id)
        product.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def hard_delete_product(db: Session, product_id: int) -> bool:
        """Elimina permanentemente un producto"""
        product = ProductService.get_product_by_id(db, product_id)
        db.delete(product)
        db.commit()
        return True


class ReviewService:
    """Servicio para gestión de reseñas"""
    
    @staticmethod
    def get_product_reviews(
        db: Session,
        product_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Review], int]:
        """Obtiene las reseñas de un producto"""
        query = db.query(Review).options(
            joinedload(Review.user)
        ).filter(Review.product_id == product_id)
        
        total = query.count()
        reviews = query.order_by(Review.date_created.desc()).offset(skip).limit(limit).all()
        
        return reviews, total
    
    @staticmethod
    def create_review(
        db: Session,
        product_id: int,
        user_id: int,
        review_data: schemas.ReviewCreate
    ) -> Review:
        """Crea una nueva reseña"""
        # Verificar que el producto existe
        product = db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Verificar si el usuario ya ha reseñado este producto
        existing_review = db.query(Review).filter(
            and_(
                Review.product_id == product_id,
                Review.user_id == user_id
            )
        ).first()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has reseñado este producto"
            )
        
        # TODO: Verificar que el usuario haya comprado el producto
        # (requiere consulta a OrderItem)
        
        # Crear reseña
        review_dict = review_data.model_dump()
        review_dict['product_id'] = product_id
        review_dict['user_id'] = user_id
        
        db_review = Review(**review_dict)
        db.add(db_review)
        
        # Actualizar rating promedio del producto
        ReviewService._update_product_rating(db, product_id)
        
        db.commit()
        db.refresh(db_review)
        
        return db_review
    
    @staticmethod
    def update_review(
        db: Session,
        review_id: int,
        user_id: int,
        review_data: schemas.ReviewUpdate
    ) -> Review:
        """Actualiza una reseña existente"""
        review = db.query(Review).filter(Review.review_id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        
        if review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar esta reseña"
            )
        
        # Actualizar campos
        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        # Actualizar rating promedio del producto
        ReviewService._update_product_rating(db, review.product_id)
        
        db.commit()
        db.refresh(review)
        
        return review
    
    @staticmethod
    def delete_review(db: Session, review_id: int, user_id: int, is_admin: bool = False) -> bool:
        """Elimina una reseña"""
        review = db.query(Review).filter(Review.review_id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reseña no encontrada"
            )
        
        if not is_admin and review.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta reseña"
            )
        
        product_id = review.product_id
        db.delete(review)
        
        # Actualizar rating promedio del producto
        ReviewService._update_product_rating(db, product_id)
        
        db.commit()
        return True
    
    @staticmethod
    def _update_product_rating(db: Session, product_id: int):
        """Actualiza el rating promedio de un producto"""
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.product_id == product_id
        ).scalar()
        
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if product:
            product.average_rating = float(avg_rating) if avg_rating else 0.0


class CategoryService:
    """Servicio para gestión de categorías (solo lectura)"""
    
    @staticmethod
    def get_all_categories(db: Session, is_active: Optional[bool] = True) -> List[Category]:
        """Obtiene todas las categorías"""
        query = db.query(Category)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.all()
    
    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Category:
        """Obtiene una categoría por ID"""
        category = db.query(Category).filter(
            Category.category_id == category_id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        
        return category