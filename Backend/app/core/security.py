# Autor: Gabriel Vilchis
# Fecha: 08/11/2025
# Descripción:
# Este archivo define dos funciones relacionadas con la seguridad de contraseñas
# utilizando la librería bcrypt. Permite generar hashes seguros y verificar si
# una contraseña ingresada coincide con su hash almacenado.
import bcrypt 

# Esta  funcion hashea una contraseña en texto plano usando bcrypt


def hash_password(password: str) -> str:
    """
    Hashea una contraseña en texto plano usando bcrypt.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de la contraseña como string
    """
    # Convertir el password (str) a bytes
    password_bytes = password.encode('utf-8')
    
    # Generar un "salt" (cadena aleatoria para el hash)
    salt = bcrypt.gensalt()
    
    # Hashear el password
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # Convertir el hash (bytes) de nuevo a string para guardarlo en la BD
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash.
    
    Args:
        plain_password: Contraseña en texto plano a verificar
        hashed_password: Hash almacenado en la base de datos
        
    Returns:
        True si la contraseña coincide, False en caso contrario
    """
    plain_password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')

    try:
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except ValueError:
        # En caso de que el hash no sea válido
        return False