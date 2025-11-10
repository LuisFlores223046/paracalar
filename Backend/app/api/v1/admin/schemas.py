from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ ESTADÍSTICAS ============
class ProductStats(BaseModel):
    """Estadísticas de un producto"""
    product_id: int
    name: str
    total_sold: int
    total_revenue: float
    average_rating: Optional[float]  # ✅ Puede ser None
    total_reviews: int


class SalesStats(BaseModel):
    """Estadísticas generales de ventas"""
    total_sales: float
    total_orders: int
    total_products_sold: int
    average_order_value: float
    top_selling_products: List[ProductStats]


class UserStats(BaseModel):
    """Estadísticas de usuarios"""
    total_users: int
    active_users: int
    new_users_this_month: int
    users_with_orders: int


class AdminDashboardStats(BaseModel):
    """Dashboard completo del administrador"""
    sales: SalesStats
    users: UserStats
    total_products: int
    low_stock_products: int  # Productos con stock < 10
    pending_reviews: int


# ============ REPORTES ============
class ReportParams(BaseModel):
    """Parámetros para generar reportes"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    report_type: str = Field(..., pattern="^(sales|products|users)$")
    format: str = Field(default="json", pattern="^(json|csv)$")


class SalesReportItem(BaseModel):
    """Item de reporte de ventas"""
    date: datetime
    total_sales: float
    total_orders: int
    average_order_value: float


class ProductReportItem(BaseModel):
    """Item de reporte de productos"""
    product_id: int
    name: str
    category: str  # ✅ String directo
    total_sold: int
    revenue: float
    current_stock: int
    average_rating: Optional[float]  # ✅ Puede ser None


class SalesReport(BaseModel):
    """Reporte completo de ventas"""
    report_type: str = "sales"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any]
    details: List[SalesReportItem]


# ============ GESTIÓN DE REVIEWS ============
class ReviewModerationAction(BaseModel):
    """Acción de moderación sobre una review"""
    action: str = Field(..., pattern="^(approve|reject|delete)$")
    reason: Optional[str] = None


class BulkProductAction(BaseModel):
    """Acción en lote sobre productos"""
    product_ids: List[int]
    action: str = Field(..., pattern="^(activate|deactivate|delete)$")


class BulkActionResponse(BaseModel):
    """Respuesta de acción en lote"""
    success: int
    failed: int
    errors: List[str] = []
