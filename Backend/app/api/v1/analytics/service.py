# Autor: Integración de Luis Flores y equipo
# Fecha: 14/11/2025
# Descripción: Servicio completo de analytics con funcionalidades de exportación a CSV y PDF
#              Incluye generación de reportes de ventas y productos con soporte de descarga

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional
from datetime import datetime, timedelta, date
import io
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.subscription import Subscription
from app.models.enum import OrderStatus, SubscriptionStatus
from app.api.v1.analytics import schemas


class AnalyticsService:
    """
    Servicio para estadísticas y análisis del sistema.
    Proporciona métricas de ventas, usuarios, productos y suscripciones.
    """
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> schemas.AdminDashboardStats:
        """
        Obtiene todas las estadísticas para el dashboard del administrador.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            AdminDashboardStats: Objeto con todas las métricas del dashboard
        """
        sales_stats = AnalyticsService._get_sales_stats(db)
        user_stats = AnalyticsService._get_user_stats(db)
        subscription_stats = AnalyticsService._get_subscription_stats(db)
        
        total_products = db.query(Product).filter(Product.is_active == True).count()
        low_stock_products = db.query(Product).filter(
            and_(Product.is_active == True, Product.stock < 10)
        ).count()
        
        top_product = AnalyticsService._get_top_product(db)
        today_summary = AnalyticsService._get_today_summary(db)
        monthly_sales = AnalyticsService._get_monthly_sales(db)
        category_sales = AnalyticsService._get_category_sales(db)
        subscriber_growth = AnalyticsService._get_subscriber_growth(db)
        
        return schemas.AdminDashboardStats(
            sales=sales_stats,
            users=user_stats,
            subscriptions=subscription_stats,
            total_products=total_products,
            low_stock_products=low_stock_products,
            top_product=top_product,
            today_summary=today_summary,
            monthly_sales=monthly_sales,
            category_sales=category_sales,
            subscriber_growth=subscriber_growth
        )
    
    @staticmethod
    def _get_sales_stats(db: Session) -> schemas.SalesStats:
        """Obtiene estadísticas generales de ventas"""
        total_sales_query = db.query(
            func.sum(Order.total_amount).label('total'),
            func.count(Order.order_id).label('count')
        ).filter(Order.order_status == OrderStatus.DELIVERED)
        
        result = total_sales_query.first()
        total_sales = float(result.total) if result.total else 0.0
        total_orders = result.count if result.count else 0
        
        total_products_sold = db.query(
            func.sum(OrderItem.quantity)
        ).join(Order).filter(
            Order.order_status == OrderStatus.DELIVERED
        ).scalar() or 0
        
        average_order_value = total_sales / total_orders if total_orders > 0 else 0.0
        
        top_products_query = db.query(
            Product.product_id,
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.subtotal).label('total_revenue'),
            Product.average_rating
        ).join(
            OrderItem, Product.product_id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).filter(
            Order.order_status == OrderStatus.DELIVERED
        ).group_by(
            Product.product_id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(10)
        
        top_products = []
        for row in top_products_query.all():
            top_products.append(schemas.ProductStats(
                product_id=row.product_id,
                name=row.name,
                total_sold=row.total_sold or 0,
                total_revenue=float(row.total_revenue or 0),
                average_rating=float(row.average_rating) if row.average_rating else None,
                total_reviews=0
            ))
        
        return schemas.SalesStats(
            total_sales=round(total_sales, 2),
            total_orders=total_orders,
            total_products_sold=total_products_sold,
            average_order_value=round(average_order_value, 2),
            top_selling_products=top_products
        )
    
    @staticmethod
    def _get_user_stats(db: Session) -> schemas.UserStats:
        """Obtiene estadísticas de usuarios"""
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.account_status == True).count()
        
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = db.query(User).filter(
            User.created_at >= start_of_month
        ).count()
        
        users_with_orders = db.query(func.count(func.distinct(Order.user_id))).scalar() or 0
        
        return schemas.UserStats(
            total_users=total_users,
            active_users=active_users,
            new_users_this_month=new_users_this_month,
            users_with_orders=users_with_orders
        )
    
    @staticmethod
    def _get_subscription_stats(db: Session) -> schemas.SubscriptionStats:
        """Obtiene estadísticas de suscripciones"""
        total_subs = db.query(Subscription).count()
        active_subs = db.query(Subscription).filter(
            Subscription.subscription_status == SubscriptionStatus.ACTIVE
        ).count()
        paused_subs = db.query(Subscription).filter(
            Subscription.subscription_status == SubscriptionStatus.PAUSED
        ).count()
        cancelled_subs = db.query(Subscription).filter(
            Subscription.subscription_status == SubscriptionStatus.CANCELLED
        ).count()
        
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_subs_this_month = db.query(Subscription).filter(
            Subscription.start_date >= start_of_month.date()
        ).count()
        
        subscription_revenue = db.query(
            func.sum(Subscription.price)
        ).filter(
            Subscription.subscription_status == SubscriptionStatus.ACTIVE
        ).scalar() or 0.0
        
        return schemas.SubscriptionStats(
            total_subscriptions=total_subs,
            active_subscriptions=active_subs,
            paused_subscriptions=paused_subs,
            cancelled_subscriptions=cancelled_subs,
            new_subscriptions_this_month=new_subs_this_month,
            subscription_revenue=float(subscription_revenue)
        )
    
    @staticmethod
    def _get_top_product(db: Session) -> Optional[schemas.TopProduct]:
        """Obtiene el producto más vendido del momento (últimos 30 días)"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        top_product_query = db.query(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.category,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.subtotal).label('total_revenue')
        ).join(
            OrderItem, Product.product_id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).filter(
            and_(
                Order.order_status == OrderStatus.DELIVERED,
                Order.order_date >= thirty_days_ago
            )
        ).group_by(
            Product.product_id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).first()
        
        if not top_product_query:
            return None
        
        product_image = db.query(ProductImage).filter(
            and_(
                ProductImage.product_id == top_product_query.product_id,
                ProductImage.is_primary == True
            )
        ).first()
        
        image_url = product_image.image_path if product_image else None
        
        return schemas.TopProduct(
            product_id=top_product_query.product_id,
            name=top_product_query.name,
            brand=top_product_query.brand,
            category=top_product_query.category,
            total_sold=top_product_query.total_sold or 0,
            total_revenue=float(top_product_query.total_revenue or 0),
            image_url=image_url
        )
    
    @staticmethod
    def _get_today_summary(db: Session) -> schemas.TodaySummary:
        """Obtiene el resumen del día de hoy"""
        today = date.today()
        
        today_orders = db.query(
            func.sum(Order.total_amount).label('sales'),
            func.count(Order.order_id).label('orders')
        ).filter(
            func.date(Order.order_date) == today
        ).first()
        
        today_products = db.query(
            func.sum(OrderItem.quantity)
        ).join(Order).filter(
            func.date(Order.order_date) == today
        ).scalar() or 0
        
        today_subs = db.query(Subscription).filter(
            Subscription.start_date == today
        ).count()
        
        return schemas.TodaySummary(
            total_sales=float(today_orders.sales or 0),
            total_orders=today_orders.orders or 0,
            total_products_sold=today_products,
            new_subscriptions=today_subs
        )
    
    @staticmethod
    def _get_monthly_sales(db: Session, months: int = 6) -> List[schemas.MonthlySalesData]:
        """Obtiene ventas mensuales de los últimos N meses"""
        result = []
        
        for i in range(months - 1, -1, -1):
            target_date = datetime.now() - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            monthly_data = db.query(
                func.sum(Order.total_amount).label('sales'),
                func.count(Order.order_id).label('orders')
            ).filter(
                and_(
                    extract('year', Order.order_date) == year,
                    extract('month', Order.order_date) == month,
                    Order.order_status == OrderStatus.DELIVERED
                )
            ).first()
            
            month_names = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            month_name = f"{month_names[month - 1]} {year}"
            
            result.append(schemas.MonthlySalesData(
                month=month_name,
                sales=float(monthly_data.sales or 0),
                orders=monthly_data.orders or 0
            ))
        
        return result
    
    @staticmethod
    def _get_category_sales(db: Session) -> List[schemas.CategorySalesData]:
        """Obtiene ventas por categoría"""
        category_data = db.query(
            Product.category,
            func.sum(OrderItem.subtotal).label('total_sales'),
            func.sum(OrderItem.quantity).label('total_products')
        ).join(
            OrderItem, Product.product_id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.order_id
        ).filter(
            Order.order_status == OrderStatus.DELIVERED
        ).group_by(
            Product.category
        ).order_by(
            func.sum(OrderItem.subtotal).desc()
        ).all()
        
        total_sales = sum(float(row.total_sales or 0) for row in category_data)
        
        result = []
        for row in category_data:
            sales = float(row.total_sales or 0)
            percentage = (sales / total_sales * 100) if total_sales > 0 else 0
            
            result.append(schemas.CategorySalesData(
                category=row.category or "Sin categoría",
                total_sales=sales,
                total_products_sold=row.total_products or 0,
                percentage=round(percentage, 2)
            ))
        
        return result
    
    @staticmethod
    def _get_subscriber_growth(db: Session, months: int = 6) -> List[schemas.SubscriberGrowthData]:
        """Obtiene crecimiento de suscriptores por mes"""
        result = []
        
        for i in range(months - 1, -1, -1):
            target_date = datetime.now() - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            
            new_subs = db.query(Subscription).filter(
                and_(
                    Subscription.start_date >= first_day,
                    Subscription.start_date <= last_day
                )
            ).count()
            
            total_active = db.query(Subscription).filter(
                and_(
                    Subscription.start_date <= last_day,
                    Subscription.subscription_status == SubscriptionStatus.ACTIVE
                )
            ).count()
            
            month_names = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            month_name = f"{month_names[month - 1]} {year}"
            
            result.append(schemas.SubscriberGrowthData(
                month=month_name,
                new_subscribers=new_subs,
                total_active=total_active
            ))
        
        return result
    
    @staticmethod
    def generate_sales_report(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> schemas.SalesReport:
        """
        Genera un reporte de ventas para un período específico.
        
        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio (por defecto últimos 30 días)
            end_date: Fecha de fin (por defecto hoy)
            
        Returns:
            SalesReport: Reporte completo de ventas
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        daily_sales = db.query(
            func.date(Order.order_date).label('date'),
            func.sum(Order.total_amount).label('total_sales'),
            func.count(Order.order_id).label('total_orders')
        ).filter(
            and_(
                Order.order_status == OrderStatus.DELIVERED,
                Order.order_date >= start_date,
                Order.order_date <= end_date
            )
        ).group_by(
            func.date(Order.order_date)
        ).order_by(
            func.date(Order.order_date)
        ).all()
        
        details = []
        total_sales = 0.0
        total_orders = 0
        
        for row in daily_sales:
            sales = float(row.total_sales or 0)
            orders = row.total_orders or 0
            avg_order = sales / orders if orders > 0 else 0.0
            
            details.append(schemas.SalesReportItem(
                date=row.date,
                total_sales=round(sales, 2),
                total_orders=orders,
                average_order_value=round(avg_order, 2)
            ))
            
            total_sales += sales
            total_orders += orders
        
        summary = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_sales": round(total_sales, 2),
            "total_orders": total_orders,
            "average_order_value": round(total_sales / total_orders if total_orders > 0 else 0, 2),
            "days_in_period": len(details)
        }
        
        return schemas.SalesReport(
            report_type="sales",
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            details=details
        )
    
    @staticmethod
    def get_product_report(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[schemas.ProductReportItem]:
        """
        Genera un reporte de productos con ventas y métricas.
        
        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio (por defecto últimos 30 días)
            end_date: Fecha de fin (por defecto hoy)
            
        Returns:
            List[ProductReportItem]: Lista de productos con sus métricas
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = db.query(
            Product.product_id,
            Product.name,
            Product.category,
            func.coalesce(func.sum(OrderItem.quantity), 0).label('total_sold'),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label('revenue'),
            Product.stock,
            Product.average_rating
        ).outerjoin(
            OrderItem, Product.product_id == OrderItem.product_id
        ).outerjoin(
            Order, and_(
                OrderItem.order_id == Order.order_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.order_status == OrderStatus.DELIVERED
            )
        ).group_by(
            Product.product_id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        )
        
        report = []
        for row in query.all():
            report.append(schemas.ProductReportItem(
                product_id=row.product_id,
                name=row.name,
                category=row.category or "Sin categoría",
                total_sold=row.total_sold,
                revenue=float(row.revenue),
                current_stock=row.stock,
                average_rating=float(row.average_rating) if row.average_rating else None
            ))
        
        return report
    
    @staticmethod
    def get_low_stock_products(db: Session, threshold: int = 10) -> List[Product]:
        """
        Obtiene productos con stock bajo.
        
        Args:
            db: Sesión de base de datos
            threshold: Umbral de stock bajo (por defecto 10)
            
        Returns:
            List[Product]: Lista de productos con stock bajo
        """
        return db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.stock < threshold
            )
        ).order_by(Product.stock.asc()).all()


class ReportExportService:
    """
    Servicio para exportación de reportes a diferentes formatos (CSV, PDF).
    Proporciona métodos para generar archivos descargables de reportes.
    """
    
    @staticmethod
    def export_sales_report_to_csv(sales_report: schemas.SalesReport) -> io.BytesIO:
        """
        Exporta un reporte de ventas a formato CSV.
        
        Args:
            sales_report: Reporte de ventas a exportar
            
        Returns:
            BytesIO: Buffer con el contenido del archivo CSV
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados del reporte
        writer.writerow(['REPORTE DE VENTAS'])
        writer.writerow(['Período', f"{sales_report.start_date.strftime('%Y-%m-%d')} - {sales_report.end_date.strftime('%Y-%m-%d')}"])
        writer.writerow([])
        
        # Resumen
        writer.writerow(['RESUMEN'])
        writer.writerow(['Total de Ventas', f"${sales_report.summary['total_sales']:,.2f}"])
        writer.writerow(['Total de Pedidos', sales_report.summary['total_orders']])
        writer.writerow(['Valor Promedio de Pedido', f"${sales_report.summary['average_order_value']:,.2f}"])
        writer.writerow(['Días en el Período', sales_report.summary['days_in_period']])
        writer.writerow([])
        
        # Detalles diarios
        writer.writerow(['DETALLES DIARIOS'])
        writer.writerow(['Fecha', 'Ventas Totales', 'Pedidos Totales', 'Valor Promedio'])
        
        for item in sales_report.details:
            writer.writerow([
                item.date.strftime('%Y-%m-%d'),
                f"${item.total_sales:,.2f}",
                item.total_orders,
                f"${item.average_order_value:,.2f}"
            ])
        
        # Convertir a bytes con encoding UTF-8
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        
        return bytes_output
    
    @staticmethod
    def export_product_report_to_csv(products: List[schemas.ProductReportItem]) -> io.BytesIO:
        """
        Exporta un reporte de productos a formato CSV.
        
        Args:
            products: Lista de productos a exportar
            
        Returns:
            BytesIO: Buffer con el contenido del archivo CSV
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['REPORTE DE PRODUCTOS'])
        writer.writerow([])
        writer.writerow([
            'ID Producto',
            'Nombre',
            'Categoría',
            'Unidades Vendidas',
            'Ingresos',
            'Stock Actual',
            'Rating Promedio'
        ])
        
        # Datos de productos
        for product in products:
            writer.writerow([
                product.product_id,
                product.name,
                product.category,
                product.total_sold,
                f"${product.revenue:,.2f}",
                product.current_stock,
                f"{product.average_rating:.1f}" if product.average_rating else "N/A"
            ])
        
        # Convertir a bytes
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        
        return bytes_output
    
    @staticmethod
    def export_sales_report_to_pdf(sales_report: schemas.SalesReport) -> io.BytesIO:
        """
        Exporta un reporte de ventas a formato PDF.
        
        Args:
            sales_report: Reporte de ventas a exportar
            
        Returns:
            BytesIO: Buffer con el contenido del archivo PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Título
        elements.append(Paragraph('REPORTE DE VENTAS', title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Período
        period_text = f"Período: {sales_report.start_date.strftime('%d/%m/%Y')} - {sales_report.end_date.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Resumen
        elements.append(Paragraph('RESUMEN EJECUTIVO', heading_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Ventas', f"${sales_report.summary['total_sales']:,.2f}"],
            ['Total de Pedidos', str(sales_report.summary['total_orders'])],
            ['Valor Promedio de Pedido', f"${sales_report.summary['average_order_value']:,.2f}"],
            ['Días en el Período', str(sales_report.summary['days_in_period'])]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Detalles diarios (solo primeros 20 para no sobrecargar el PDF)
        elements.append(Paragraph('DETALLES DIARIOS (Últimos 20 días)', heading_style))
        
        details_data = [['Fecha', 'Ventas', 'Pedidos', 'Promedio']]
        for item in sales_report.details[-20:]:
            details_data.append([
                item.date.strftime('%d/%m/%Y'),
                f"${item.total_sales:,.2f}",
                str(item.total_orders),
                f"${item.average_order_value:,.2f}"
            ])
        
        details_table = Table(details_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        
        elements.append(details_table)
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def export_product_report_to_pdf(products: List[schemas.ProductReportItem]) -> io.BytesIO:
        """
        Exporta un reporte de productos a formato PDF.
        
        Args:
            products: Lista de productos a exportar
            
        Returns:
            BytesIO: Buffer con el contenido del archivo PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Título
        elements.append(Paragraph('REPORTE DE PRODUCTOS', title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Fecha de generación
        generation_date = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(generation_date, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de productos (primeros 30 para no sobrecargar)
        products_data = [['ID', 'Nombre', 'Categoría', 'Vendidos', 'Ingresos', 'Stock', 'Rating']]
        
        for product in products[:30]:
            products_data.append([
                str(product.product_id),
                product.name[:30] + '...' if len(product.name) > 30 else product.name,
                product.category[:15] if product.category else 'N/A',
                str(product.total_sold),
                f"${product.revenue:,.0f}",
                str(product.current_stock),
                f"{product.average_rating:.1f}" if product.average_rating else "N/A"
            ])
        
        products_table = Table(products_data, colWidths=[0.5*inch, 2*inch, 1*inch, 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch])
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (1, 1), (1, -1), 'LEFT')
        ]))
        
        elements.append(products_table)
        
        if len(products) > 30:
            note = Paragraph(f"<i>Nota: Mostrando los primeros 30 de {len(products)} productos</i>", styles['Normal'])
            elements.append(Spacer(1, 0.2*inch))
            elements.append(note)
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer