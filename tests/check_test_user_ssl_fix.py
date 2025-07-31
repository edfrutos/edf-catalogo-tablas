# Script: check_test_user_ssl_fix.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 check_test_user_ssl_fix.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

from pymongo import MongoClient
import os
from dotenv import load_dotenv
import ssl

# Cargar variables de entorno
load_dotenv()

# Obtener URI base
mongo_uri = os.getenv('MONGO_URI')

# Conectar a MongoDB con configuración SSL modificada para macOS
client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)

try:
    # Probar conexión
    client.admin.command('ping')
    print("Conexión exitosa a MongoDB")
    
    # Obtener la base de datos
    db = client.get_default_database()
    
    # Buscar el usuario de prueba
    test_user = db.users.find_one({'email': 'test@example.com'})
    if test_user:
        print("\nUsuario de prueba encontrado:")
        print(f"Email: {test_user['email']}")
        print(f"Nombre: {test_user.get('nombre', 'No especificado')}")
        print(f"Tipo de contraseña: {test_user.get('password_type', 'No especificado')}")
        print(f"Hash de contraseña: {test_user['password']}")
        
        # Mostrar otros campos si existen
        if 'fecha_registro' in test_user:
            print(f"Fecha de registro: {test_user['fecha_registro']}")
        if 'ultimo_acceso' in test_user:
            print(f"Último acceso: {test_user['ultimo_acceso']}")
        if 'activo' in test_user:
            print(f"Activo: {test_user['activo']}")
    else:
        print("\nUsuario de prueba no encontrado")
        
        # Mostrar cuántos usuarios hay en total
        total_users = db.users.count_documents({})
        print(f"Total de usuarios en la base de datos: {total_users}")
        
        if total_users > 0:
            print("\nPrimeros 5 usuarios:")
            for user in db.users.find().limit(5):
                print(f"- {user.get('email', 'sin email')} ({user.get('nombre', 'sin nombre')})")
    
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")
finally:
    client.close()
