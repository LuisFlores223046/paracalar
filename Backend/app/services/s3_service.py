import boto3
from botocore.exceptions import ClientError
import uuid
from PIL import Image
import io
from app.config import settings


class S3Service:
    """Servicio para gestión de archivos en AWS S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_profile_img(
        self, 
        file_content: bytes, 
        user_id: str, 
        max_size_mb: int = 5, 
        allowed_formats: tuple = ('JPEG', 'PNG', 'WEBP')
    ) -> dict:
        """
        Sube una imagen de perfil a S3.
        
        Args:
            file_content: Contenido del archivo en bytes
            user_id: ID del usuario
            max_size_mb: Tamaño máximo permitido en MB
            allowed_formats: Formatos de imagen permitidos
            
        Returns:
            Dict con success, file_url y file_name o error
        """
        try:
            # Validar tamaño del archivo
            file_size = len(file_content) / (1024 * 1024)
            if file_size > max_size_mb:
                return {
                    "success": False, 
                    "error": f"El tamaño del archivo excede el límite de {max_size_mb} MB"
                }
            
            # Abrir y validar la imagen
            try:
                img = Image.open(io.BytesIO(file_content))
                img_format = img.format

                if img_format not in allowed_formats:
                    return {
                        "success": False, 
                        "error": f"Formato no permitido. Permitidos: {', '.join(allowed_formats)}"
                    }

            except Exception as e:
                return {
                    "success": False, 
                    "error": f"El archivo no es una imagen válida: {str(e)}"
                }
            
            # Redimensionar la imagen si es necesario
            max_dimension = 1024
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format=img_format, optimize=True, quality=85)
                file_content = output.getvalue()

            # Preparar para subir a S3
            file_ext = img_format.lower()
            file_name = f"profile_images/{user_id}/{uuid.uuid4()}.{file_ext}"

            content_types = {
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp'
            }
            content_type = content_types.get(file_ext, 'image/jpeg')

            # Subir el archivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_content,
                ContentType=content_type,
                Metadata={'user_id': user_id}
            )

            img_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"

            return {
                "success": True, 
                "file_url": img_url, 
                "file_name": file_name
            }
        
        except ClientError as e:
            return {"success": False, "error": f"Error al subir a S3: {str(e)}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}
        
    def upload_product_img(
        self, 
        file_content: bytes, 
        product_id: str, 
        max_size_mb: int = 5, 
        allowed_formats: tuple = ('JPEG', 'PNG', 'WEBP')
    ) -> dict:
        """
        Sube una imagen de producto a S3.
        
        Similar a upload_profile_img pero con ruta diferente.
        """
        try:
            # Validar tamaño
            file_size = len(file_content) / (1024 * 1024)
            if file_size > max_size_mb:
                return {
                    "success": False, 
                    "error": f"El tamaño del archivo excede el límite de {max_size_mb} MB"
                }
            
            # Validar imagen
            try:
                img = Image.open(io.BytesIO(file_content))
                img_format = img.format

                if img_format not in allowed_formats:
                    return {
                        "success": False, 
                        "error": f"Formato no permitido. Permitidos: {', '.join(allowed_formats)}"
                    }
            
            except Exception as e:
                return {
                    "success": False, 
                    "error": f"El archivo no es una imagen válida: {str(e)}"
                }
            
            # Redimensionar
            max_dimension = 1024
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format=img_format, optimize=True, quality=85)
                file_content = output.getvalue()

            # Preparar para S3
            file_ext = img_format.lower()
            file_name = f"product_images/{product_id}/{uuid.uuid4()}.{file_ext}"

            content_types = {
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp'
            }
            content_type = content_types.get(file_ext, 'image/jpeg')

            # Subir
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_content,
                ContentType=content_type,
                Metadata={'product_id': product_id}
            )

            img_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"

            return {
                "success": True, 
                "file_url": img_url, 
                "file_name": file_name
            }
        
        except ClientError as e:
            return {"success": False, "error": f"Error al subir a S3: {str(e)}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}
    
    def delete_file(self, file_key: str) -> dict:
        """
        Elimina un archivo de S3.
        
        Args:
            file_key: Ruta del archivo en S3 (ej: "profile_images/123/uuid.jpg")
            
        Returns:
            Dict con success y message o error
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return {"success": True, "message": "Archivo eliminado correctamente"}
        
        except ClientError as e:
            return {"success": False, "error": f"Error al eliminar de S3: {str(e)}"}