# Autor: Lizbeth Barajas
# Fecha: 11-11-25
# Descripción: Servicio para la administración de métodos de pago de los usuarios, incluyendo tarjetas guardadas, 
#               setup intents de Stripe y configuración de tarjetas predeterminadas.

from sqlalchemy.orm import Session
from typing import Dict
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.models.enum import PaymentType
from app.services.stripe_service import stripe_service

class PaymentMethodService:
    
    def get_user_payment_methods(self, db: Session, cognito_sub: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción: Obtiene todos los metodos de pago guardados (unicamente tarjetas)

        Parámetros:
            db (Session): Sesión activa de la base de datos.
            cognito_sub (str): Identificador único del usuario en Cognito.

        Retorna:
            dict: Resultado de la operación, incluyendo lista de métodos de pago y total.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            # Solo tarjetas - para display
            payment_methods = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).all()
            
            return {
                "success": True,
                "payment_methods": payment_methods,
                "total": len(payment_methods)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener métodos de pago: {str(e)}"}
    
    def get_payment_method_by_id(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción: Obtiene un método de pago específico por su ID

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario en Cognito.
            payment_id (int): Identificador del método de pago.

        Retorna:
            dict: Resultado con la información del método de pago solicitado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            return {
                "success": True,
                "payment_method": payment_method
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener método de pago: {str(e)}"}
    
    def create_setup_intent(self, db: Session, cognito_sub: str) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción: Crea un Setup Intent en Stripe para permitir al usuario registrar una tarjeta.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador único del usuario.

        Retorna:
            dict: Client secret del Setup Intent y el ID generado por Stripe.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            email = user.email
            
            if not email: # si no fue registrado por correo lo intenta obtener en cognito
                try:
                    from app.api.v1.auth.service import cognito_service
                    cognito_user = cognito_service.get_user_info(cognito_sub)
                    email = cognito_user.get('email')
                except Exception as e:
                    print(f"Warning: No se pudo obtener email de Cognito: {str(e)}")
            
            if not email: # ya si de plano no se pudo, le genera uno (total no es relevante para el usuario)
                email = f"user_{user.user_id}@befit.internal"
                print(f"Warning: Generando email interno para user_id {user.user_id}")
         
            customer_result = stripe_service.get_or_create_customer(
                user_id=user.user_id,
                email=email,
                name=f"{user.first_name} {user.last_name}"
            )
            
            if not customer_result.get('success'):
                return customer_result
            
            customer_id = customer_result['customer_id']
            
            if not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
                db.commit()
            
            # crea setup intent
            setup_result = stripe_service.create_setup_intent(customer_id)
            
            if not setup_result.get('success'):
                return setup_result
            
            return {
                "success": True,
                "client_secret": setup_result['client_secret'],
                "setup_intent_id": setup_result['setup_intent_id']
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al crear setup intent: {str(e)}"}
    
    def save_payment_method_from_setup(
        self,
        db: Session,
        cognito_sub: str,
        payment_method_id: str,
        is_default: bool = False
    ) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Guarda un método de pago en la base de datos después de completar un Setup Intent de Stripe.
            Obtiene la información de la tarjeta desde Stripe y la almacena localmente.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario.
            payment_method_id (str): ID del método de pago generado en Stripe (pm_xxx).
            is_default (bool): Indica si la tarjeta debe quedar como predeterminada.

        Retorna:
            dict: Resultado de la operación y datos del método de pago guardado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            if not user.stripe_customer_id:
                return {"success": False, "error": "Usuario no tiene customer de Stripe"}
            
            pm_result = stripe_service.get_payment_method(payment_method_id)
            if not pm_result.get('success'):
                return pm_result
            
            pm_data = pm_result['payment_method']
            card = pm_data['card']
            
            # establece tipo de tarjeta
            funding_type = card.get('funding', 'credit')
            if funding_type == 'debit':
                payment_type = PaymentType.DEBIT_CARD
            elif funding_type == 'credit':
                payment_type = PaymentType.CREDIT_CARD
            else:
                # si no es uno de estos se pondra default a credit
                payment_type = PaymentType.CREDIT_CARD
                        
            # Crea el metodo de pago
            new_payment = PaymentMethod(
                user_id=user.user_id,
                payment_type=payment_type,
                provider_ref=payment_method_id,  # pm_xxxxx
                last_four=card['last4'],
                expiration_date=f"{card['exp_month']:02d}/{str(card['exp_year'])[2:]}",
                is_default=False
            )
            
            db.add(new_payment)
            db.commit()
            db.refresh(new_payment)

            # Hace uso de la otra funcion para establecer default y borrar los demas si hay
            if is_default:
                return self.set_default_payment_method(
                    db=db,
                    cognito_sub=cognito_sub,
                    payment_id=new_payment.payment_id
                )
            
            return {
                "success": True,
                "message": "Tarjeta guardada exitosamente",
                "payment_method": new_payment
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al guardar método de pago: {str(e)}"}

    def delete_payment_method(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Elimina un método de pago previamente guardado tanto en el sistema como en Stripe.
            En caso de error al desvincular en Stripe, el método se elimina de la base de datos
            de todas formas.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario.
            payment_id (int): Identificador del método de pago a eliminar.

        Retorna:
            dict: Mensaje de éxito o detalle del error.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            # Intenta hacer detach de stripe
            if payment_method.provider_ref and payment_method.provider_ref.startswith('pm_'):
                detach_result = stripe_service.detach_payment_method(payment_method.provider_ref)
                if not detach_result.get('success'):
                    print(f"Warning: Could not detach from Stripe: {detach_result.get('error')}")
            
            db.delete(payment_method)
            db.commit()
            
            return {
                "success": True,
                "message": "Método de pago eliminado correctamente"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al eliminar método de pago: {str(e)}"}
    
    def set_default_payment_method(self, db: Session, cognito_sub: str, payment_id: int) -> Dict:
        """
        Autor: Lizbeth Barajas

        Descripción:
            Establece una tarjeta como método de pago predeterminado del usuario.
            Se desmarca cualquier otra tarjeta que anteriormente estuviera configurada
            como predeterminada.

        Parámetros:
            db (Session): Sesión de base de datos.
            cognito_sub (str): Identificador del usuario.
            payment_id (int): ID del método de pago a establecer como predeterminado.

        Retorna:
            dict: Resultado de la operación y el método configurado.
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.payment_id == payment_id,
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_type.in_([PaymentType.CREDIT_CARD, PaymentType.DEBIT_CARD])
            ).first()
            
            if not payment_method:
                return {"success": False, "error": "Método de pago no encontrado"}
            
            # Quita el default de otros metodos de pago
            db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user.user_id,
                PaymentMethod.payment_id != payment_id
            ).update({"is_default": False})
            
            # Establece este como unico metodo default
            payment_method.is_default = True
            db.commit()
            db.refresh(payment_method)
            
            return {
                "success": True,
                "message": "Método de pago establecido como predeterminado",
                "payment_method": payment_method
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al establecer método de pago predeterminado: {str(e)}"}

payment_method_service = PaymentMethodService()
