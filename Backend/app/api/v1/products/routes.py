from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.api.v1.products import schemas
from app.api.v1.products.service import ProductService, ReviewService
from app.models.user import User

router = APIRouter()


# ============ ENDPOINTS DE PRODUCTOS ============

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles completos de un producto.
    """
    product = ProductService.get_product_by_id(db, product_id)
    return product


@router.get("/{product_id}/related", response_model=List[schemas.ProductListResponse])
def get_related_products(
    product_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Obtiene productos relacionados basados en categoría y objetivos fitness.
    """
    products = ProductService.get_related_products(db, product_id, limit)
    
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
    
    return items


# ============ ENDPOINTS DE REVIEWS ============

@router.get("/{product_id}/reviews", response_model=List[schemas.ReviewResponse])
def get_product_reviews(
    product_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Obtiene las reseñas de un producto.
    """
    skip = (page - 1) * limit
    reviews, total = ReviewService.get_product_reviews(db, product_id, skip, limit)
    
    response = []
    for review in reviews:
        review_dict = schemas.ReviewResponse.from_orm(review)
        review_dict.user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Usuario"
        response.append(review_dict)
    
    return response


@router.post(
    "/{product_id}/reviews",
    response_model=schemas.ReviewResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product_review(
    product_id: int,
    review_data: schemas.ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva reseña para un producto.
    Requiere autenticación.
    """
    review = ReviewService.create_review(
        db=db,
        product_id=product_id,
        user_id=current_user.user_id,
        review_data=review_data
    )
    
    response = schemas.ReviewResponse.from_orm(review)
    response.user_name = f"{current_user.first_name} {current_user.last_name}"
    
    return response