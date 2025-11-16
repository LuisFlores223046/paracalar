# Autor: Gabriel Vilchis
# Fecha: 12/11/2025
# Descripción: Este archivo define los endpoints de la API relacionados con la gestión
# de pedidos y el seguimiento de envíos (shipping). Incluye funcionalidades para crear
# nuevas órdenes de compra y consultar el estado actual de los pedidos para rastreo.

from app.core.database import get_db
from app.api.v1.shipping.schemas import Order, CreateOrder, OrderTrackingResponse
from app.api.v1.shipping.service import ShippingService
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, status, Depends

router = APIRouter(prefix="/shipping", tags=["Shipping"])

@router.post("/crear-pedido/", response_model=Order, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido_in: CreateOrder, db: Session = Depends(get_db)):
    """
    Autor: Gabriel Vilchis
    Crea una nueva orden de compra en el sistema (un pedido con sus respectivos items).

    Esta función recibe los detalles de la orden (usuario, dirección y pago) y 
    utiliza el servicio de envío para procesar la creación de la orden en la base de datos.

    Args:
        pedido_in (`CreateOrder`): Esquema de Pydantic con `user_id`, `address_id` y `payment_id`.
        db (Session, optional): Dependencia de la sesión de base de datos.

    Raises:
        HTTPException: Si ocurre un error de validación o un error interno en el servidor.

    Returns:
        `Order`: El objeto de la orden creada, incluyendo el `order_id` y totales calculados.
    """
    
    try:
        nuevo_pedido = ShippingService.create_order_db(db=db, order_in=pedido_in)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return nuevo_pedido

@router.get("/rastrear-pedido/{pedido_id}", response_model=OrderTrackingResponse)
def rastrear_pedido( pedido_id: int, db: Session = Depends(get_db)):
    """
    Autor: Gabriel Vilchis
    Consulta el estado actual de una orden de compra específica para fines de rastreo.

    Proporciona información clave como el número de rastreo, el estado actual de la orden
    y los productos incluidos.

    Args:
        pedido_id (int): El ID único del pedido a rastrear.
        db (Session, optional): Dependencia de la sesión de base de datos.

    Raises:
        HTTPException: 404 NOT FOUND si el pedido no existe.

    Returns:
        `OrderTrackingResponse`: Detalles clave para el rastreo del pedido.
    """
    tracking_details = ShippingService.get_details(db=db, pedido_id=pedido_id)
    
    if not tracking_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Pedido no encontrado"
        )
        
    return tracking_details