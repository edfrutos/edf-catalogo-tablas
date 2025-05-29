# Script: test_password_verify.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_password_verify.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv
import os
import certifi
from pymongo.server_api import ServerApi

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB Atlas
client = MongoClient(
    os.getenv('MONGO_URI'),
    tls=True,
    tlsCAFile=certifi.where(),
    server_api=ServerApi('1')
)

# Seleccionar la base de datos y colección
db = client['app_catalogojoyero']
users = db['users_unified']

def test_password(email, test_password):
    """Prueba una contraseña específica para un usuario"""
    user = users.find_one({'email': email})
    if not user:
        print(f"Usuario no encontrado: {email}")
        return
        
    print(f"\nProbando contraseña para {email}")
    stored_password = user['password']
    
    try:
        # Convertir la contraseña de prueba a bytes
        test_password_bytes = test_password.encode('utf-8')
        # Convertir el hash almacenado a bytes si es necesario
        stored_password_bytes = stored_password.encode('utf-8') if isinstance(stored_password, str) else stored_password
        
        # Intentar verificar
        result = bcrypt.checkpw(test_password_bytes, stored_password_bytes)
        print(f"Resultado de la verificación: {'Éxito' if result else 'Fallido'}")
        
    except Exception as e:
        print(f"Error al verificar: {str(e)}")

# Probar con la contraseña conocida
test_password('edfrutos@gmail.com', 'admin123')