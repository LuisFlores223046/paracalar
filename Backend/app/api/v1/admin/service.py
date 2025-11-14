# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Servicios de lógica de negocio para operaciones administrativas.
#              Implementa funcionalidades para gestión masiva de productos.

from sqlalchemy.orm import Session

from app.models.product import Product
from app.api.v1.admin import schemas


class AdminProductService:
    """
    Autor: Luis Flores
    Descripción: Clase de servicio para operaciones administrativas de productos.
                 Contiene métodos estáticos para gestión masiva y operaciones
                 que requieren permisos de administrador.
    """
    
    @staticmethod
    def bulk_update_products(
        db: Session,
        action_data: schemas.BulkProductAction
    ) -> schemas.BulkActionResponse:
        """
        Autor: Luis Flores
        Descripción: Realiza operaciones en lote sobre múltiples productos.
                     Procesa cada producto individualmente y registra éxitos y errores.
                     Acciones soportadas: activate, deactivate, delete.
        Parámetros:
            db (Session): Sesión de base de datos.
            action_data (BulkProductAction): Contiene lista de product_ids y acción a realizar.
        Retorna:
            BulkActionResponse: Objeto con contadores de success y failed, 
                                más lista de mensajes de error.
        """
        success = 0
        failed = 0
        errors = []
        
        for product_id in action_data.product_ids:
            try:
                product = db.query(Product).filter(
                    Product.product_id == product_id
                ).first()
                
                if not product:
                    errors.append(f"Producto {product_id} no encontrado")
                    failed += 1
                    continue
                
                if action_data.action == "activate":
                    product.is_active = True
                elif action_data.action == "deactivate":
                    product.is_active = False
                elif action_data.action == "delete":
                    db.delete(product)
                
                success += 1
            except Exception as e:
                errors.append(f"Error en producto {product_id}: {str(e)}")
                failed += 1
        
        db.commit()
        
        return schemas.BulkActionResponse(
            success=success,
            failed=failed,
            errors=errors
        )