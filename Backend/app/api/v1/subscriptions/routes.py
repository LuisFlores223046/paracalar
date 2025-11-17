# Autor: Luis Flores y Lizbeth Barajas
# Fecha: 17/11/2025
# Descripción: Rutas API para gestión de suscripciones mensuales.
#              Define todos los endpoints REST para operaciones de suscripción.

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.api.v1.subscriptions import schemas
from app.api.v1.subscriptions.service import subscription_service
from app.models.user import User

router = APIRouter()


@router.post(
    "/create",
    response_model=schemas.SubscriptionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_subscription(
    subscription_data: schemas.CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Crea una nueva suscripción mensual para el usuario autenticado.
                 Valida que el usuario tenga un perfil fitness completo y método de pago.
                 Realiza el primer cobro inmediatamente.
    Parámetros:
        subscription_data (CreateSubscriptionRequest): Datos para crear la suscripción.
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        SubscriptionResponse: Información completa de la suscripción creada.
    Excepciones:
        HTTPException 400: Si el usuario no cumple requisitos o hay error en el cobro.
    
    Requisitos:
    - Usuario debe tener un Fitness Profile completo (test de posicionamiento)
    - Debe tener un método de pago guardado (tarjeta)
    - No puede tener otra suscripción activa
    
    El primer cobro se realiza inmediatamente al crear la suscripción.
    """
    result = subscription_service.create_subscription(
        db=db,
        user_id=current_user.user_id,
        payment_method_id=subscription_data.payment_method_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    subscription = result["subscription"]
    
    # Obtener info adicional para la respuesta
    plan_name = None
    if subscription.fitness_profile and subscription.fitness_profile.attributes:
        plan_name = subscription.fitness_profile.attributes.get("recommended_plan")
    
    payment_last_four = None
    if subscription.payment_method:
        payment_last_four = subscription.payment_method.last_four
    
    return schemas.SubscriptionResponse(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        profile_id=subscription.profile_id,
        payment_method_id=subscription.payment_method_id,
        subscription_status=subscription.subscription_status.value,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        next_delivery_date=subscription.next_delivery_date,
        auto_renew=subscription.auto_renew,
        price=subscription.price,
        last_payment_date=subscription.last_payment_date,
        failed_payment_attempts=subscription.failed_payment_attempts,
        plan_name=plan_name,
        payment_method_last_four=payment_last_four
    )


@router.get(
    "/my-subscription",
    response_model=schemas.SubscriptionResponse
)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Obtiene la suscripción actual del usuario autenticado con toda su información.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        SubscriptionResponse: Información completa de la suscripción del usuario.
    Excepciones:
        HTTPException 404: Si el usuario no tiene suscripción activa.
        HTTPException 400: Si ocurre un error al consultar la suscripción.
    
    Retorna toda la información de la suscripción incluyendo:
    - Estado actual
    - Próxima fecha de entrega
    - Método de pago asociado
    - Plan fitness asignado
    """
    result = subscription_service.get_user_subscription(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    if not result.get("has_subscription"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una suscripción activa"
        )
    
    subscription = result["subscription"]
    
    return schemas.SubscriptionResponse(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        profile_id=subscription.profile_id,
        payment_method_id=subscription.payment_method_id,
        subscription_status=subscription.subscription_status.value,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        next_delivery_date=subscription.next_delivery_date,
        auto_renew=subscription.auto_renew,
        price=subscription.price,
        last_payment_date=subscription.last_payment_date,
        failed_payment_attempts=subscription.failed_payment_attempts,
        plan_name=result.get("plan_name"),
        payment_method_last_four=result.get("payment_last_four")
    )


@router.get(
    "/summary",
    response_model=schemas.SubscriptionSummary
)
def get_subscription_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Obtiene un resumen rápido del estado de suscripción del usuario.
                 Endpoint optimizado para mostrar en headers o dashboards.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        SubscriptionSummary: Resumen con información básica de la suscripción.
                            Si no tiene suscripción, retorna is_active=False.
    
    Útil para mostrar en el header o dashboard sin cargar toda la información.
    """
    result = subscription_service.get_user_subscription(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success") or not result.get("has_subscription"):
        return schemas.SubscriptionSummary(
            is_active=False,
            subscription_status=None,
            next_delivery_date=None,
            price=None
        )
    
    subscription = result["subscription"]
    
    return schemas.SubscriptionSummary(
        is_active=subscription.subscription_status.value == "active",
        subscription_status=subscription.subscription_status.value,
        next_delivery_date=subscription.next_delivery_date,
        price=subscription.price
    )


@router.patch(
    "/pause",
    response_model=schemas.MessageResponse
)
def pause_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Pausa la suscripción activa del usuario.
                 Durante el pausado no se realizarán cobros ni envíos.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        MessageResponse: Mensaje de confirmación de la operación.
    Excepciones:
        HTTPException 400: Si no se encuentra suscripción activa o hay error.
    
    Mientras esté pausada:
    - No se realizarán cobros
    - No se enviarán productos
    - Se puede reanudar en cualquier momento
    """
    result = subscription_service.pause_subscription(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return schemas.MessageResponse(
        success=True,
        message=result.get("message")
    )


@router.patch(
    "/resume",
    response_model=schemas.MessageResponse
)
def resume_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Reanuda una suscripción pausada, reactivando el ciclo de cobros y envíos.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        MessageResponse: Mensaje de confirmación de la operación.
    Excepciones:
        HTTPException 400: Si no se encuentra suscripción pausada o hay error.
    
    La suscripción volverá a su ciclo normal de cobros y envíos.
    """
    result = subscription_service.resume_subscription(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return schemas.MessageResponse(
        success=True,
        message=result.get("message")
    )


@router.delete(
    "/cancel",
    response_model=schemas.MessageResponse
)
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Cancela permanentemente la suscripción del usuario.
                 Esta es una acción definitiva que requiere crear una nueva suscripción
                 para reactivar el servicio.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        MessageResponse: Mensaje de confirmación de la cancelación.
    Excepciones:
        HTTPException 400: Si no se encuentra suscripción o hay error.
    
    **IMPORTANTE**: Esta acción es permanente.
    El usuario deberá crear una nueva suscripción si desea reactivar el servicio.
    """
    result = subscription_service.cancel_subscription(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return schemas.MessageResponse(
        success=True,
        message=result.get("message")
    )


@router.put(
    "/payment-method",
    response_model=schemas.MessageResponse
)
def update_subscription_payment_method(
    update_data: schemas.UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Actualiza el método de pago asociado a la suscripción activa.
    Parámetros:
        update_data (UpdateSubscriptionRequest): Datos con el nuevo payment_method_id.
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        MessageResponse: Mensaje de confirmación de la actualización.
    Excepciones:
        HTTPException 400: Si el método de pago no es válido o hay error.
    
    El nuevo método de pago debe:
    - Pertenecer al usuario
    - Ser una tarjeta guardada válida
    """
    result = subscription_service.update_payment_method(
        db=db,
        user_id=current_user.user_id,
        new_payment_method_id=update_data.payment_method_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return schemas.MessageResponse(
        success=True,
        message=result.get("message")
    )


@router.get(
    "/history",
    response_model=schemas.SubscriptionHistoryResponse
)
def get_subscription_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores y Lizbeth Barajas
    Descripción: Obtiene el historial completo de órdenes de la suscripción del usuario.
                 Incluye todas las órdenes generadas, totales y detalles de envío.
    Parámetros:
        current_user (User): Usuario autenticado obtenido del token JWT.
        db (Session): Sesión de base de datos inyectada.
    Retorna:
        SubscriptionHistoryResponse: Historial completo con suscripción y todas sus órdenes.
    Excepciones:
        HTTPException 400: Si no se encuentra suscripción o hay error.
    
    Incluye:
    - Todas las órdenes generadas por la suscripción
    - Total gastado
    - Detalles de cada entrega
    """
    result = subscription_service.get_subscription_history(
        db=db,
        user_id=current_user.user_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    subscription = result["subscription"]
    orders = result["orders"]
    
    # Preparar info de suscripción
    plan_name = None
    if subscription.fitness_profile and subscription.fitness_profile.attributes:
        plan_name = subscription.fitness_profile.attributes.get("recommended_plan")
    
    payment_last_four = None
    if subscription.payment_method:
        payment_last_four = subscription.payment_method.last_four
    
    subscription_response = schemas.SubscriptionResponse(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        profile_id=subscription.profile_id,
        payment_method_id=subscription.payment_method_id,
        subscription_status=subscription.subscription_status.value,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        next_delivery_date=subscription.next_delivery_date,
        auto_renew=subscription.auto_renew,
        price=subscription.price,
        last_payment_date=subscription.last_payment_date,
        failed_payment_attempts=subscription.failed_payment_attempts,
        plan_name=plan_name,
        payment_method_last_four=payment_last_four
    )
    
    # Preparar historial de órdenes
    orders_response = [
        schemas.SubscriptionOrderHistory(
            order_id=order.order_id,
            order_date=order.order_date.date(),
            total_amount=order.total_amount,
            order_status=order.order_status.value,
            tracking_number=order.tracking_number
        )
        for order in orders
    ]
    
    return schemas.SubscriptionHistoryResponse(
        subscription=subscription_response,
        orders=orders_response,
        total_orders=result["total_orders"],
        total_spent=result["total_spent"]
    )