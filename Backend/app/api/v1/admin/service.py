from sqlalchemy.orm import Session

from app.models.product import Product
from app.api.v1.admin import schemas


class AdminProductService:
    """Servicio para operaciones administrativas de productos"""
    
    @staticmethod
    def bulk_update_products(
        db: Session,
        action_data: schemas.BulkProductAction
    ) -> schemas.BulkActionResponse:
        """
        Realiza operaciones en lote sobre productos
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