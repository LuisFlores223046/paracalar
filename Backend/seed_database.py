"""
Script de Seeding para BeFit - Base de Datos de Prueba
======================================================

Este script crea:
- 1 Usuario Administrador
- 18 Productos distribuidos en 6 categorías

Nota: Las categorías ahora son strings directos en el modelo Product.
No existe tabla Category separada.

Uso:
    python seed_database.py
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.models.enum import UserRole, AuthType, Gender
from app.core.security import hash_password
from datetime import date, datetime
import sys


def create_admin_user(db: Session):
    """Crea un usuario administrador de prueba"""
    print("\n👤 Creando usuario administrador...")
    
    # Verificar si ya existe un admin
    existing_admin = db.query(User).filter(
        User.email == "admin@befit.com"
    ).first()
    
    if existing_admin:
        print("   ⚠️  Admin ya existe. Saltando...")
        return existing_admin
    
    # Crear admin
    admin = User(
        cognito_sub="test-admin-123",  # Sub de prueba
        email="admin@befit.com",
        password_hash=hash_password("Admin123!"),
        first_name="Admin",
        last_name="BeFit",
        gender=Gender.MALE,
        date_of_birth=date(1990, 1, 1),
        profile_picture="https://ui-avatars.com/api/?name=Admin+BeFit&size=200",
        auth_type=AuthType.EMAIL,
        role=UserRole.ADMIN,
        account_status=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"   ✅ Admin creado: {admin.email}")
    print(f"   🔑 Password: Admin123!")
    
    return admin


def seed_products(db: Session):
    """Crea 18 productos en 6 categorías"""
    
    print("\n📦 Creando productos...")
    
    # Definir las 6 categorías
    categories = [
        "Proteínas",
        "Pre-Entreno",
        "Creatina",
        "Vitaminas",
        "Aminoácidos",
        "Ganadores de Peso"
    ]
    
    # Verificar si ya existen productos
    existing_count = db.query(Product).count()
    if existing_count > 0:
        print(f"   ⚠️  Ya existen {existing_count} productos.")
        response = input("   ¿Deseas eliminarlos y crear nuevos? (s/n): ")
        if response.lower() == 's':
            # Eliminar productos existentes
            db.query(ProductImage).delete()
            db.query(Product).delete()
            db.commit()
            print("   ✅ Productos anteriores eliminados")
        else:
            print("   ❌ Operación cancelada")
            return
    
    # Productos por categoría
    products_data = {
        "Proteínas": [
            {
                "name": "Whey Protein Gold Standard",
                "description": "Proteína de suero de leche de alta calidad con 24g de proteína por servida. Perfecta para recuperación muscular post-entrenamiento.",
                "brand": "Optimum Nutrition",
                "physical_activities": ["weightlifting", "crossfit", "bodybuilding"],
                "fitness_objectives": ["muscle_gain", "recovery", "strength"],
                "nutritional_value": "Por servida (30g): 120 calorías, 24g proteína, 1g carbohidratos, 1g grasa",
                "price": 899.99,
                "stock": 50,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Proteína Vegana Premium",
                "description": "Mezcla de proteínas vegetales (arveja, arroz y quinoa) con sabor natural. Ideal para atletas veganos.",
                "brand": "Garden of Life",
                "physical_activities": ["running", "yoga", "cycling"],
                "fitness_objectives": ["muscle_gain", "weight_loss", "general_wellness"],
                "nutritional_value": "Por servida (33g): 140 calorías, 20g proteína, 7g carbohidratos, 3g grasa",
                "price": 1099.99,
                "stock": 30,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1622484211850-5f7e61d99102?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Caseína Micelar Nocturna",
                "description": "Proteína de absorción lenta perfecta para tomar antes de dormir. Mantiene tus músculos alimentados durante la noche.",
                "brand": "Dymatize",
                "physical_activities": ["weightlifting", "bodybuilding"],
                "fitness_objectives": ["muscle_gain", "recovery"],
                "nutritional_value": "Por servida (34g): 120 calorías, 25g proteína, 3g carbohidratos, 1g grasa",
                "price": 949.99,
                "stock": 40,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?w=400", "is_primary": True}
                ]
            }
        ],
        
        "Pre-Entreno": [
            {
                "name": "C4 Original Pre-Workout",
                "description": "Pre-entreno explosivo con cafeína, beta-alanina y creatina. Energía y enfoque para entrenamientos intensos.",
                "brand": "Cellucor",
                "physical_activities": ["weightlifting", "crossfit", "hiit"],
                "fitness_objectives": ["strength", "endurance", "energy_boost"],
                "nutritional_value": "Por servida (6.5g): 0 calorías, 150mg cafeína, 1.6g beta-alanina",
                "price": 649.99,
                "stock": 60,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1541788125-7f8f93c7cf91?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Pre-Entreno Natural Sin Cafeína",
                "description": "Fórmula natural con óxido nítrico, citrulina y beta-alanina. Perfecto para entrenar por la noche.",
                "brand": "Legion Athletics",
                "physical_activities": ["weightlifting", "bodybuilding", "crossfit"],
                "fitness_objectives": ["muscle_gain", "pump", "endurance"],
                "nutritional_value": "Por servida (8g): 5 calorías, 0mg cafeína, 6g citrulina malato",
                "price": 799.99,
                "stock": 35,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Extreme Energy Pre-Workout",
                "description": "Pre-entreno de alta potencia con 300mg de cafeína. Solo para atletas experimentados.",
                "brand": "Hyde",
                "physical_activities": ["weightlifting", "crossfit", "powerlifting"],
                "fitness_objectives": ["strength", "energy_boost", "focus"],
                "nutritional_value": "Por servida (7g): 0 calorías, 300mg cafeína, 3.2g beta-alanina",
                "price": 729.99,
                "stock": 45,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=400", "is_primary": True}
                ]
            }
        ],
        
        "Creatina": [
            {
                "name": "Creatina Monohidratada Micronizada",
                "description": "Creatina pura al 99.99%, micronizada para mejor absorción. El suplemento más estudiado y efectivo.",
                "brand": "Optimum Nutrition",
                "physical_activities": ["weightlifting", "powerlifting", "sprinting"],
                "fitness_objectives": ["strength", "muscle_gain", "power"],
                "nutritional_value": "Por servida (5g): 0 calorías, 5g creatina monohidratada",
                "price": 399.99,
                "stock": 80,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1599932164574-643c2695bc5d?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Creatina HCL Concentrada",
                "description": "Clorhidrato de creatina concentrado. Sin fase de carga, sin retención de líquidos.",
                "brand": "MuscleTech",
                "physical_activities": ["weightlifting", "bodybuilding", "crossfit"],
                "fitness_objectives": ["strength", "muscle_gain", "definition"],
                "nutritional_value": "Por servida (2g): 0 calorías, 2g creatina HCL",
                "price": 549.99,
                "stock": 55,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1571939228382-b2f2b585ce15?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Creatina + Carbohidratos",
                "description": "Creatina monohidratada con dextrosa para maximizar la absorción. Ideal post-entrenamiento.",
                "brand": "Universal Nutrition",
                "physical_activities": ["weightlifting", "bodybuilding"],
                "fitness_objectives": ["muscle_gain", "strength", "recovery"],
                "nutritional_value": "Por servida (50g): 190 calorías, 5g creatina, 45g carbohidratos",
                "price": 599.99,
                "stock": 40,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1607962837359-5e7e89f86776?w=400", "is_primary": True}
                ]
            }
        ],
        
        "Vitaminas": [
            {
                "name": "Multivitamínico Completo",
                "description": "Complejo vitamínico y mineral completo diseñado para atletas. 24 nutrientes esenciales.",
                "brand": "Animal Pak",
                "physical_activities": ["weightlifting", "crossfit", "running", "cycling"],
                "fitness_objectives": ["general_wellness", "recovery", "immune_support"],
                "nutritional_value": "Por servida (2 tabletas): Vitaminas A, C, D, E, B-Complex, Zinc, Magnesio",
                "price": 449.99,
                "stock": 70,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Vitamina D3 + K2",
                "description": "Combinación sinérgica de vitaminas D3 y K2 para salud ósea, inmune y cardiovascular.",
                "brand": "Now Foods",
                "physical_activities": ["weightlifting", "running", "swimming"],
                "fitness_objectives": ["bone_health", "immune_support", "general_wellness"],
                "nutritional_value": "Por servida (1 cápsula): 5000 IU Vitamina D3, 100mcg Vitamina K2",
                "price": 299.99,
                "stock": 90,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1550572017-4c797d8e7e46?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Omega 3 Premium",
                "description": "Aceite de pescado ultra purificado con EPA y DHA. Apoya salud cardiovascular y articular.",
                "brand": "Nordic Naturals",
                "physical_activities": ["weightlifting", "running", "cycling", "swimming"],
                "fitness_objectives": ["joint_health", "recovery", "general_wellness"],
                "nutritional_value": "Por servida (2 cápsulas): 20 calorías, 1000mg EPA, 500mg DHA",
                "price": 649.99,
                "stock": 60,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=400", "is_primary": True}
                ]
            }
        ],
        
        "Aminoácidos": [
            {
                "name": "BCAA 2:1:1 Powder",
                "description": "Aminoácidos de cadena ramificada en polvo. Leucina, Isoleucina y Valina para recuperación muscular.",
                "brand": "Scivation Xtend",
                "physical_activities": ["weightlifting", "crossfit", "bodybuilding"],
                "fitness_objectives": ["recovery", "muscle_gain", "endurance"],
                "nutritional_value": "Por servida (7g): 0 calorías, 7g BCAA (3.5g Leucina)",
                "price": 549.99,
                "stock": 65,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1526224499653-e65eb46e97a3?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Glutamina Pura",
                "description": "L-Glutamina micronizada para recuperación intestinal y muscular. Apoya el sistema inmune.",
                "brand": "Optimum Nutrition",
                "physical_activities": ["weightlifting", "crossfit", "running"],
                "fitness_objectives": ["recovery", "immune_support", "gut_health"],
                "nutritional_value": "Por servida (5g): 0 calorías, 5g L-Glutamina",
                "price": 449.99,
                "stock": 50,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400", "is_primary": True}
                ]
            },
            {
                "name": "EAA Complete",
                "description": "Los 9 aminoácidos esenciales en proporciones óptimas. Superior a los BCAA tradicionales.",
                "brand": "Transparent Labs",
                "physical_activities": ["weightlifting", "crossfit", "bodybuilding", "hiit"],
                "fitness_objectives": ["muscle_gain", "recovery", "endurance"],
                "nutritional_value": "Por servida (9g): 0 calorías, 9g EAA (incluye 5g BCAA)",
                "price": 699.99,
                "stock": 40,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1541554440-6f26acf4a792?w=400", "is_primary": True}
                ]
            }
        ],
        
        "Ganadores de Peso": [
            {
                "name": "Mass Gainer Extreme 1250",
                "description": "Fórmula hipercalórica con 1250 calorías por servida. Ideal para personas con metabolismo rápido.",
                "brand": "Dymatize Super Mass",
                "physical_activities": ["weightlifting", "bodybuilding"],
                "fitness_objectives": ["mass_gain", "muscle_gain", "bulking"],
                "nutritional_value": "Por servida (334g): 1250 calorías, 50g proteína, 250g carbohidratos, 9g grasa",
                "price": 1299.99,
                "stock": 25,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Lean Mass Gainer",
                "description": "Ganador de peso limpio con proteínas de calidad y carbohidratos complejos. Mínima grasa.",
                "brand": "BSN True Mass",
                "physical_activities": ["weightlifting", "bodybuilding", "crossfit"],
                "fitness_objectives": ["mass_gain", "muscle_gain", "lean_bulking"],
                "nutritional_value": "Por servida (165g): 700 calorías, 46g proteína, 90g carbohidratos, 16g grasa",
                "price": 1149.99,
                "stock": 30,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1622484211850-5f7e61d99102?w=400", "is_primary": True}
                ]
            },
            {
                "name": "Carbohidratos Complejos",
                "description": "Maltodextrina y dextrosa de alta calidad. Perfecto para mezclar con tu proteína favorita.",
                "brand": "MyProtein",
                "physical_activities": ["weightlifting", "bodybuilding", "endurance_sports"],
                "fitness_objectives": ["mass_gain", "recovery", "energy_boost"],
                "nutritional_value": "Por servida (100g): 380 calorías, 0g proteína, 95g carbohidratos, 0g grasa",
                "price": 499.99,
                "stock": 70,
                "images": [
                    {"image_path": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?w=400", "is_primary": True}
                ]
            }
        ]
    }
    
    # Crear productos
    created_count = 0
    for category, products in products_data.items():
        print(f"\n   📂 Categoría: {category}")
        
        for product_data in products:
            # Extraer imágenes
            images_data = product_data.pop("images")
            
            # Crear producto
            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                brand=product_data["brand"],
                category=category,  # ✅ String directo
                physical_activities=product_data["physical_activities"],  # ✅ JSON Array
                fitness_objectives=product_data["fitness_objectives"],  # ✅ JSON Array
                nutritional_value=product_data["nutritional_value"],
                price=product_data["price"],
                stock=product_data["stock"],
                average_rating=None,  # ✅ Inicialmente sin rating
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(product)
            db.flush()  # Para obtener el product_id
            
            # Crear imágenes
            for img_data in images_data:
                image = ProductImage(
                    product_id=product.product_id,
                    image_path=img_data["image_path"],
                    is_primary=img_data["is_primary"]
                )
                db.add(image)
            
            created_count += 1
            print(f"      ✅ {product.name} - ${product.price}")
    
    db.commit()
    print(f"\n   🎉 {created_count} productos creados exitosamente!")


def show_summary(db: Session):
    """Muestra un resumen de lo creado"""
    print("\n" + "="*70)
    print("📊 RESUMEN DE LA BASE DE DATOS")
    print("="*70)
    
    # Contar usuarios
    admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
    user_count = db.query(User).count()
    
    print(f"\n👥 USUARIOS:")
    print(f"   - Total: {user_count}")
    print(f"   - Administradores: {admin_count}")
    
    # Contar productos por categoría
    print(f"\n📦 PRODUCTOS:")
    products = db.query(Product).all()
    
    categories = {}
    for product in products:
        if product.category not in categories:
            categories[product.category] = 0
        categories[product.category] += 1
    
    print(f"   - Total: {len(products)}")
    print(f"   - Por categoría:")
    for category, count in sorted(categories.items()):
        print(f"      • {category}: {count} productos")
    
    # Contar imágenes
    image_count = db.query(ProductImage).count()
    print(f"\n🖼️  IMÁGENES:")
    print(f"   - Total: {image_count}")
    
    print("\n" + "="*70)
    
    # Credenciales de acceso
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("   Email: admin@befit.com")
    print("   Password: Admin123!")
    print("\n   📝 Login en: POST /api/v1/auth/login")
    print("   📚 Docs en: http://localhost:8000/docs")
    print("="*70 + "\n")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🌱 SEEDING DE BASE DE DATOS - BEFIT")
    print("="*70)
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Verificar conexión
        print("\n🔌 Conectando a la base de datos...")
        engine.connect()
        print("   ✅ Conexión exitosa")
        
        # Crear admin
        create_admin_user(db)
        
        # Crear productos
        seed_products(db)
        
        # Mostrar resumen
        show_summary(db)
        
        print("✅ Seeding completado exitosamente!")
        print("\n💡 Ahora puedes iniciar el servidor con: uvicorn app.main:app --reload\n")
        
    except Exception as e:
        print(f"\n❌ Error durante el seeding: {str(e)}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
