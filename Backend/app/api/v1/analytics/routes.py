from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, require_admin
from app.api.v1.analytics import schemas
from app.api.v1.analytics.service import AnalyticsService
from app.models.user import User

router = APIRouter()


@router.get("/dashboard", response_model=schemas.AdminDashboardStats)
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
    return AnalyticsService.get_dashboard_stats(db)


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
    return AnalyticsService.generate_sales_report(db, start_date, end_date)


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
    return AnalyticsService.get_product_report(db, start_date, end_date)


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
    products = AnalyticsService.get_low_stock_products(db, threshold)
    return products