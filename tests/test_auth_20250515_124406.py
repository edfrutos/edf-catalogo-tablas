# Script: test_auth_20250515_124406.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_auth_20250515_124406.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from pymongo import MongoClient
import os
from dotenv import load_dotenv
import scrypt
import base64

def verify_password(password, stored_password):
    try:
        print("\nDebug de verificación de contraseña:")
        
        # El formato es: scrypt:N:r:p$salt$hash
        params, salt, stored_hash = stored_password.split('$')
        print(f"Parámetros: {params}")
        print(f"Salt: {salt}")
        print(f"Hash almacenado: {stored_hash}")
        
        # Extraer parámetros
        scrypt_params = params.split(':')
        if len(scrypt_params) != 4:
            print(f"Parámetros scrypt inválidos: {params}")
            return False
            
        n = int(scrypt_params[1])  # 32768
        r = int(scrypt_params[2])  # 8
        p = int(scrypt_params[3])  # 1
        print(f"Parámetros extraídos - N: {n}, r: {r}, p: {p}")
        
        # Convertir salt de base64 a bytes
        salt_bytes = base64.b64decode(salt + '==')
        print(f"Salt en bytes: {salt_bytes.hex()}")
        
        # Generar hash de la contraseña proporcionada
        password_hash = scrypt.hash(password.encode('utf-8'), salt_bytes, N=n, r=r, p=p).hex()
        print(f"Hash generado: {password_hash}")
        print(f"Coinciden los hashes: {password_hash == stored_hash}")
        
        return password_hash == stored_hash
    except Exception as e:
        print(f"Error verificando contraseña: {str(e)}")
        return False

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client.get_default_database()

# Buscar el usuario
email = "edfrutos@gmail.com"
password = "script"

user = db.users.find_one({'email': email})
if user:
    print(f"Usuario encontrado: {user['email']}")
    print(f"Tipo de contraseña: {user.get('password_type', 'scrypt')}")
    print(f"Hash almacenado: {user['password']}")
    
    # Verificar contraseña
    if verify_password(password, user['password']):
        print("¡Contraseña correcta!")
    else:
        print("Contraseña incorrecta")
else:
    print("Usuario no encontrado")
