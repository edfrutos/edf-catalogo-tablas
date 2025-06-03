import pymongo
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
from pymongo.errors import ConnectionFailure, AutoReconnect, ConfigurationError
import time

# Reemplaza esto con tu string de conexión real
MONGO_URI = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/?retryWrites=true&w=majority"

def test_connection():
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        # Forzar la conexión
        print("Intentando conectar a MongoDB...")
        client.admin.command('ping')
        print("Conexión a MongoDB establecida correctamente")
        
        # Listar bases de datos disponibles
        print("\nBases de datos disponibles:")
        for db_name in client.list_database_names():
            print(f" - {db_name}")
            
        return client
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        return None

# Intentar la conexión
client = test_connection()

if client:
    # Si la conexión fue exitosa, intenta realizar algunas operaciones
    try:
        db_name = input("\nIntroduce el nombre de la base de datos a usar: ")
        db = client[db_name]
        
        print("\nColecciones disponibles:")
        for collection in db.list_collection_names():
            print(f" - {collection}")
            
        collection_name = input("\nIntroduce el nombre de una colección para contar documentos: ")
        count = db[collection_name].count_documents({})
        print(f"La colección {collection_name} tiene {count} documentos")
        
    except Exception as e:
        print(f"Error al realizar operaciones: {e}")
    finally:
        client.close()