# Autor: Gabriel Vilchis
# Fecha: 13-11-25
# Descripción: Servicio para la integración con PayPal, incluyendo autenticación,
#              creación de órdenes y captura de pagos.

import httpx
from app.config import settings
from base64 import b64encode

class PaypalService:
    def __init__(self):
        # configuraciones de paypal
        self.base_url = settings.PAYPAL_API_BASE_URL # esta en sandbox
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.client = httpx.AsyncClient()
        self.access_token = None

    def get_auth_header(self):
        """
        Autor: Gabriel Vilchis

        Descripción: Genera el encabezado de autenticación en Base64 requerido por PayPal
                     para solicitar el token de acceso OAuth2.

        Parámetros: Ninguno.

        Retorna:
            str: Cadena de autenticación en formato 'Basic <base64string>'.
        """
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = b64encode(auth_str.encode()).decode()
        return f"Basic {encoded_auth}"
    
    async def get_access_token(self):
        """
        Autor: Gabriel Vilchis

        Descripción: Solicita a PayPal un token de acceso OAuth2 utilizando las credenciales
                     del cliente. El token se almacena internamente para futuras peticiones.

        Parámetros: Ninguno.

        Retorna:
            str: Token de acceso proporcionado por PayPal.
        """
        token_url = f"{self.base_url}/v1/oauth2/token"

        headers = {
            "Authorization": self.get_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        response = await self.client.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data.get("access_token")

        return self.access_token
    
    async def create_order(self, amount: float, currency: str = "MXN", return_url: str = None, cancel_url: str = None):
        """
        Autor: Gabriel Vilchis

        Descripción: Crea una orden de pago en PayPal con el monto, moneda y URLs de retorno
                     especificadas, iniciando el proceso de checkout para el usuario.

        Parámetros:
            amount (float): Monto total de la orden.
            currency (str): Código de la moneda en formato ISO-4217.
            return_url (str): URL a la que PayPal redirige después de aprobar la orden.
            cancel_url (str): URL a la que PayPal redirige si el usuario cancela el proceso.

        Retorna:
            dict: Información de la orden creada, proveniente de PayPal.
        """
        token = await self.get_access_token()

        order_url = f"{self.base_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        return_url = return_url or f"{settings.APP_URL}/success"
        #cancel_url = cancel_url or f"{settings.APP_URL}/cancel"
        cancel_url = f"{settings.APP_URL}/checkout" # lo debe redirigir a la pagina de compra/pagos

        body = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}"
                }
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }

        response = await self.client.post(order_url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    
    async def capture_order(self, order_id: str):
        """
        Autor: Gabriel Vilchis

        Descripción: Captura el pago de una orden previamente aprobada por el usuario en PayPal,
                     finalizando la transacción.

        Parámetros:
            order_id (str): Identificador de la orden que se desea capturar.

        Retorna:
            dict: Datos de la captura del pago devueltos por PayPal.
        """
        token = await self.get_access_token()

        capture_url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = await self.client.post(capture_url, headers=headers)
        response.raise_for_status()

        return response.json()
    
# instancia de uso
paypal_service = PaypalService()
