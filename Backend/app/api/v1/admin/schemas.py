# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Schemas de validación y serialización para el módulo de administración.
#              Define las estructuras de datos para operaciones administrativas en lote.

from pydantic import BaseModel, Field
from typing import List


# ============ GESTIÓN DE PRODUCTOS ============

class BulkProductAction(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema para realizar acciones en lote sobre múltiples productos.
                 Permite activar, desactivar o eliminar varios productos simultáneamente.
    """
    product_ids: List[int] = Field(..., description="Lista de IDs de productos a procesar")
    action: str = Field(
        ..., 
        pattern="^(activate|deactivate|delete)$",
        description="Acción a realizar: 'activate', 'deactivate' o 'delete'"
    )


class BulkActionResponse(BaseModel):
    """
    Autor: Luis Flores
    Descripción: Schema de respuesta para operaciones en lote.
                 Indica cuántos productos se procesaron exitosamente y cuántos fallaron.
    """
    success: int = Field(..., description="Cantidad de productos procesados exitosamente")
    failed: int = Field(..., description="Cantidad de productos que fallaron")
    errors: List[str] = Field(
        default=[],
        description="Lista de mensajes de error para productos que fallaron"
    )