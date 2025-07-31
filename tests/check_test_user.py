from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client.get_default_database()

# Buscar el usuario de prueba
test_user = db.users.find_one({'email': 'test@example.com'})
if test_user:
    print("Usuario de prueba encontrado:")
    print(f"Email: {test_user['email']}")
    print(f"Nombre: {test_user.get('nombre', 'No especificado')}")
    print(f"Tipo de contraseña: {test_user.get('password_type', 'No especificado')}")
    print(f"Hash de contraseña: {test_user['password']}")
else:
    print("Usuario de prueba no encontrado")
