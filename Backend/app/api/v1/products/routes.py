from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from app.api.deps import get_db, get_current_user
from app.api.v1.products import schemas
from app.api.v1.products.service import ProductService, ReviewService
from app.models.user import User

router = APIRouter()


# ============ ENDPOINTS DE PRODUCTOS ============

@router.get("/", response_model=schemas.PaginatedResponse)
def get_all_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,  # ✅ Cambio: ahora es string
    fitness_objective: Optional[str] = None,
    physical_activity: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los productos con filtros y paginación.
    
    - **page**: Número de página (default: 1)
    - **limit**: Items por página (default: 10, max: 100)
    - **category**: Filtrar por categoría (string directo, ej: "Proteínas")
    - **fitness_objective**: Filtrar por objetivo fitness
    - **physical_activity**: Filtrar por actividad física
    - **min_price**: Precio mínimo
    - **max_price**: Precio máximo
    - **is_active**: Mostrar solo productos activos (default: True)
    """
    skip = (page - 1) * limit
    
    products, total = ProductService.get_all_products(
        db=db,
        skip=skip,
        limit=limit,
        category=category,  # ✅ Ahora es string
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
        if product.product_images:  # ✅ Usar product_images
            primary = next((img for img in product.product_images if img.is_primary), None)
            primary_image = primary.image_path if primary else product.product_images[0].image_path
        
        items.append(schemas.ProductListResponse(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            average_rating=product.average_rating,
            brand=product.brand,
            category=product.category,  # ✅ String directo
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


@router.get("/categories", response_model=List[str])
def get_all_categories(db: Session = Depends(get_db)):
    """
    Obtiene todas las categorías únicas de productos disponibles.
    """
    from sqlalchemy import distinct
    from app.models.product import Product
    
    categories = db.query(distinct(Product.category)).filter(
        Product.is_active == True
    ).all()
    
    category_list = [cat[0] for cat in categories if cat[0]]
    return sorted(category_list)

@router.get("/search", response_model=schemas.PaginatedResponse)
def search_products(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Busca productos por nombre, descripción, marca o categoría.
    
    - **query**: Término de búsqueda (requerido)
    """
    skip = (page - 1) * limit
    
    products, total = ProductService.search_products(
        db=db,
        query=query,
        skip=skip,
        limit=limit
    )
    
    # Convertir a ProductListResponse
    items = []
    for product in products:
        primary_image = None
        if product.product_images:  # ✅ Usar product_images
            primary = next((img for img in product.product_images if img.is_primary), None)
            primary_image = primary.image_path if primary else product.product_images[0].image_path
        
        items.append(schemas.ProductListResponse(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            average_rating=product.average_rating,
            brand=product.brand,
            category=product.category,  # ✅ String directo
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
    
    # Convertir a ProductListResponse
    items = []
    for product in products:
        primary_image = None
        if product.product_images:  # ✅ Usar product_images
            primary = next((img for img in product.product_images if img.is_primary), None)
            primary_image = primary.image_path if primary else product.product_images[0].image_path
        
        items.append(schemas.ProductListResponse(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            average_rating=product.average_rating,
            brand=product.brand,
            category=product.category,  # ✅ String directo
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
    
    # Agregar nombre de usuario a cada review
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


@router.put("/reviews/{review_id}", response_model=schemas.ReviewResponse)
def update_review(
    review_id: int,
    review_data: schemas.ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza una reseña existente.
    Solo el autor puede actualizar su reseña.
    """
    review = ReviewService.update_review(
        db=db,
        review_id=review_id,
        user_id=current_user.user_id,
        review_data=review_data
    )
    
    response = schemas.ReviewResponse.from_orm(review)
    response.user_name = f"{current_user.first_name} {current_user.last_name}"
    
    return response


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina una reseña.
    Solo el autor puede eliminar su reseña.
    """
    ReviewService.delete_review(
        db=db,
        review_id=review_id,
        user_id=current_user.user_id
    )
    return None



# ============ NOTA SOBRE CATEGORÍAS ============
# Las categorías ahora son strings directos en el modelo Product.
# No hay endpoints separados para categorías.
# Para filtrar por categoría, usa: GET /api/v1/products/?category=Proteínas