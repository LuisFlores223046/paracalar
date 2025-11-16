from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.models.user import User
from app.models.enum import Gender
from app.services.s3_service import S3Service
from datetime import date

class UserProfileService:
    def __init__(self):
        self.s3_service = S3Service()
    
    def get_user_profile(self, db: Session, cognito_sub: str) -> Optional[Dict]:
        """
        Obtiene perfil de usuario de la base de datos
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            if not user.account_status:
                return {"success": False, "error": "Cuenta inactiva"}
            
            return {
                "success": True,
                "user": {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "gender": user.gender.value if user.gender else None,
                    "date_of_birth": user.date_of_birth,
                    "profile_picture": user.profile_picture,
                    "role": user.role.value,
                    "account_status": user.account_status,
                    "auth_type": user.auth_type.value,
                    "created_at": user.created_at
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener perfil: {str(e)}"}
    
    def update_user_profile(
        self,
        db: Session,
        cognito_sub: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        gender: Optional[Gender] = None,
        date_of_birth: Optional[date] = None
    ) -> Dict:
        """
        Actualiza informacion de usuario
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            if not user.account_status:
                return {"success": False, "error": "Cuenta inactiva"}
            
            # Update only provided fields
            if first_name is not None:
                user.first_name = first_name
            
            if last_name is not None:
                user.last_name = last_name
            
            if gender is not None:
                user.gender = gender
            
            if date_of_birth is not None:
                user.date_of_birth = date_of_birth
            
            db.commit()
            db.refresh(user)
            
            return {
                "success": True,
                "message": "Perfil actualizado correctamente",
                "user": {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "gender": user.gender.value if user.gender else None,
                    "date_of_birth": user.date_of_birth,
                    "profile_picture": user.profile_picture,
                    "role": user.role.value,
                    "account_status": user.account_status,
                    "auth_type": user.auth_type.value,
                    "created_at": user.created_at
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al actualizar perfil: {str(e)}"}
        
    def update_profile_image(
        self,
        db: Session,
        cognito_sub: str,
        image_content: bytes
    ) -> Dict:
        """
        Actualiza foto de perfil en S3 y URL en base de datos
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()

            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            if not user.account_status:
                return {"success": False, "error": "Cuenta inactiva"}
            
            old_url = user.profile_picture

            if old_url:
                self.s3_service.delete_profile_img(old_url=old_url, user_id=str(cognito_sub))
            
            # Upload new image to S3 (this will overwrite if same user_id)
            upload_result = self.s3_service.upload_profile_img(
                file_content=image_content,
                user_id=str(cognito_sub)
            )
            
            if not upload_result["success"]:
                return upload_result
            
            # Update database with new image URL
            user.profile_picture = upload_result["file_url"]
            db.commit()
            db.refresh(user)
            
            return {
                "success": True,
                "message": "Imagen de perfil actualizada correctamente",
                "profile_picture_url": user.profile_picture
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al actualizar imagen: {str(e)}"}
    
    def soft_delete_account(self, db: Session, cognito_sub: str) -> Dict:
        """
        Cambia status de usuario a falso (soft delete)
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            if not user.account_status:
                return {"success": False, "error": "La cuenta ya esta inactiva"}
            
            user.account_status = False
            db.commit()
            
            return {
                "success": True,
                "message": "Cuenta eliminada correctamente"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error al eliminar cuenta: {str(e)}"}
    
    def get_basic_profile(self, db: Session, cognito_sub: str) -> Optional[Dict]:
        """
        Obtiene perfil basico de usuario
        """
        try:
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            
            if not user:
                return {"success": False, "error": "Usuario no encontrado"}
            
            return {
                "success": True,
                "user": {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_picture": user.profile_picture
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Error al obtener perfil básico: {str(e)}"}

user_profile_service = UserProfileService()