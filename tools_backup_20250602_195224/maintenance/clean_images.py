#!/usr/bin/env python3
import os
import shutil
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import sys

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar variables de entorno críticas
    if not os.environ.get('MONGO_URI'):
        print("ERROR: La variable de entorno MONGO_URI no está configurada.", file=sys.stderr)
        sys.exit(1)
    
    # Forzar el uso del bundle de certificados de certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    
    # Conectar a MongoDB usando la misma conexión que la aplicación Flask
    MONGO_URI = os.environ.get("MONGO_URI")
    try:
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1')
        )
        
        # Verificar conexión
        client.admin.command('ping')
        print("✅ Conexión exitosa a MongoDB")
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Conectar a la base de datos y colección
    db = client["app_catalogojoyero_nueva"]
    catalog_collection = db["67b8c24a7fdc72dd4d8703cf"]
    
    # Obtener el directorio base de la aplicación
    app_root_path = os.path.dirname(os.path.abspath(__file__))
    images_folder = os.path.join(app_root_path, "imagenes_subidas")
    
    if not os.path.exists(images_folder):
        print(f"❌ El directorio de imágenes {images_folder} no existe.")
        sys.exit(1)
    
    # Crear directorio para imágenes no utilizadas
    unused_folder = os.path.join(app_root_path, "unused_images")
    if not os.path.exists(unused_folder):
        os.makedirs(unused_folder)
        print(f"✅ Directorio creado: {unused_folder}")
    
    # Paso 1: Obtener todas las rutas de imágenes de MongoDB
    referenced_images = set()
    
    # Buscar en todos los documentos de la colección
    cursor = catalog_collection.find({})
    total_documents = 0
    documents_with_images = 0
    
    for doc in cursor:
        total_documents += 1
        images = doc.get("Imagenes", [])
        
        # Asegurar que images sea una lista
        if not isinstance(images, list):
            if images is None:
                images = []
            else:
                images = [images]
        
        if images and any(images):
            documents_with_images += 1
        
        # Procesar cada ruta de imagen
        for img_path in images:
            if not img_path:
                continue
                
            # Solo nos interesan las imágenes locales, no las de S3
            if not img_path.startswith('s3://'):
                # Normalizar la ruta: remover barra inicial si existe
                if img_path.startswith('/'):
                    img_path = img_path[1:]
                
                # Si es una ruta de "imagenes_subidas", extraer el nombre del archivo
                if "imagenes_subidas" in img_path:
                    img_filename = os.path.basename(img_path)
                    referenced_images.add(img_filename)
    
    print(f"📊 Total de documentos procesados: {total_documents}")
    print(f"📊 Documentos con imágenes: {documents_with_images}")
    print(f"📊 Imágenes referenciadas: {len(referenced_images)}")
    
    # Paso 2: Escanear el directorio de imágenes
    all_images = set()
    for filename in os.listdir(images_folder):
        if os.path.isfile(os.path.join(images_folder, filename)):
            all_images.add(filename)
    
    # Paso 3: Identificar imágenes no utilizadas
    unused_images = all_images - referenced_images
    
    print(f"📊 Total de archivos en el directorio: {len(all_images)}")
    print(f"📊 Imágenes no utilizadas: {len(unused_images)}")
    
    # Paso 4: Mover las imágenes no utilizadas
    moved_count = 0
    error_count = 0
    
    for img_name in unused_images:
        src_path = os.path.join(images_folder, img_name)
        dst_path = os.path.join(unused_folder, img_name)
        
        try:
            shutil.move(src_path, dst_path)
            moved_count += 1
            print(f"🔄 Movida: {img_name}")
        except Exception as e:
            error_count += 1
            print(f"❌ Error al mover {img_name}: {e}")
    
    # Paso 5: Imprimir estadísticas finales
    print("\n--- RESUMEN DE LIMPIEZA ---")
    print(f"📊 Total de imágenes encontradas: {len(all_images)}")
    print(f"📊 Imágenes referenciadas en la BD: {len(referenced_images)}")
    print(f"📊 Imágenes no utilizadas: {len(unused_images)}")
    print(f"✅ Imágenes movidas con éxito: {moved_count}")
    if error_count > 0:
        print(f"❌ Errores durante el proceso: {error_count}")
    
    print(f"\nLas imágenes no utilizadas se han movido a: {unused_folder}")
    print("Para restaurar alguna imagen, simplemente muévala de vuelta al directorio 'imagenes_subidas'.")

if __name__ == "__main__":
    main()

