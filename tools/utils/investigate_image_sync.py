#!/usr/bin/env python3
"""
Script para investigar la sincronización entre archivos físicos y referencias en la base de datos
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def investigate_image_sync():
    """Investiga la sincronización entre archivos físicos y referencias en la base de datos"""
    
    print("🔍 INVESTIGANDO SINCRONIZACIÓN DE IMÁGENES")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    try:
        # Importar la aplicación Flask
        from main_app import create_app
        
        # Crear la aplicación
        app = create_app()
        
        with app.app_context():
            # Importar funciones de base de datos
            from app.database import get_mongo_db
            
            # Obtener la base de datos
            db = get_mongo_db()
            if db is None:
                print("   ❌ No se pudo conectar a la base de datos")
                return False
            
            # 1. Contar archivos físicos
            upload_dir = os.path.join(app.static_folder, 'uploads')
            physical_files = []
            
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        physical_files.append(filename)
            
            print(f"   📁 Archivos físicos en uploads/: {len(physical_files)}")
            
            # 2. Obtener referencias en la base de datos
            collection = db["spreadsheets"]
            catalogs = list(collection.find({}))
            
            db_references = []
            catalog_details = []
            
            for catalog in catalogs:
                catalog_id = catalog.get("_id")
                catalog_name = catalog.get("name", "Sin nombre")
                rows = catalog.get("rows", [])
                
                catalog_images = []
                
                for row_index, row in enumerate(rows):
                    images = row.get("images", [])
                    
                    for img in images:
                        if img not in db_references:
                            db_references.append(img)
                        catalog_images.append({
                            'row': row_index + 1,
                            'image': img
                        })
                
                if catalog_images:
                    catalog_details.append({
                        'name': catalog_name,
                        'id': catalog_id,
                        'images': catalog_images
                    })
            
            print(f"   🗄️  Referencias en base de datos: {len(db_references)}")
            
            # 3. Análisis de sincronización
            print(f"\n" + "="*50)
            print("ANÁLISIS DE SINCRONIZACIÓN")
            print("="*50)
            
            # Archivos físicos sin referencia en DB
            orphaned_files = [f for f in physical_files if f not in db_references]
            print(f"📁 Archivos huérfanos (físicos sin DB): {len(orphaned_files)}")
            
            # Referencias en DB sin archivo físico
            missing_files = [f for f in db_references if f not in physical_files and not f.startswith('http')]
            print(f"🗄️  Referencias faltantes (DB sin físico): {len(missing_files)}")
            
            # Archivos sincronizados
            synced_files = [f for f in physical_files if f in db_references]
            print(f"✅ Archivos sincronizados: {len(synced_files)}")
            
            # 4. Detalles por catálogo
            print(f"\n" + "="*50)
            print("DETALLES POR CATÁLOGO")
            print("="*50)
            
            for catalog in catalog_details:
                print(f"📋 {catalog['name']} (ID: {catalog['id']})")
                for img_info in catalog['images']:
                    status = "✅" if img_info['image'] in physical_files else "❌"
                    print(f"   {status} Fila {img_info['row']}: {img_info['image']}")
                print()
            
            # 5. Muestra de archivos huérfanos
            if orphaned_files:
                print(f"\n" + "="*50)
                print("MUESTRA DE ARCHIVOS HUÉRFANOS (primeros 10)")
                print("="*50)
                for i, filename in enumerate(orphaned_files[:10]):
                    print(f"   {i+1}. {filename}")
                if len(orphaned_files) > 10:
                    print(f"   ... y {len(orphaned_files) - 10} más")
            
            # 6. Recomendaciones
            print(f"\n" + "="*50)
            print("RECOMENDACIONES")
            print("="*50)
            
            if orphaned_files:
                print(f"⚠️  Hay {len(orphaned_files)} archivos físicos sin referencia en la base de datos")
                print(f"   Estos archivos no se mostrarán en los catálogos")
                print(f"   Opciones:")
                print(f"   1. Eliminar archivos huérfanos para ahorrar espacio")
                print(f"   2. Crear referencias en la base de datos")
                print(f"   3. Migrar archivos a S3 y eliminar locales")
            
            if missing_files:
                print(f"⚠️  Hay {len(missing_files)} referencias en DB sin archivo físico")
                print(f"   Estas referencias causarán errores 404")
                print(f"   Recomendación: Limpiar referencias huérfanas de la base de datos")
            
            if not orphaned_files and not missing_files:
                print(f"✅ Sincronización perfecta entre archivos físicos y base de datos")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    
    print("🚀 INICIANDO INVESTIGACIÓN DE SINCRONIZACIÓN DE IMÁGENES")
    print("=" * 60)
    
    # Ejecutar investigación
    success = investigate_image_sync()
    
    if success:
        print(f"\n🎉 Investigación completada")
        return True
    else:
        print(f"\n❌ La investigación no se completó correctamente")
        return False

if __name__ == "__main__":
    main()
