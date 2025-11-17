# Autor: Gabriel Vilchis
# Fecha 14/11/2025
# Descripcion:
# Este codigo contiene la lógica de negocio (servicios) para obtener y calcular
# todas las métricas, estadísticas y reportes utilizados en el dashboard administrativo
# y los endpoints de analíticas. Utiliza SQLAlchemy para interactuar con la base de datos.
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional
from datetime import datetime, timedelta, date
import io, csv
# Imports de reportlab - TODOS AL INICIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    Autor: Gabriel Vilchis
    Esta clase de servicio encapsula la logica de negocio para la obtencion y el calculo de 
    estadisticas y reportes de la tienda, utilizando consultas SQLAlchemy
    """
    @staticmethod
    def get_dashboard_stats(db: Session) -> schemas.AdminDashboardStats:
        """
        Autor: Gabriel Vilchis
        Obtiene todas las estadísticas para el dashboard del admin
        Args:
            db: Sesión de SQLAlchemy para la conexión a la base de datos.

        Returns:
            AdminDashboardStats: Un objeto AdminDashboardStats con todas las mé
        """
        sales_stats = AnalyticsService._get_sales_stats(db)
        user_stats = AnalyticsService._get_user_stats(db)
        subscription_stats = AnalyticsService._get_subscription_stats(db)
        
        total_products = db.query(Product).filter(Product.is_active == True).count()
        low_stock_products = db.query(Product).filter(
            and_(Product.is_active == True, Product.stock < 10)
        ).count()
        
        # Producto más vendido
        top_product = AnalyticsService._get_top_product(db)
        
        # Resumen de hoy
        today_summary = AnalyticsService._get_today_summary(db)
        
        # Datos para gráficas
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
        """
        Autor: Gabriel Vilchis
        Método auxiliar para calcular las métricas globales de ventas y el top 10 de productos vendidos.

        Args:
            db: Sesión de SQLAlchemy.

        Returns:
            SalesStats: Un objeto SalesStats con los totales de ventas, órdenes y el top de productos.
        """
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
                total_reviews=0  # Puedes agregar esto si tienes reviews
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
        """
        Autor: Gabriel Vilchis
        Método auxiliar para calcular las métricas clave de la base de usuarios.

        Args:
            db: Sesión de SQLAlchemy.

        Returns:
            UserStats: Un objeto UserStats con el total de usuarios, activos, nuevos del mes y con órdenes.
        """
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
        """
        Autor: Gabriel Vilchis
        Obtiene y calcula las métricas principales relacionadas con las
        suscripciones de la plataforma.

        Args:
            db (Session): Sesión de SQLAlchemy para ejecutar consultas a la base de datos.

        Returns:
            SubscriptionStats: Objeto que contiene el total de suscripciones,
            suscripciones activas, pausadas, canceladas, nuevas del mes y
            los ingresos generados por suscripciones activas.
        """

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
        
        # Calcular ingresos de suscripciones activas
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
        """
        Autor: Gabriel Vilchis
        Obtiene el producto más vendido en los últimos 30 días,
        incluyendo cantidad vendida, ingresos generados e imagen principal.

        Args:
            db (Session): Sesión de SQLAlchemy para operaciones de consulta.

        Returns:
            Optional[TopProduct]: Información del producto más vendido.
            Retorna None si no hay registros de ventas recientes.
        """
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
        
        # Obtener imagen del producto
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
        """
        Autor: Gabriel Vilchis
        Genera un resumen de métricas correspondientes al día actual,
        incluyendo ventas, órdenes, productos vendidos y nuevas suscripciones.

        Args:
            db (Session): Sesión de SQLAlchemy.

        Returns:
            TodaySummary: Objeto con ventas totales del día, número de órdenes,
            productos vendidos y suscripciones nuevas.
        """
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
        """
        Autor: Gabriel Vilchis
        Calcula las ventas y número de órdenes para los últimos N meses.

        Args:
            db (Session): Sesión de SQLAlchemy.
            months (int, opcional): Cantidad de meses a analizar. Default = 6.

        Returns:
            List[MonthlySalesData]: Lista con los registros mensuales de ventas y órdenes.
        """
        result = []
        
        for i in range(months - 1, -1, -1):
            # Calcular fecha del mes
            target_date = datetime.now() - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            # Query para ese mes
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
            
            # Nombre del mes en español
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
        """
        Autor: Gabriel Vilchis
        Obtiene las ventas agrupadas por categoría, incluyendo ingresos,
        cantidad de productos vendidos y porcentaje sobre el total de ventas.

        Args:
            db (Session): Sesión de SQLAlchemy.

        Returns:
            List[CategorySalesData]: Lista de categorías con métricas calculadas.
        """
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
        
        # Calcular total para porcentajes
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
        """
        Autor: Gabriel Vilchis
        Calcula el crecimiento mensual de suscriptores para los últimos N meses,
        incluyendo nuevos suscriptores y total de activos.

        Args:
            db (Session): Sesión de SQLAlchemy.
            months (int, opcional): Cantidad de meses a considerar. Default = 6.

        Returns:
            List[SubscriberGrowthData]: Lista con datos de crecimiento de suscriptores.
        """
        result = []
        
        for i in range(months - 1, -1, -1):
            # Calcular fecha del mes
            target_date = datetime.now() - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            # Primer y último día del mes
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            
            # Nuevos suscriptores ese mes
            new_subs = db.query(Subscription).filter(
                and_(
                    Subscription.start_date >= first_day,
                    Subscription.start_date <= last_day
                )
            ).count()
            
            # Total activos al final del mes
            total_active = db.query(Subscription).filter(
                and_(
                    Subscription.start_date <= last_day,
                    Subscription.subscription_status == SubscriptionStatus.ACTIVE
                )
            ).count()
            
            # Nombre del mes
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
        Autor: Gabriel Vilchis
        Genera un reporte detallado de ventas dentro de un período específico,
        incluyendo resumen estadístico y ventas por día.

        Args:
            db (Session): Sesión de SQLAlchemy.
            start_date (datetime, opcional): Fecha inicial del período. Si no se
                proporciona, se toman los últimos 30 días.
            end_date (datetime, opcional): Fecha final del período. Default = fecha actual.

        Returns:
            SalesReport: Reporte completo con resumen y detalle diario.
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
        Autor: Gabriel Vilchis
        Genera un reporte de productos que muestra ventas, ingresos, stock actual
        y calificación promedio dentro del período solicitado.

        Args:
            db (Session): Sesión de SQLAlchemy.
            start_date (datetime, opcional): Inicio del rango del reporte.
            end_date (datetime, opcional): Fin del rango del reporte.

        Returns:
            List[ProductReportItem]: Lista con métricas por producto.
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
        Autor: Gabriel Vilchis
        Obtiene los productos cuyo inventario está por debajo del umbral definido.

        Args:
            db (Session): Sesión de SQLAlchemy.
            threshold (int, opcional): Valor mínimo de stock para considerar un producto
                como bajo en inventario. Default = 10.

        Returns:
            List[Product]: Lista de productos con stock por debajo del umbral.
        """
        return db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.stock < threshold
            )
        ).order_by(Product.stock.asc()).all()
    
class ReportExportService:
    """Servicio para generación de reportes y exportación de datos"""
    
    @staticmethod
    def export_sales_report_to_csv(sales_report: schemas.SalesReport) -> io.BytesIO:
        """
        Autor: Gabriel Vilchis
        Exporta un reporte de ventas al formato CSV, incluyendo el encabezado,
        resumen ejecutivo y el detalle diario.

        Args:
            sales_report (SalesReport): Objeto con la información del reporte.

        Returns:
            BytesIO: Archivo CSV en memoria listo para descargar o enviar.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados del reporte
        writer.writerow(['REPORTE DE VENTAS'])
        writer.writerow(['Período', f"{sales_report.start_date.strftime('%Y-%m-%d')} a {sales_report.end_date.strftime('%Y-%m-%d')}"])
        writer.writerow([])
        
        # Resumen
        writer.writerow(['RESUMEN'])
        writer.writerow(['Total Ventas', f"${sales_report.summary['total_sales']:,.2f}"])
        writer.writerow(['Total Órdenes', sales_report.summary['total_orders']])
        writer.writerow(['Ticket Promedio', f"${sales_report.summary['average_order_value']:,.2f}"])
        writer.writerow(['Días en Período', sales_report.summary['days_in_period']])
        writer.writerow([])
        
        # Detalle por día
        writer.writerow(['DETALLE DIARIO'])
        writer.writerow(['Fecha', 'Ventas Totales', 'Órdenes', 'Ticket Promedio'])
        
        for item in sales_report.details:
            writer.writerow([
                item.date.strftime('%Y-%m-%d'),
                f"${item.total_sales:,.2f}",
                item.total_orders,
                f"${item.average_order_value:,.2f}"
            ])
        
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        
        return bytes_output
    
    @staticmethod
    def export_sales_report_to_pdf(sales_report: schemas.SalesReport) -> io.BytesIO:
        """
        Autor: Gabriel Vilchis
        Genera un archivo PDF estilizado con el contenido del reporte de ventas,
        incluyendo título, período, resumen y tabla detallada.

        Args:
            sales_report (SalesReport): Reporte a exportar en PDF.

        Returns:
            BytesIO: Archivo PDF generado en memoria.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        title = Paragraph("Reporte de Ventas", title_style)
        elements.append(title)
        
        # Período
        period_style = ParagraphStyle(
            'Period',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4b5563'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        period_text = f"{sales_report.start_date.strftime('%d/%m/%Y')} - {sales_report.end_date.strftime('%d/%m/%Y')}"
        period = Paragraph(period_text, period_style)
        elements.append(period)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de resumen
        summary_data = [
            ['RESUMEN EJECUTIVO'],
            ['Total Ventas', f"${sales_report.summary['total_sales']:,.2f}"],
            ['Total Órdenes', str(sales_report.summary['total_orders'])],
            ['Ticket Promedio', f"${sales_report.summary['average_order_value']:,.2f}"],
            ['Días Analizados', str(sales_report.summary['days_in_period'])]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Tabla de detalles
        detail_data = [['Fecha', 'Ventas', 'Órdenes', 'Ticket Promedio']]
        
        for item in sales_report.details:
            detail_data.append([
                item.date.strftime('%d/%m/%Y'),
                f"${item.total_sales:,.2f}",
                str(item.total_orders),
                f"${item.average_order_value:,.2f}"
            ])
        
        detail_table = Table(detail_data, colWidths=[1.5*inch, 1.8*inch, 1.3*inch, 1.8*inch])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
        ]))
        
        elements.append(detail_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def export_product_report_to_csv(products: List[schemas.ProductReportItem]) -> io.BytesIO:
        """
        Autor: Gabriel Vilchis
        Exporta un reporte de ventas al formato CSV, incluyendo el encabezado,
        resumen ejecutivo y el detalle diario.

        Args:
            sales_report (SalesReport): Objeto con la información del reporte.

        Returns:
            BytesIO: Archivo CSV en memoria listo para descargar o enviar.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['REPORTE DE PRODUCTOS'])
        writer.writerow([])
        writer.writerow(['ID', 'Nombre', 'Categoría', 'Vendidos', 'Ingresos', 'Stock', 'Rating'])
        
        # Datos
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
        
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        
        return bytes_output
    
    @staticmethod
    def export_product_report_to_pdf(products: List[schemas.ProductReportItem]) -> io.BytesIO:
        """
        Autor: Gabriel Vilchis
        Genera un archivo PDF estilizado con el contenido del reporte de ventas,
        incluyendo título, período, resumen y tabla detallada.

        Args:
            sales_report (SalesReport): Reporte a exportar en PDF.

        Returns:
            BytesIO: Archivo PDF generado en memoria.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        title = Paragraph("Reporte de Productos", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de productos
        data = [['ID', 'Nombre', 'Categoría', 'Vendidos', 'Ingresos', 'Stock', 'Rating']]
        
        for product in products:
            data.append([
                str(product.product_id),
                product.name[:30] + '...' if len(product.name) > 30 else product.name,
                product.category,
                str(product.total_sold),
                f"${product.revenue:,.2f}",
                str(product.current_stock),
                f"{product.average_rating:.1f}" if product.average_rating else "N/A"
            ])
        
        table = Table(data, colWidths=[0.5*inch, 2.5*inch, 1.3*inch, 0.9*inch, 1.2*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer