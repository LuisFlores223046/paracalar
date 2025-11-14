# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Servicios de lógica de negocio para productos y reseñas. Implementa
#              operaciones CRUD de productos, gestión de reseñas y cálculo de ratings.

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.review import Review
from app.api.v1.products import schemas


class ProductService:
    """
    Autor: Luis Flores
    Descripción: Clase de servicio para gestión de productos.
                 Contiene métodos estáticos para operaciones CRUD y consultas
                 relacionadas con productos.
    """
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Product:
        """
        Autor: Luis Flores
        Descripción: Obtiene un producto por ID con todas sus relaciones cargadas
                     (imágenes y reseñas).
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a buscar.
        Retorna:
            Product: Producto completo con relaciones.
        Excepciones:
            HTTPException 404: Si el producto no existe.
        """
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
        Autor: Luis Flores
        Descripción: Obtiene productos relacionados basados en categoría y objetivos fitness.
                     Excluye el producto de referencia y solo retorna productos activos.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto de referencia.
            limit (int): Cantidad máxima de productos a retornar.
        Retorna:
            List[Product]: Lista de productos relacionados.
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
        """
        Autor: Luis Flores
        Descripción: Crea un nuevo producto con sus imágenes asociadas.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_data (ProductCreate): Datos del producto a crear.
        Retorna:
            Product: Producto creado con todas sus relaciones.
        """
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
        """
        Autor: Luis Flores
        Descripción: Actualiza un producto existente. Solo actualiza los campos
                     proporcionados en product_data.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a actualizar.
            product_data (ProductUpdate): Datos a actualizar (campos opcionales).
        Retorna:
            Product: Producto actualizado.
        Excepciones:
            HTTPException 404: Si el producto no existe.
        """
        product = ProductService.get_product_by_id(db, product_id)
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """
        Autor: Luis Flores
        Descripción: Realiza un soft delete del producto (is_active = False).
                     El producto no se elimina físicamente de la base de datos.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a desactivar.
        Retorna:
            bool: True si la desactivación fue exitosa.
        Excepciones:
            HTTPException 404: Si el producto no existe.
        """
        product = ProductService.get_product_by_id(db, product_id)
        product.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def hard_delete_product(db: Session, product_id: int) -> bool:
        """
        Autor: Luis Flores
        Descripción: Elimina permanentemente un producto de la base de datos.
                     Esta operación no se puede revertir.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a eliminar.
        Retorna:
            bool: True si la eliminación fue exitosa.
        Excepciones:
            HTTPException 404: Si el producto no existe.
        """
        product = ProductService.get_product_by_id(db, product_id)
        db.delete(product)
        db.commit()
        return True


class ReviewService:
    """
    Autor: Luis Flores
    Descripción: Clase de servicio para gestión de reseñas de productos.
                 Contiene métodos para CRUD de reseñas y actualización de ratings.
    """
    
    @staticmethod
    def get_product_reviews(
        db: Session,
        product_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Review], int]:
        """
        Autor: Luis Flores
        Descripción: Obtiene las reseñas de un producto con paginación.
                     Las reseñas incluyen información del usuario que las creó.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto.
            skip (int): Cantidad de reseñas a saltar (para paginación).
            limit (int): Cantidad máxima de reseñas a retornar.
        Retorna:
            tuple: (lista de reseñas, total de reseñas).
        """
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
        review_data: schemas.ReviewCreate,
        order_id: int
) -> Review:
        """
        Autor: Luis Flores
        Descripción: Crea una nueva reseña para un producto. Verifica que el producto
                     exista y que el usuario no haya reseñado previamente el producto.
                     Actualiza automáticamente el rating promedio del producto.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a reseñar.
            user_id (int): ID del usuario que crea la reseña.
            review_data (ReviewCreate): Datos de la reseña (rating y texto).
        Retorna:
            Review: Reseña creada.
        Excepciones:
            HTTPException 404: Si el producto no existe.
            HTTPException 400: Si el usuario ya reseñó este producto.
        """
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
        review_dict['order_id'] = order_id
        
        db_review = Review(**review_dict)
        db.add(db_review)

        db.flush()
        
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
        """
        Autor: Luis Flores
        Descripción: Actualiza una reseña existente. Verifica que el usuario
                     sea el dueño de la reseña. Actualiza el rating promedio del producto.
        Parámetros:
            db (Session): Sesión de base de datos.
            review_id (int): ID de la reseña a actualizar.
            user_id (int): ID del usuario que intenta actualizar.
            review_data (ReviewUpdate): Nuevos datos de la reseña.
        Retorna:
            Review: Reseña actualizada.
        Excepciones:
            HTTPException 404: Si la reseña no existe.
            HTTPException 403: Si el usuario no es el dueño de la reseña.
        """
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
        """
        Autor: Luis Flores
        Descripción: Elimina una reseña. Los usuarios solo pueden eliminar sus propias
                     reseñas, pero los administradores pueden eliminar cualquier reseña.
                     Actualiza el rating promedio del producto.
        Parámetros:
            db (Session): Sesión de base de datos.
            review_id (int): ID de la reseña a eliminar.
            user_id (int): ID del usuario que intenta eliminar.
            is_admin (bool): Indica si el usuario es administrador.
        Retorna:
            bool: True si la eliminación fue exitosa.
        Excepciones:
            HTTPException 404: Si la reseña no existe.
            HTTPException 403: Si el usuario no tiene permisos para eliminar.
        """
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
        """
        Autor: Luis Flores
        Descripción: Actualiza el rating promedio de un producto basándose en todas
                     sus reseñas. Método interno usado después de crear, actualizar
                     o eliminar reseñas.
        Parámetros:
            db (Session): Sesión de base de datos.
            product_id (int): ID del producto a actualizar.
        Retorna:
            None: Actualiza directamente en la base de datos.
        """
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.product_id == product_id
        ).scalar()
        
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if product:
            product.average_rating = float(avg_rating) if avg_rating else None