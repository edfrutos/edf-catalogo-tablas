from pymongo import MongoClient

# URI de conexión a MongoDB Atlas
uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"

try:
    # Crear cliente de MongoDB
    client = MongoClient(uri)
    # Probar conexión
    print("Conexión exitosa a MongoDB Atlas")
    # Listar bases de datos
    print("Bases de datos disponibles:", client.list_database_names())
except Exception as e:
    print("Error al conectar a MongoDB Atlas:", e)