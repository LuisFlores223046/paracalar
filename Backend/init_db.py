from app.core.database import Base, engine
from app.models import *  # Importar todos los modelos

def init_db():
    """Crea todas las tablas en la base de datos"""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente!")

if __name__ == "__main__":
    init_db()