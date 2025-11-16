# Autor: Lizbeth Barajas
# Fecha: 14-11-2024
# Descripción: Routes para procesamiento de pagos

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Request,
    Header
)
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.api.v1.payments import schemas
from app.api.v1.payments.service import payment_process_service
from app.services.stripe_service import stripe_service
from app.config import settings

router = APIRouter()

@router.post(
    "/summary", 
    response_model=schemas.CheckoutSummary, 
    status_code=status.HTTP_200_OK
)
async def get_checkout_summary(
    request: schemas.CheckoutSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Obtiene el resumen del checkout del usuario, incluyendo subtotal,
        envío, descuentos, total y puntos estimados. Utiliza automáticamente
        los productos del carrito del usuario y aplica el cupón si lo hay.

    Parámetros:
        request (CheckoutSummaryRequest): Datos enviados por el cliente, incluyendo address_id y cupón.
        db (Session): Sesión activa de la base de datos.
        current_user (User): Usuario autenticado que solicita el resumen.

    Retorna:
        dict: Resumen del checkout, incluyendo montos finales y desglose.
    """
    result = payment_process_service.calculate_checkout_summary(
        db=db,
        user_id=current_user.user_id,
        address_id=request.address_id,
        coupon_code=request.coupon_code
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result["summary"]

@router.post(
    "/stripe", 
    response_model=schemas.PaymentResponse, 
    status_code=status.HTTP_200_OK
)
async def create_stripe_checkout(
    checkout_data: schemas.StripeCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Crea una sesión de pago en Stripe. Puede usarse para pagos directos
        con tarjeta guardada o para redirigir al usuario al portal de Stripe Checkout.
        Maneja cupones, dirección, métodos de pago guardados y suscripciones.

    Parámetros:
        checkout_data (StripeCheckoutRequest): Información necesaria para iniciar el pago.
        db (Session): Sesión activa de base de datos.
        current_user (User): Usuario autenticado iniciando la compra.

    Retorna:
        dict: Información del checkout, como URL de Stripe o client_secret.
    """
    result = await payment_process_service.create_stripe_checkout_session(
        db=db,
        cognito_sub=current_user.cognito_sub,
        address_id=checkout_data.address_id,
        payment_method_id=checkout_data.payment_method_id,
        coupon_code=checkout_data.coupon_code,
        subscription_id=checkout_data.subscription_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result

@router.post(
    "/stripe/webhook", 
    status_code=status.HTTP_200_OK
)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Procesa los eventos enviados por Stripe mediante webhooks. Verifica la firma
        del evento para garantizar la autenticidad y maneja especialmente el evento
        'checkout.session.completed', generando la orden correspondiente y registrando
        el pago realizado.

    Parámetros:
        request (Request): Objeto con el contenido bruto del webhook.
        db (Session): Sesión activa de base de datos.
        stripe_signature (str): Firma enviada por Stripe en los headers.

    Retorna:
        dict: Confirmación de recepción del webhook.
    """
    try:
        payload = await request.body()
        
        # Verifica webhook signature
        if not stripe_signature or not hasattr(settings, 'STRIPE_WEBHOOK_SECRET'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionó firma de webhook"
            )
        
        try:
            event = stripe_service.construct_webhook_event(
                payload=payload.decode('utf-8'),
                signature=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Firma de webhook inválida: {str(e)}"
            )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Procesa el pago hecho
            result = await payment_process_service.process_stripe_webhook(
                db=db,
                session_id=session.get('id'),
                payment_intent_id=session.get('payment_intent')
            )
            
            if not result.get("success"):
                print(f"Error procesando webhook: {result.get('error')}")
        
        return {"success": True, "message": "Webhook recibido"}
    
    except Exception as e:
        print(f"Error en webhook: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post(
    "/paypal/init", 
    response_model=schemas.PaymentResponse, 
    status_code=status.HTTP_200_OK
)
async def initialize_paypal_checkout(
    paypal_data: schemas.PayPalCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Inicializa el proceso de pago con PayPal creando la orden y devolviendo
        la URL de aprobación del usuario. Soporta cupones, direcciones y suscripciones.

    Parámetros:
        paypal_data (PayPalCheckoutRequest): Información proporcionada por el cliente.
        db (Session): Sesión de base de datos.
        current_user (User): Usuario autenticado que inicia el proceso de pago.

    Retorna:
        dict: URL de aprobación de PayPal y datos del resumen.
    """
    result = await payment_process_service.initialize_paypal_checkout(
        db=db,
        cognito_sub=current_user.cognito_sub,
        address_id=paypal_data.address_id,
        coupon_code=paypal_data.coupon_code,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result


@router.post(
    "/paypal/capture", 
    response_model=schemas.PaymentResponse, 
    status_code=status.HTTP_200_OK
)
async def capture_paypal_payment(
    capture_data: schemas.PayPalCaptureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Autor: Lizbeth Barajas

    Descripción:
        Captura el pago previamente aprobado en PayPal después de que el usuario
        autoriza en la plataforma. Genera la orden en el sistema, asigna puntos y
        guarda el método de pago si corresponde.

    Parámetros:
        capture_data (PayPalCaptureRequest): Contiene paypal_order_id y address_id.
        db (Session): Sesión activa de base de datos.
        current_user (User): Usuario autenticado que completó el proceso de pago.

    Retorna:
        dict: Resultado de la captura, incluyendo datos de la orden creada.
    """
    result = await payment_process_service.capture_paypal_payment(
        db=db,
        cognito_sub=current_user.cognito_sub,
        paypal_order_id=capture_data.paypal_order_id,
        address_id=capture_data.address_id,
        coupon_code=capture_data.coupon_code,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error")
        )
    
    return result