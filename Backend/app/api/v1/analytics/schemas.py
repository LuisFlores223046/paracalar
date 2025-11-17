# Autor: Gabriel Vilchis
# Fecha 14/11/2025
# Descripcion: Este codigo define los esquemas (schemas) de Pydantic utilizados para la
# validación de datos de entrada y la estructura de las respuestas (payloads)
# en los endpoints de analíticas, reportes y métricas del dashboard administrativo.
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Estadisticas de productos
class ProductStats(BaseModel):
    product_id: int
    name: str
    total_sold: int
    total_revenue: float
    average_rating: Optional[float]
    total_reviews: int

class SalesStats(BaseModel):
    total_sales: float
    total_orders: int
    total_products_sold: int
    average_order_value: float
    top_selling_products: List[ProductStats]

class TopProduct(BaseModel):
    product_id: int
    name: str
    brand: str
    category: str
    total_sold: int
    total_revenue: float
    image_url: Optional[str]

# Estadisticas de usuarios
class UserStats(BaseModel):
    total_users: int
    active_users: int
    new_users_this_month: int
    users_with_orders: int

class SubscriptionStats(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    paused_subscriptions: int
    cancelled_subscriptions: int
    new_subscriptions_this_month: int
    subscription_revenue: float

# Estadisticas generales
class TodaySummary(BaseModel):
    total_sales: float
    total_orders: int
    total_products_sold: int
    new_subscriptions: int

class MonthlySalesData(BaseModel):
    month: str  # Formato: "2024-01" o "Enero 2024"
    sales: float
    orders: int

class CategorySalesData(BaseModel):
    category: str
    total_sales: float
    total_products_sold: int
    percentage: float

class SubscriberGrowthData(BaseModel):
    month: str
    new_subscribers: int
    total_active: int

# Dashboard completo del admin con todas las graficas
class AdminDashboardStats(BaseModel):
    sales: SalesStats
    users: UserStats
    subscriptions: SubscriptionStats
    
    # Estadisticas basicas
    total_products: int
    low_stock_products: int
    
    # Producto destacado
    top_product: Optional[TopProduct]
    
    # Resumen de hoy
    today_summary: TodaySummary
    
    # Datos para gráficas
    monthly_sales: List[MonthlySalesData]
    category_sales: List[CategorySalesData]
    subscriber_growth: List[SubscriberGrowthData]

# Reportes
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
    category: str
    total_sold: int
    revenue: float
    current_stock: int
    average_rating: Optional[float]

class SalesReport(BaseModel):
    """Reporte completo de ventas"""
    report_type: str = "sales"
    start_date: datetime
    end_date: datetime
    summary: Dict[str, Any]
    details: List[SalesReportItem]
