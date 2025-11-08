from app.core.database import SessionLocal
from app.models.category import Category

def seed_categories():
    """Inicializa las categorías predefinidas en la base de datos"""
    db = SessionLocal()
    
    # Definir categorías predefinidas
    categories = [
        {
            "name": "Proteínas",
            "description": "Suplementos de proteína para ganancia muscular y recuperación",
            "image_url": "https://example.com/images/proteinas.jpg"
        },
        {
            "name": "Pre-Entreno",
            "description": "Suplementos para energía y rendimiento antes del entrenamiento",
            "image_url": "https://example.com/images/pre-entreno.jpg"
        },
        {
            "name": "Vitaminas y Minerales",
            "description": "Suplementos vitamínicos y minerales para salud general",
            "image_url": "https://example.com/images/vitaminas.jpg"
        },
        {
            "name": "Creatina",
            "description": "Suplementos de creatina para fuerza y potencia",
            "image_url": "https://example.com/images/creatina.jpg"
        },
        {
            "name": "Aminoácidos",
            "description": "BCAA, glutamina y otros aminoácidos esenciales",
            "image_url": "https://example.com/images/aminoacidos.jpg"
        },
        {
            "name": "Quemadores de Grasa",
            "description": "Suplementos para pérdida de peso y definición",
            "image_url": "https://example.com/images/quemadores.jpg"
        },
        {
            "name": "Ganadores de Peso",
            "description": "Suplementos hipercalóricos para ganancia de masa",
            "image_url": "https://example.com/images/ganadores.jpg"
        },
        {
            "name": "Barras y Snacks",
            "description": "Barras proteicas y snacks saludables",
            "image_url": "https://example.com/images/barras.jpg"
        },
        {
            "name": "Accesorios",
            "description": "Shakers, guantes, cinturones y otros accesorios",
            "image_url": "https://example.com/images/accesorios.jpg"
        },
        {
            "name": "Salud Articular",
            "description": "Suplementos para articulaciones y huesos",
            "image_url": "https://example.com/images/articular.jpg"
        }
    ]
    
    try:
        # Verificar si ya existen categorías
        existing_count = db.query(Category).count()
        
        if existing_count > 0:
            print(f"⚠️  Ya existen {existing_count} categorías en la base de datos.")
            print("¿Deseas continuar? Esto puede crear duplicados. (s/n)")
            response = input().lower()
            if response != 's':
                print("❌ Operación cancelada.")
                return
        
        # Insertar categorías
        created_count = 0
        for cat_data in categories:
            # Verificar si la categoría ya existe por nombre
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            
            if not existing:
                category = Category(**cat_data)
                db.add(category)
                created_count += 1
                print(f"✅ Creada: {cat_data['name']}")
            else:
                print(f"⏭️  Ya existe: {cat_data['name']}")
        
        db.commit()
        print(f"\n🎉 Proceso completado. {created_count} categorías creadas.")
        
        # Mostrar todas las categorías
        all_categories = db.query(Category).all()
        print("\n📋 Categorías disponibles:")
        for cat in all_categories:
            print(f"   ID: {cat.category_id} - {cat.name}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Inicializando categorías predefinidas...\n")
    seed_categories()
