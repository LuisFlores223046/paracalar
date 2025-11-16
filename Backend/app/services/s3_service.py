# Autor: Gabriel Vilchis
# Fecha: 13/11/2025
# Descripción: Este servicio define la clase S3Service, la cual proporciona métodos para manejar
# imágenes dentro de un bucket de Amazon S3
import boto3, re, io
from botocore.exceptions import ClientError
#import uuid
from PIL import Image
from app.config import settings
from typing import Dict

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_profile_img(self, file_content: bytes, user_id: str, max_size_mb: int = 5, allowed_formats: tuple = ('JPEG', 'PNG', 'WEBP')) -> dict:
        """
        Autor: Gabriel Vilchis
        Sube una imagen de perfil al bucket de S3 con validación de tamaño, formato,
        redimensionamiento y asignación de ruta única asociada al usuario.

        Args:
            file_content (bytes): Contenido binario del archivo de imagen.
            user_id (str): ID del usuario que será dueño de la imagen.
            max_size_mb (int, opcional): Límite máximo permitido en MB. Default = 5.
            allowed_formats (tuple, opcional): Formatos de imagen permitidos. Default = ('JPEG', 'PNG', 'WEBP').

        Returns:
            dict: Resultado del proceso de carga. Contiene:
                - success (bool): Indica si el proceso fue exitoso.
                - file_url (str, opcional): URL pública generada.
                - file_name (str, opcional): Ruta completa dentro del bucket.
                - error (str, opcional): Mensaje en caso de fallo.
        """
        try:
            # Tamaño del archivo en MB
            file_size = len(file_content) / (1024 * 1024)
            if file_size > max_size_mb:
                return {"success": False, "error": f"El tamaño del archivo excede el limite de {max_size_mb} MB"}
            
            # Abrir la imagen para verificar formato
            try:
                img = Image.open(io.BytesIO(file_content))
                img_format = img.format

                if img_format not in allowed_formats:
                    return {"success": False, "error": f"Formato de imagen no permitido. Los formatos permitidos son: {", ".join(allowed_formats)}"}

            except Exception as e:
                return {"success": False, "error": f"El archivo no es una imagen válida o está corrupto. Detalle: {str(e)}"}
            
            # Redimensiona la imagen
            max_dimension = 1024
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format=img_format, optimize=True, quality=85)
                file_content = output.getvalue()

            # Lógica para S3
            file_ext = img_format.lower()
            # corregi el nombre del archivo de la imagen aqui
            # Ahora en S3 sale el 1 del usuario como su carpeta, y posteriormente su imagen con el formato de imagen 
            file_name = f"profile_images/{user_id}/picture.{file_ext}" 

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

            return {"success": True, "file_url": img_url, "file_name": file_name}
 
        except ClientError as e:
            return {"success": False, "error": f"Error al subir a S3: {str(e)}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}
         
    def upload_product_img(self, file_content: bytes, product_id: str, max_size_mb: int = 5, allowed_formats: tuple = ('JPEG', 'PNG', 'WEBP')) -> dict:
        """
        Autor: Gabriel Vilchis
        Sube una imagen de producto a S3 siguiendo el mismo proceso de validación
        y redimensionamiento que las imágenes de perfil, pero usando una ruta
        distinta asociada al producto.

        Args:
            file_content (bytes): Contenido binario de la imagen.
            product_id (str): ID del producto asociado a la imagen.
            max_size_mb (int, opcional): Tamaño máximo permitido en MB. Default = 5.
            allowed_formats (tuple, opcional): Formatos permitidos. Default = ('JPEG', 'PNG', 'WEBP').

        Returns:
            dict: Resultado de la subida. Contiene:
                - success (bool)
                - file_url (str, opcional)
                - file_name (str, opcional)
                - error (str, opcional)
        """
        try:
            # Tamaño del archivo en MB
            file_size = len(file_content) / (1024 * 1024)
            if file_size > max_size_mb:
                return {"success": False, "error": f"El tamaño del archivo excede el limite de {max_size_mb} MB"}
            
            # Abrir la imagen para verificar formato
            try:
                img = Image.open(io.BytesIO(file_content))
                img_format = img.format

                if img_format not in allowed_formats:
                    return {"success": False, "error": f"Formato de imagen no permitido. Los formatos permitidos son: {", ".join(allowed_formats)}"}
            
            except Exception as e:
                return {"success": False, "error": f"El archivo no es una imagen válida o está corrupto. Detalle: {str(e)}"}
            
            # Redimensiona la imagen
            max_dimension = 1024
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format=img_format, optimize=True, quality=85)
                file_content = output.getvalue()

            # Lógica para S3
            file_ext = img_format.lower()
            file_name = f"product_images/{product_id}/picture.{file_ext}" # de igual forma aqui 

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
                Metadata={'product_id': product_id}
            )

            img_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"

            return {"success": True, "file_url": img_url, "file_name": file_name}
        
        except ClientError as e:
            return {"success": False, "error": f"Error al subir a S3: {str(e)}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}
            
    def delete_profile_img(self, old_url: str, user_id: str) -> Dict:
        """
        Autor: Gabriel Vilchis
        Elimina una imagen de perfil antigua del bucket de S3 buscando su ruta
        dentro del URL mediante un patrón regex. Si la imagen no existe o el enlace
        es inválido, la operación se omite sin error crítico.

        Args:
            old_url (str): URL antiguo de la imagen almacenada en S3.
            user_id (str): ID del usuario dueño del recurso (usado únicamente como referencia lógica).

        Returns:
            Dict: Resultado del proceso:
                - success (bool)
                - message (str, opcional): Detalles del resultado.
                - error (str, opcional): Mensaje de error si ocurre un fallo inesperado.
        """

        try:
            # busca el patron del sub de cognito en las carpetas
            key_match = re.search(r"profile_images/[^/?]+/[^/?]+", old_url)
            
            if not key_match:
                return {"success": True, "message": "URL antigua no válida o vacía, no se requiere eliminación."}

            s3_key_to_delete = key_match.group(0)

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key_to_delete
            )
            
            return {"success": True, "message": f"Objeto eliminado: {s3_key_to_delete}"}
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {"success": True, "message": "El objeto no existía, eliminación omitida."}
            
            return {"success": False, "error": f"Error al eliminar de S3: {str(e)}"}
        
        except Exception as e:
            return {"success": False, "error": f"Error inesperado al intentar eliminar: {str(e)}"} 