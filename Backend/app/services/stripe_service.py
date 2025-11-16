# Autor: Lizbeth Barajas y Gabriel Vilchis
# Fecha: 13-11-25
# Descripción: Servicio para integración con Stripe. Maneja sesiones de pago,
#              creación de clientes, intents de setup, cobros con tarjeta guardada,
#              métodos de pago, webhooks y más.

import stripe
from typing import Dict, Optional
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    
    def create_checkout_session(
        self,
        amount: int,
        currency: str,
        product_name: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Autor: Gabriel Vilchis

        Descripción:
            Crea una sesión de Stripe Checkout para pagos por redirección. 
            Recibe datos del producto y URLs de éxito/cancelación para el flujo de pago.

        Parámetros:
            amount (int): Monto total en centavos.
            currency (str): Moneda (ej. "mxn").
            product_name (str): Nombre del producto o servicio.
            success_url (str): URL a redirigir después de un pago exitoso.
            cancel_url (str): URL a redirigir si el usuario cancela el pago.
            metadata (dict, opcional): Metadatos adicionales a adjuntar.

        Retorna:
            dict: ID de la sesión y URL del checkout, o None en caso de error.
        """
        try:
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': product_name,
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
            }
            
            if metadata:
                session_params['metadata'] = metadata
            
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                'id': session.id,
                'url': session.url
            }
        except stripe.error.StripeError as e:
            print(f"Stripe error creating checkout session: {str(e)}")
            return None
        except Exception as e:
            print(f"Error creating checkout session: {str(e)}")
            return None
    
    def get_or_create_customer(self, user_id: int, email: str, name: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Obtiene un cliente existente en Stripe por correo o crea uno nuevo.
            Esto permite asociar métodos de pago y cobros al usuario del sistema.

        Parámetros:
            user_id (int): ID interno del usuario.
            email (str): Correo del usuario.
            name (str): Nombre del usuario.

        Retorna:
            dict: Estado de la operación y el customer_id en Stripe.
        """
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata={'user_id': str(user_id)}
                )
            
            return {
                'success': True,
                'customer_id': customer.id
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_setup_intent(self, customer_id: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Crea un Setup Intent para permitir al usuario registrar una tarjeta 
            sin realizar un cobro. Se utiliza para guardar métodos de pago futuros.

        Parámetros:
            customer_id (str): ID del cliente en Stripe.

        Retorna:
            dict: Client secret y ID del setup intent.
        """
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session',
            )
            
            return {
                'success': True,
                'client_secret': setup_intent.client_secret,
                'setup_intent_id': setup_intent.id
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_method(self, payment_method_id: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Recupera detalles de un método de pago previamente guardado en Stripe.

        Parámetros:
            payment_method_id (str): ID del método de pago (pm_xxx).

        Retorna:
            dict: Información del método de pago o error.
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            
            return {
                'success': True,
                'payment_method': {
                    'id': payment_method.id,
                    'type': payment_method.type,
                    'card': {
                        'brand': payment_method.card.brand,
                        'last4': payment_method.card.last4,
                        'exp_month': payment_method.card.exp_month,
                        'exp_year': payment_method.card.exp_year,
                        'funding': payment_method.card.funding
                    }
                }
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment_intent_with_saved_card(
        self,
        amount: int,
        currency: str,
        customer_id: str,
        payment_method_id: str,
        description: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Crea y confirma un Payment Intent utilizando una tarjeta ya guardada.
            Esto permite realizar cobros sin interacción del usuario.

        Parámetros:
            amount (int): Monto en centavos.
            currency (str): Moneda (ej. "mxn").
            customer_id (str): ID del cliente.
            payment_method_id (str): ID del método de pago guardado.
            description (str): Descripción opcional del pago.
            metadata (dict): Datos adicionales opcionales.

        Retorna:
            dict: Resultado del pago y estatus final.
        """
        try:
            payment_intent_params = {
                'amount': amount,
                'currency': currency,
                'customer': customer_id,
                'payment_method': payment_method_id,
                'off_session': True,
                'confirm': True,
            }
            
            if description:
                payment_intent_params['description'] = description
            
            if metadata:
                payment_intent_params['metadata'] = metadata
            
            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)
            
            if payment_intent.status == 'succeeded':
                return {
                    'success': True,
                    'payment_intent_id': payment_intent.id,
                    'status': 'succeeded'
                }
            elif payment_intent.status == 'requires_action':
                return {
                    'success': False,
                    'requires_action': True,
                    'client_secret': payment_intent.client_secret,
                    'payment_intent_id': payment_intent.id
                }
            else:
                return {
                    'success': False,
                    'error': f'Payment status: {payment_intent.status}'
                }
                
        except stripe.error.CardError as e:
            return {
                'success': False,
                'error': e.user_message or str(e)
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_customer_payment_methods(self, customer_id: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Lista todas las tarjetas guardadas asociadas a un cliente.

        Parámetros:
            customer_id (str): ID del cliente en Stripe.

        Retorna:
            dict: Lista de métodos de pago.
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            cards = []
            for pm in payment_methods.data:
                cards.append({
                    'id': pm.id,
                    'brand': pm.card.brand,
                    'last4': pm.card.last4,
                    'exp_month': pm.card.exp_month,
                    'exp_year': pm.card.exp_year
                })
            
            return {
                'success': True,
                'payment_methods': cards
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def detach_payment_method(self, payment_method_id: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Desvincula un método de pago de un cliente, eliminándolo de Stripe.

        Parámetros:
            payment_method_id (str): ID del método de pago.

        Retorna:
            dict: Estado de la operación.
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            
            return {
                'success': True,
                'message': 'Payment method removed'
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def retrieve_session(self, session_id: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Recupera una sesión de checkout por ID. Usado normalmente en webhooks.

        Parámetros:
            session_id (str): ID de la sesión.

        Retorna:
            dict: Objeto de la sesión o None.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            print(f"Stripe error retrieving session: {str(e)}")
            return None
        except Exception as e:
            print(f"Error retrieving session: {str(e)}")
            return None
    
    def construct_webhook_event(self, payload: str, signature: str, secret: str):
        """
        Autor: Lizbeth Barajas

        Descripción:
            Verifica la firma y construye un evento de webhook de Stripe para asegurar 
            que realmente proviene de Stripe.

        Parámetros:
            payload (str): Cuerpo original de la petición.
            signature (str): Header stripe-signature.
            secret (str): Webhook signing secret.

        Retorna:
            event: Evento verificado.

        Excepciones:
            ValueError: Si el payload o firma no son válidos.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, secret
            )
            return event
        except ValueError as e:
            raise ValueError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {str(e)}")
    
    def charge_saved_card(
        self,
        customer_id: str,
        amount: int,
        currency: str,
        description: str
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Realiza un cobro utilizando la tarjeta predeterminada del cliente.
            Se usa normalmente en cobros automáticos o renovaciones.

        Parámetros:
            customer_id (str): ID del cliente en Stripe.
            amount (int): Monto en centavos.
            currency (str): Moneda del cobro.
            description (str): Descripción del cargo.

        Retorna:
            dict: Resultado del pago.
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            default_payment_method = customer.invoice_settings.default_payment_method
            
            if not default_payment_method:
                return {
                    'success': False,
                    'error': 'No default payment method found'
                }
            
            return self.create_payment_intent_with_saved_card(
                amount=amount,
                currency=currency,
                customer_id=customer_id,
                payment_method_id=default_payment_method,
                description=description
            )
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': f"Stripe error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

stripe_service = StripeService()
