# Autor: Luis Flores
# Fecha: 13/11/2025
# Descripción: Rutas API de administración para gestión de productos. Incluye endpoints
#              para crear, actualizar y eliminar productos, así como operaciones en lote.
#              Todos los endpoints requieren permisos de administrador.

from fastapi import APIRouter, Depends, Query, status, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.api.deps import get_db, require_admin
from app.api.v1.admin import schemas
from app.api.v1.admin.service import AdminProductService
from app.api.v1.products import schemas as product_schemas
from app.api.v1.products.service import ProductService
from app.models.user import User

router = APIRouter()


# ============ GESTIÓN DE PRODUCTOS (ADMIN) ============

@router.post("/products", response_model=product_schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    brand: str = Form(...),
    category: str = Form(...),
    physical_activities: str = Form("[]", description="JSON array o strings separados por coma"),
    fitness_objectives: str = Form("[]", description="JSON array o strings separados por coma"),
    nutritional_value: str = Form(...),
    price: float = Form(..., gt=0),
    stock: int = Form(..., ge=0),
    images: List[UploadFile] = File(..., description="Al menos 1 imagen es requerida"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Crea un nuevo producto con sus imágenes. Este endpoint usa multipart/form-data
                 para permitir la carga de archivos. Valida formatos de imagen y tamaños,
                 sube las imágenes a S3 y registra el producto en la base de datos.
    Parámetros:
        name (str): Nombre del producto.
        description (str): Descripción detallada.
        brand (str): Marca del producto.
        category (str): Categoría del producto.
        physical_activities (str): Actividades físicas relacionadas (JSON array o CSV).
        fitness_objectives (str): Objetivos fitness relacionados (JSON array o CSV).
        nutritional_value (str): Información nutricional.
        price (float): Precio del producto (mayor a 0).
        stock (int): Cantidad en inventario (mayor o igual a 0).
        images (List[UploadFile]): Lista de imágenes del producto (mínimo 1).
        current_user (User): Usuario administrador autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        ProductResponse: Producto creado con todas sus relaciones.
    Excepciones:
        HTTPException 400: Si no se proporciona al menos 1 imagen o hay errores en los datos.
    """
    from app.services.s3_service import S3Service
    from app.models.product import Product
    from app.models.product_image import ProductImage
    
    # Validar que hay al menos 1 imagen
    if not images or len(images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes subir al menos 1 imagen del producto"
        )
    
    # Función helper para parsear arrays
    def parse_array_field(value: str, field_name: str) -> list:
        """
        Autor: Luis Flores
        Descripción: Parsea un campo que puede ser JSON array o string separado por comas.
        Parámetros:
            value (str): Valor a parsear.
            field_name (str): Nombre del campo para mensajes de error.
        Retorna:
            list: Lista de valores parseados.
        Excepciones:
            HTTPException 400: Si el formato JSON es inválido.
        """
        if not value or value.strip() == "":
            return []
        
        value = value.strip()
        
        # Intentar parsear como JSON
        if value.startswith('['):
            try:
                result = json.loads(value)
                if isinstance(result, list):
                    return result
                else:
                    raise ValueError(f"{field_name} debe ser un array")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error en {field_name}: JSON inválido. Ejemplo: '[\"weightlifting\", \"crossfit\"]'"
                )
        
        # Si no es JSON, asumir que es string separado por comas
        return [item.strip() for item in value.split(',') if item.strip()]
    
    # Parsear los arrays
    try:
        physical_activities_list = parse_array_field(physical_activities, "physical_activities")
        fitness_objectives_list = parse_array_field(fitness_objectives, "fitness_objectives")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error procesando arrays: {str(e)}"
        )
    
    # Crear el producto en la BD
    new_product = Product(
        name=name,
        description=description,
        brand=brand,
        category=category,
        physical_activities=physical_activities_list,
        fitness_objectives=fitness_objectives_list,
        nutritional_value=nutritional_value,
        price=price,
        stock=stock,
        is_active=True
    )
    
    db.add(new_product)
    db.flush()  # Para obtener el product_id sin hacer commit aún
    
    # Subir imágenes a S3
    s3_service = S3Service()
    uploaded_count = 0
    errors = []
    
    for idx, image_file in enumerate(images):
        try:
            # Leer la imagen
            image_bytes = await image_file.read()
            
            # Subir a S3
            result = s3_service.upload_product_img(
                file_content=image_bytes,
                product_id=str(new_product.product_id)
            )
            
            if result["success"]:
                # Guardar en la BD
                db_image = ProductImage(
                    product_id=new_product.product_id,
                    image_path=result["file_url"],
                    is_primary=(idx == 0)  # La primera imagen es primary
                )
                db.add(db_image)
                uploaded_count += 1
            else:
                errors.append(f"Imagen {idx + 1}: {result['error']}")
        
        except Exception as e:
            errors.append(f"Imagen {idx + 1}: Error - {str(e)}")
    
    # Si ninguna imagen se subió, revertir la creación del producto
    if uploaded_count == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo subir ninguna imagen. Errores: {', '.join(errors)}"
        )
    
    # Si algunas imágenes fallaron, registrar pero continuar
    if errors:
        print(f"⚠️ Advertencias al subir imágenes del producto {new_product.product_id}: {errors}")
    
    db.commit()
    db.refresh(new_product)
    
    return new_product


@router.put("/products/{product_id}", response_model=product_schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: product_schemas.ProductUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Actualiza un producto existente. Solo los campos proporcionados
                 en el request serán actualizados. Requiere permisos de administrador.
    Parámetros:
        product_id (int): ID del producto a actualizar.
        product_data (ProductUpdate): Datos del producto a actualizar (campos opcionales).
        current_user (User): Usuario administrador autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        ProductResponse: Producto actualizado con todas sus relaciones.
    Excepciones:
        HTTPException 404: Si el producto no existe.
    """
    return ProductService.update_product(db, product_id, product_data)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    hard_delete: bool = Query(False, description="Si es True, elimina permanentemente"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Elimina un producto. Por defecto hace soft delete (is_active = False).
                 Si hard_delete=True, elimina permanentemente de la base de datos.
    Parámetros:
        product_id (int): ID del producto a eliminar.
        hard_delete (bool): Si es True, eliminación permanente; si es False, soft delete.
        current_user (User): Usuario administrador autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        None: Respuesta 204 No Content si la eliminación fue exitosa.
    Excepciones:
        HTTPException 404: Si el producto no existe.
    """
    if hard_delete:
        ProductService.hard_delete_product(db, product_id)
    else:
        ProductService.delete_product(db, product_id)
    
    return None


@router.post("/products/bulk-action", response_model=schemas.BulkActionResponse)
def bulk_product_action(
    action_data: schemas.BulkProductAction,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Autor: Luis Flores
    Descripción: Realiza operaciones en lote sobre múltiples productos.
                 Acciones disponibles: activar, desactivar o eliminar productos.
    Parámetros:
        action_data (BulkProductAction): IDs de productos y acción a realizar.
        current_user (User): Usuario administrador autenticado.
        db (Session): Sesión de base de datos.
    Retorna:
        BulkActionResponse: Resultado con cantidad de éxitos, fallos y lista de errores.
    """
    return AdminProductService.bulk_update_products(db, action_data)