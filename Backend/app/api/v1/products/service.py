from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.review import Review
from app.api.v1.products import schemas


class ProductService:
    """Servicio para gestión de productos"""
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Product:
        """Obtiene un producto por ID con todas sus relaciones"""
        product = db.query(Product).options(
            joinedload(Product.product_images),
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
        Obtiene productos relacionados basados en categoría y objetivos fitness
        """
        product = ProductService.get_product_by_id(db, product_id)
        
        query = db.query(Product).options(
            joinedload(Product.product_images)
        ).filter(
            and_(
                Product.product_id != product_id,
                Product.is_active == True,
                or_(
                    Product.category == product.category,
                    *[Product.fitness_objectives.contains([obj]) 
                      for obj in product.fitness_objectives] if product.fitness_objectives else []
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
        product_dict = product_data.model_dump(exclude={'product_images'})
        db_product = Product(**product_dict)
        
        db.add(db_product)
        db.flush()
        
        if product_data.product_images:
            for img_data in product_data.product_images:
                img_dict = img_data.model_dump()
                img_dict['product_id'] = db_product.product_id
                
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
    ) -> tuple[List[Review], int]:
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
        product = db.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
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
        
        review_dict = review_data.model_dump()
        review_dict['product_id'] = product_id
        review_dict['user_id'] = user_id
        
        db_review = Review(**review_dict)
        db.add(db_review)
        
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
        
        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
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
            product.average_rating = float(avg_rating) if avg_rating else None