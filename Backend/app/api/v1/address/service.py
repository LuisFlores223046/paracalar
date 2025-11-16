from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.models.address import Address
from app.models.user import User

class AddressService:
    
    def get_user_addresses(self, db: Session, cognito_sub: str) -> Dict:
        """
        Obtiene todas las direcciones de un usuario
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            addresses = db.query(Address).filter(Address.user_id == user.user_id).all()
            
            return {
                "success": True,
                "addresses": addresses,
                "total": len(addresses)
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener direcciones: {str(e)}"}
    
    def get_address_by_id(self, db: Session, cognito_sub: str, address_id: int) -> Dict:
        """
        Obtiene una direccion especifica del usuario
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            address = db.query(Address).filter(
                Address.address_id == address_id,
                Address.user_id == user.user_id
            ).first()
            
            if not address:
                return {"success": False, "error": "Dirección no encontrada"}
            
            return {
                "success": True,
                "address": address
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener dirección: {str(e)}"}
    
    def create_address(
        self,
        db: Session,
        cognito_sub: str,
        address_name: Optional[str],
        address_line1: str,
        address_line2: Optional[str],
        country: str,
        state: str,
        city: str,
        zip_code: str,
        recipient_name: str,
        phone_number: str,
        is_default: bool = False
    ) -> Dict:
        """
        Crea nueva direccion 
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user or not user.account_status:
                return {"success": False, "error": "Usuario no encontrado o inactivo"}
            
            if is_default: # Checa si hay otro default para cambiarlo por este
                db.query(Address).filter(
                    Address.user_id == user.user_id,
                    Address.is_default == True
                ).update({"is_default": False})
            
            new_address = Address(
                user_id=user.user_id,
                address_name=address_name,
                address_line1=address_line1,
                address_line2=address_line2,
                country=country,
                state=state,
                city=city,
                zip_code=zip_code,
                recipient_name=recipient_name,
                phone_number=phone_number,
                is_default=is_default
            )
            
            db.add(new_address)
            db.commit()
            db.refresh(new_address)
            
            return {
                "success": True,
                "message": "Dirección creada correctamente",
                "address": new_address
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al crear dirección: {str(e)}"}
    
    def update_address(
        self,
        db: Session,
        cognito_sub: str,
        address_id: int,
        address_name: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        recipient_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> Dict:
        """
        Actualiza una direccion existente
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            address = db.query(Address).filter(
                Address.address_id == address_id,
                Address.user_id == user.user_id
            ).first()
            
            if not address:
                return {"success": False, "error": "Dirección no encontrada"}
            
            if is_default: # Checa y cambia default (si ya hay)
                db.query(Address).filter(
                    Address.user_id == user.user_id,
                    Address.address_id != address_id,
                    Address.is_default == True
                ).update({"is_default": False})
            
            if address_name is not None:
                address.address_name = address_name
            if address_line1 is not None:
                address.address_line1 = address_line1
            if address_line2 is not None:
                address.address_line2 = address_line2
            if country is not None:
                address.country = country
            if state is not None:
                address.state = state
            if city is not None:
                address.city = city
            if zip_code is not None:
                address.zip_code = zip_code
            if recipient_name is not None:
                address.recipient_name = recipient_name
            if phone_number is not None:
                address.phone_number = phone_number
            if is_default is not None:
                address.is_default = is_default
            
            db.commit()
            db.refresh(address)
            
            return {
                "success": True,
                "message": "Dirección actualizada correctamente",
                "address": address
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al actualizar dirección: {str(e)}"}
    
    def delete_address(self, db: Session, cognito_sub: str, address_id: int) -> Dict:
        """
        Borra una direccion
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            address = db.query(Address).filter(
                Address.address_id == address_id,
                Address.user_id == user.user_id
            ).first()
            
            if not address:
                return {"success": False, "error": "Dirección no encontrada"}
            
            db.delete(address)
            db.commit()
            
            return {
                "success": True,
                "message": "Dirección eliminada correctamente"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al eliminar dirección: {str(e)}"}
    
    def set_default_address(self, db: Session, cognito_sub: str, address_id: int) -> Dict:
        """
        Hace a una direccion la seleccionada por defecto
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            address = db.query(Address).filter(
                Address.address_id == address_id,
                Address.user_id == user.user_id
            ).first()
            
            if not address:
                return {"success": False, "error": "Dirección no encontrada"}
            
            # Se asegura que el resto no esten marcadas como default
            db.query(Address).filter(
                Address.user_id == user.user_id,
                Address.address_id != address_id
            ).update({"is_default": False})
            
            address.is_default = True
            db.commit()
            db.refresh(address)
            
            return {
                "success": True,
                "message": "Dirección establecida como predeterminada",
                "address": address
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al establecer dirección predeterminada: {str(e)}"}

address_service = AddressService()
