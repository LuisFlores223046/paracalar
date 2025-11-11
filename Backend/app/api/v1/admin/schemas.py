from pydantic import BaseModel, Field
from typing import List


# ============ GESTIÓN DE PRODUCTOS ============
class BulkProductAction(BaseModel):
    """Acción en lote sobre productos"""
    product_ids: List[int]
    action: str = Field(..., pattern="^(activate|deactivate|delete)$")


class BulkActionResponse(BaseModel):
    """Respuesta de acción en lote"""
    success: int
    failed: int
    errors: List[str] = []