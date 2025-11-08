from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_user, require_admin
from app.api.v1.admin import schemas
from app.api.v1.admin.service import AdminStatsService, AdminProductService, AdminReviewService
from app.api.v1.products import schemas as product_schemas
from app.api.v1.products.service import ProductService
from app.models.user import User, UserRole

router = APIRouter()


# ============ ESTADÍSTICAS Y DASHBOARD ============

@router.get("/stats", response_model=schemas.AdminDashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las estadísticas para el dashboard del administrador.
    
    Solo accesible para usuarios con rol de administrador.
    
    Retorna:
    - Estadísticas de ventas (total, órdenes, productos más vendidos)
    - Estadísticas de usuarios (total, activos, nuevos del mes)
    - Estadísticas de productos (total, stock bajo)
    - Reviews pendientes de moderación
    """
    return AdminStatsService.get_dashboard_stats(db)


@router.get("/reports/sales", response_model=schemas.SalesReport)
def generate_sales_report(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin (ISO format)"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Genera un reporte de ventas para un período específico.
    
    Si no se especifican fechas, genera reporte de los últimos 30 días.
    
    Query params:
    - **start_date**: Fecha de inicio en formato ISO
    - **end_date**: Fecha de fin en formato ISO
    """
    return AdminStatsService.generate_sales_report(db, start_date, end_date)


@router.get("/reports/products", response_model=List[schemas.ProductReportItem])
def generate_product_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Genera un reporte de productos con métricas de ventas.
    
    Incluye: ventas totales, ingresos, stock actual, rating promedio por producto.
    """
    return AdminStatsService.get_product_report(db, start_date, end_date)


@router.get("/products/low-stock")
def get_low_stock_products(
    threshold: int = Query(10, ge=1, le=100, description="Umbral de stock bajo"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene productos con stock bajo.
    
    Útil para alertas de reabastecimiento.
    """
    products = AdminStatsService.get_low_stock_products(db, threshold)
    return products


# ============ GESTIÓN DE PRODUCTOS (ADMIN) ============

@router.post("/products", response_model=product_schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: product_schemas.ProductCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo producto.
    
    Solo accesible para administradores.
    
    Body:
    ```json
    {
        "name": "Proteína Whey",
        "description": "Proteína de suero de leche",
        "price": 599.99,
        "stock": 100,
        "category_id": 1,
        "fitness_objective": "muscle_gain",
        "physical_activity": "weightlifting",
        "sku": "PROT-001",
        "brand": "MyBrand",
        "images": [
            {
                "image_url": "https://example.com/image.jpg",
                "is_primary": true,
                "display_order": 0
            }
        ]
    }
    ```
    
    **Nota:** category_id es opcional. Si no se proporciona, el producto no tendrá categoría.
    """
    return ProductService.create_product(db, product_data)


@router.put("/products/{product_id}", response_model=product_schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: product_schemas.ProductUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Actualiza un producto existente.
    
    Solo accesible para administradores.
    """
    return ProductService.update_product(db, product_id, product_data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    hard_delete: bool = Query(False, description="Si es True, elimina permanentemente"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Elimina un producto.
    
    Por defecto hace soft delete (is_active = False).
    Si hard_delete=True, elimina permanentemente de la base de datos.
    
    Solo accesible para administradores.
    """
    if hard_delete:
        ProductService.hard_delete_product(db, product_id)
    else:
        ProductService.delete_product(db, product_id)
    
    return None


@router.post("/products/bulk-action", response_model=schemas.BulkActionResponse)
def bulk_product_action(
    action_data: schemas.BulkProductAction,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Realiza operaciones en lote sobre productos.
    
    Acciones disponibles:
    - **activate**: Activa productos
    - **deactivate**: Desactiva productos
    - **delete**: Elimina productos
    
    Body:
    ```json
    {
        "product_ids": [1, 2, 3, 4],
        "action": "deactivate"
    }
    ```
    """
    return AdminProductService.bulk_update_products(db, action_data)


# ============ MODERACIÓN DE REVIEWS ============

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_review(
    review_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Elimina una reseña como administrador.
    
    Los administradores pueden eliminar cualquier reseña (útil para moderar contenido inapropiado).
    """
    from app.api.v1.products.service import ReviewService
    
    ReviewService.delete_review(
        db=db,
        review_id=review_id,
        user_id=current_user.user_id,
        is_admin=True
    )
    return None


@router.post("/reviews/{review_id}/moderate", status_code=status.HTTP_200_OK)
def moderate_review(
    review_id: int,
    action_data: schemas.ReviewModerationAction,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Modera una reseña.
    
    Acciones disponibles:
    - **approve**: Aprueba la reseña
    - **reject**: Rechaza la reseña
    - **delete**: Elimina la reseña
    
    Body:
    ```json
    {
        "action": "delete",
        "reason": "Contenido inapropiado"
    }
    ```
    """
    AdminReviewService.moderate_review(db, review_id, action_data)
    return {"message": "Reseña moderada exitosamente"}


# ============ NOTA SOBRE CATEGORÍAS ============
# Las categorías son predefinidas y no pueden ser creadas/editadas por admin.
# Para ver las categorías disponibles, usa: GET /api/v1/products/categories/