"""
Script para crear un usuario administrador completo
(Incluye registro en Cognito y base de datos local)
VERSIÓN CORREGIDA - Sin campo is_verified
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.models.enum import UserRole, AuthType, Gender
from app.core.security import hash_password
from app.api.v1.auth.service import cognito_service
import boto3
from app.config import settings
from datetime import datetime

def create_admin_user():
    """Crea un usuario administrador completo"""
    
    print("🔐 Creación de Usuario Administrador\n")
    
    # Pedir datos del admin
    email = input("Email del admin: ").strip()
    password = input("Contraseña (mín 8 caracteres, con mayúsculas, números y especiales): ").strip()
    first_name = input("Nombre: ").strip()
    last_name = input("Apellido: ").strip()
    
    # Atributos adicionales requeridos por tu Cognito
    print("\n📝 Atributos adicionales (requeridos por tu configuración de Cognito):")
    gender = input("Género (M/F/prefer_not_say) [default: M]: ").strip() or "M"
    birthdate = input("Fecha de nacimiento (YYYY-MM-DD) [default: 1990-01-01]: ").strip() or "1990-01-01"
    picture = input("URL de imagen de perfil [default: https://via.placeholder.com/150]: ").strip() or "https://via.placeholder.com/150"
    
    db = SessionLocal()
    
    try:
        # 1. Verificar si el usuario ya existe en la BD local
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n⚠️  El usuario {email} ya existe en la base de datos.")
            
            if existing_user.role == UserRole.ADMIN:
                print("   Ya es administrador.")
                return
            
            response = input("¿Quieres convertirlo en admin? (s/n): ")
            if response.lower() == 's':
                existing_user.role = UserRole.ADMIN
                db.commit()
                print(f"✅ {email} ahora es ADMIN en la base de datos local.")
                
                # Actualizar en Cognito también
                if existing_user.cognito_sub:
                    update_cognito_role(email, "admin")
                
            return
        
        # 2. Registrar en Cognito
        print("\n📝 Registrando en AWS Cognito...")
        
        client = boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Registrar usuario con rol de admin
        response = client.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": first_name},
                {"Name": "family_name", "Value": last_name},
                {"Name": "custom:role", "Value": "admin"},  # ✅ ADMIN desde el inicio
                {"Name": "gender", "Value": gender},  # ✅ Requerido
                {"Name": "birthdate", "Value": birthdate},  # ✅ Requerido
                {"Name": "picture", "Value": picture}  # ✅ Requerido
            ]
        )
        
        cognito_sub = response["UserSub"]
        print(f"✅ Usuario creado en Cognito (sub: {cognito_sub})")
        
        # 3. Auto-confirmar el usuario (para pruebas)
        try:
            client.admin_confirm_sign_up(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=email
            )
            print("✅ Usuario confirmado automáticamente")
        except Exception as e:
            print(f"⚠️  No se pudo auto-confirmar: {str(e)}")
            print("   Deberás confirmar manualmente con el código del email.")
        
        # 4. Crear en base de datos local
        print("\n💾 Creando en base de datos local...")
        
        hashed_password = hash_password(password)
        
        # Convertir género a enum
        gender_enum = Gender.MALE
        if gender.upper() == "F":
            gender_enum = Gender.FEMALE
        elif gender.upper() == "PREFER_NOT_SAY":
            gender_enum = Gender.PREFER_NOT_SAY
        
        # Convertir birthdate string a date
        birth_date_obj = datetime.strptime(birthdate, "%Y-%m-%d").date()
        
        # ✅ CREAR USUARIO - SIN is_verified (no existe en el modelo)
        new_user = User(
            cognito_sub=cognito_sub,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            gender=gender_enum,
            date_of_birth=birth_date_obj,
            profile_picture=picture,
            auth_type=AuthType.EMAIL,
            role=UserRole.ADMIN,
            account_status=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"\n🎉 ¡Usuario administrador creado exitosamente!")
        print(f"\n📋 Detalles:")
        print(f"   User ID: {new_user.user_id}")
        print(f"   Email: {new_user.email}")
        print(f"   Nombre: {new_user.first_name} {new_user.last_name}")
        print(f"   Rol: {new_user.role.value}")
        print(f"   Cognito Sub: {cognito_sub}")
        print(f"   Género: {new_user.gender.value}")
        print(f"   Fecha de nacimiento: {new_user.date_of_birth}")
        print(f"\n🔑 Credenciales de acceso:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"\n👉 Ahora puedes hacer login en: POST /api/v1/auth/login")
        
    except client.exceptions.UsernameExistsException:
        print(f"\n❌ El email {email} ya existe en Cognito.")
        print("   Opciones:")
        print("   1. Usa otro email")
        print("   2. Si es tu usuario, ignora Cognito y créalo solo en BD local")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"\n🔍 Tipo de error: {type(e).__name__}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def update_cognito_role(email: str, role: str):
    """Actualiza el rol de un usuario en Cognito"""
    try:
        client = boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        client.admin_update_user_attributes(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {"Name": "custom:role", "Value": role}
            ]
        )
        
        print(f"✅ Rol actualizado en Cognito a: {role}")
    
    except Exception as e:
        print(f"⚠️  No se pudo actualizar Cognito: {str(e)}")
        print("   Actualízalo manualmente en AWS Console.")


if __name__ == "__main__":
    import os
    
    print("\n" + "="*70)
    print("🔐 CREACIÓN DE ADMINISTRADOR - BEFIT")
    print("="*70)
    
    # Verificar directorio
    print(f"\n📂 Directorio actual: {os.getcwd()}")
    print(f"📂 ¿Existe befit.db?: {os.path.exists('befit.db')}")
    
    if not os.path.exists('befit.db'):
        print("\n❌ ERROR: No se encuentra befit.db")
        print("💡 Ejecuta primero: python init_db.py")
        exit(1)
    
    # Verificar conexión
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Conexión a base de datos exitosa\n")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        print("💡 Ejecuta: python init_db.py")
        exit(1)
    
    create_admin_user()