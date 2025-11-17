# Autor: Gabriel Vilchis
# Fecha 14/11/2025
# Descripcion: Este codigo define los endopints de la API para la gestion de analiticas, reportes
# y exportacion de datos para el dashboard adminsitrativo. Todos los endopints requieren autenticacion
# y el rol de administrador
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.api.deps import require_admin
from app.api.v1.analytics import schemas
from app.api.v1.analytics.service import AnalyticsService, ReportExportService
from app.models.user import User
from app.api.deps import get_db, require_admin
import io, csv
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/dashboard", response_model=schemas.AdminDashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Autor: Gabriel Vilchis
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
    Autor: Gabriel Vilchis
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
    Autor: Gabriel Vilchis
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
    Autor: Gabriel Vilchis
    Obtiene productos con stock bajo. Útil para alertas de reabastecimiento.
    """
    products = AnalyticsService.get_low_stock_products(db, threshold)
    return products

@router.get("/reports/sales/export/csv")
async def export_sales_report_csv(
    start_date: Optional[datetime] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Autor: Gabriel Vilchis
    Exporta el reporte de ventas en formato CSV
    """
    sales_report = AnalyticsService.generate_sales_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )

    csv_buffer = ReportExportService.export_sales_report_to_csv(sales_report)
    
    filename = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/reports/sales/export/pdf")
async def export_sales_report_pdf(
    start_date: Optional[datetime] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Autor: Gabriel Vilchis
    Exporta el reporte de ventas en formato PDF
    """
    sales_report = AnalyticsService.generate_sales_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    
    pdf_buffer = ReportExportService.export_sales_report_to_pdf(sales_report)
    
    filename = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/reports/products/export/csv")
async def export_product_report_csv(
    start_date: Optional[datetime] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Autor: Gabriel Vilchis
    Exporta el reporte de productos en formato CSV
    """
    
    products = AnalyticsService.get_product_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )

    csv_buffer = ReportExportService.export_product_report_to_csv(products)
    
    filename = f"reporte_productos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/reports/products/export/pdf")
async def export_product_report_pdf(
    start_date: Optional[datetime] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Autor: Gabriel Vilchis
    Exporta el reporte de productos en formato PDF
    """

    products = AnalyticsService.get_product_report(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    
    pdf_buffer = ReportExportService.export_product_report_to_pdf(products)
    
    filename = f"reporte_productos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/reports/low-stock/export/csv")
async def export_low_stock_csv(
    threshold: int = Query(10, description="Umbral de stock bajo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Autor: Gabriel Vilchis
    Exporta el reporte de productos con stock bajo en formato CSV
    """

    # Obtener productos con stock bajo
    products = AnalyticsService.get_low_stock_products(db, threshold)
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(['PRODUCTOS CON STOCK BAJO'])
    writer.writerow(['Umbral', threshold])
    writer.writerow([])
    writer.writerow(['ID', 'Nombre', 'Stock Actual', 'Precio', 'Estado'])
    
    # Datos
    for product in products:
        writer.writerow([
            product.product_id,
            product.name,
            product.stock,
            f"${product.price:,.2f}",
            'Activo' if product.is_active else 'Inactivo'
        ])
    
    output.seek(0)
    bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    bytes_output.seek(0)
    
    filename = f"stock_bajo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        bytes_output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )