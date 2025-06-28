#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()

try:
    # Obtener URI de MongoDB desde las variables de entorno
    mongo_uri = os.getenv('MONGO_URI')
    print(f"URI de MongoDB: {mongo_uri}")
    
    if not mongo_uri:
        print("ERROR: No se encontró MONGO_URI en el archivo .env")
        sys.exit(1)
    
    # Intentar conectar a MongoDB
    print("Intentando conectar a MongoDB...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # Probar la conexión
    client.admin.command('ismaster')
    print("✅ Conexión a MongoDB exitosa!")
    
    # Verificar la base de datos
    db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
    db = client[db_name]
    print(f"✅ Base de datos: {db_name}")
    
    # Verificar colecciones
    collections = db.list_collection_names()
    print(f"✅ Colecciones disponibles: {collections}")
    
    # Verificar usuarios
    if 'users' in collections:
        users_count = db.users.count_documents({})
        print(f"✅ Usuarios en la base de datos: {users_count}")
        
        # Buscar usuario admin
        admin_user = db.users.find_one({"email": "admin@example.com"})
        if admin_user:
            print(f"✅ Usuario admin encontrado: {admin_user.get('email')}")
        else:
            print("⚠️  Usuario admin no encontrado")
            
        # Mostrar algunos usuarios para referencia
        print("\n📋 Primeros 5 usuarios en la base de datos:")
        usuarios = list(db.users.find({}, {"email": 1, "nombre": 1, "role": 1}).limit(5))
        for i, user in enumerate(usuarios, 1):
            print(f"  {i}. Email: {user.get('email')}, Nombre: {user.get('nombre')}, Rol: {user.get('role')}")
    else:
        print("⚠️  Colección 'users' no existe")
    
    client.close()
    print("✅ Test de MongoDB completado exitosamente")
    
except Exception as e:
    print(f"❌ Error al conectar con MongoDB: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
