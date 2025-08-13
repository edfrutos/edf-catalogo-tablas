#!/usr/bin/env python3
"""
Script mejorado para restaurar imágenes identificadas y crear catálogo para no clasificadas
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def restore_images_with_fallback():
    """Restaura imágenes identificadas y crea catálogo para no clasificadas"""
    
    print("🔄 RESTAURACIÓN MEJORADA DE IMÁGENES")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    try:
        # Importar la aplicación Flask
        from main_app import create_app
        
        # Crear la aplicación
        app = create_app()
        
        with app.app_context():
            # Importar funciones de base de datos y S3
            from app.database import get_mongo_db
            from app.utils.s3_utils import upload_file_to_s3
            
            # Obtener la base de datos
            db = get_mongo_db()
            if db is None:
                print("   ❌ No se pudo conectar a la base de datos")
                return False
            
            collection = db["spreadsheets"]
            upload_dir = os.path.join(app.static_folder, 'uploads')
            
            # Obtener archivos físicos
            physical_files = []
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        physical_files.append(filename)
            
            print(f"   📁 Archivos físicos encontrados: {len(physical_files)}")
            
            # Obtener catálogos existentes
            catalogs = list(collection.find({}))
            print(f"   📋 Catálogos existentes: {len(catalogs)}")
            
            # Identificar imágenes por catálogo
            catalog_images = {}
            unmatched_images = []
            
            # Buscar imágenes que coincidan con nombres de catálogos
            for filename in physical_files:
                matched_catalog = None
                
                # Buscar por patrones específicos
                if filename.startswith('Conectores_'):
                    # Buscar catálogo "Conectores y cables"
                    for catalog in catalogs:
                        if 'conectores' in catalog.get("name", "").lower():
                            matched_catalog = catalog
                            break
                
                elif filename.startswith('storage_units.xlsx_'):
                    # Buscar catálogo relacionado con storage
                    for catalog in catalogs:
                        if 'storage' in catalog.get("name", "").lower():
                            matched_catalog = catalog
                            break
                
                elif filename.startswith('tabla.csv_'):
                    # Buscar catálogo relacionado con tabla
                    for catalog in catalogs:
                        if 'tabla' in catalog.get("name", "").lower():
                            matched_catalog = catalog
                            break
                
                elif filename.startswith('Catalogo_hecho_a_mano_'):
                    # Buscar catálogo manual
                    for catalog in catalogs:
                        if 'manual' in catalog.get("name", "").lower() or 'hecho' in catalog.get("name", "").lower():
                            matched_catalog = catalog
                            break
                
                if matched_catalog:
                    catalog_id = str(matched_catalog.get("_id"))
                    if catalog_id not in catalog_images:
                        catalog_images[catalog_id] = []
                    catalog_images[catalog_id].append(filename)
                else:
                    unmatched_images.append(filename)
            
            # Mostrar resultados
            print(f"\n" + "="*50)
            print("ANÁLISIS DE CLASIFICACIÓN")
            print("="*50)
            print(f"📊 Imágenes clasificadas: {sum(len(imgs) for imgs in catalog_images.values())}")
            print(f"📊 Imágenes sin clasificar: {len(unmatched_images)}")
            
            for catalog_id, images in catalog_images.items():
                catalog = next((c for c in catalogs if str(c.get("_id")) == catalog_id), None)
                if catalog:
                    catalog_name = catalog.get("name", "Sin nombre")
                    print(f"   📋 {catalog_name}: {len(images)} imágenes")
            
            # Restaurar imágenes clasificadas
            restored_count = 0
            failed_count = 0
            
            print(f"\n🔄 RESTAURANDO IMÁGENES CLASIFICADAS")
            print("=" * 50)
            
            for catalog_id, images in catalog_images.items():
                catalog = collection.find_one({"_id": catalog_id})
                if not catalog:
                    print(f"   ❌ Catálogo no encontrado: {catalog_id}")
                    failed_count += len(images)
                    continue
                
                catalog_name = catalog.get("name", "Sin nombre")
                print(f"   📋 Restaurando {len(images)} imágenes a '{catalog_name}'")
                
                # Obtener filas del catálogo
                rows = catalog.get("rows", [])
                if not rows:
                    rows = [{"images": []}]
                
                # Agregar imágenes a la primera fila
                for filename in images:
                    file_path = os.path.join(upload_dir, filename)
                    
                    if os.path.exists(file_path):
                        try:
                            # Subir a S3
                            s3_result = upload_file_to_s3(file_path, filename)
                            
                            if s3_result.get('success'):
                                # Agregar a la fila
                                if "images" not in rows[0]:
                                    rows[0]["images"] = []
                                rows[0]["images"].append(filename)
                                
                                # Eliminar archivo local
                                os.remove(file_path)
                                
                                restored_count += 1
                                print(f"      ✅ Restaurada: {filename}")
                            else:
                                print(f"      ❌ Error S3: {filename}")
                                failed_count += 1
                                
                        except Exception as e:
                            print(f"      ❌ Error: {filename} - {e}")
                            failed_count += 1
                    else:
                        print(f"      ⚠️  Archivo no encontrado: {filename}")
                        failed_count += 1
                
                # Actualizar el catálogo
                try:
                    collection.update_one(
                        {"_id": catalog_id},
                        {
                            "$set": {
                                "rows": rows,
                                "data": rows,
                                "updated_at": datetime.now()
                            }
                        }
                    )
                    print(f"   ✅ Catálogo '{catalog_name}' actualizado")
                    
                except Exception as e:
                    print(f"   ❌ Error actualizando catálogo: {e}")
                    failed_count += len(images)
            
            # Crear catálogo para imágenes no clasificadas
            if unmatched_images:
                print(f"\n📋 CREANDO CATÁLOGO PARA IMÁGENES NO CLASIFICADAS")
                print("=" * 50)
                
                # Migrar imágenes no clasificadas a S3
                migrated_images = []
                for filename in unmatched_images:
                    file_path = os.path.join(upload_dir, filename)
                    
                    if os.path.exists(file_path):
                        try:
                            s3_result = upload_file_to_s3(file_path, filename)
                            if s3_result.get('success'):
                                migrated_images.append(filename)
                                os.remove(file_path)
                                print(f"   ✅ Migrada: {filename}")
                            else:
                                print(f"   ❌ Error S3: {filename}")
                        except Exception as e:
                            print(f"   ❌ Error: {filename} - {e}")
                
                if migrated_images:
                    # Crear filas (máximo 10 imágenes por fila)
                    rows = []
                    for i in range(0, len(migrated_images), 10):
                        batch = migrated_images[i:i+10]
                        row = {
                            "images": batch,
                            "nota": f"Lote {i//10 + 1} de imágenes no clasificadas"
                        }
                        rows.append(row)
                    
                    # Crear el catálogo
                    catalog_data = {
                        "name": f"Imágenes No Clasificadas - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        "description": f"Catálogo automático con {len(migrated_images)} imágenes no clasificadas",
                        "headers": ["images", "nota"],
                        "rows": rows,
                        "data": rows,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "is_auto_generated": True
                    }
                    
                    try:
                        result = collection.insert_one(catalog_data)
                        if result.inserted_id:
                            print(f"   ✅ Catálogo creado con ID: {result.inserted_id}")
                            print(f"   📊 {len(rows)} filas creadas con {len(migrated_images)} imágenes")
                        else:
                            print(f"   ❌ Error al crear catálogo")
                            
                    except Exception as e:
                        print(f"   ❌ Error al crear catálogo: {e}")
            
            # Imprimir estadísticas finales
            print(f"\n" + "="*50)
            print("ESTADÍSTICAS FINALES")
            print("="*50)
            print(f"Imágenes restauradas a catálogos originales: {restored_count}")
            print(f"Imágenes migradas a catálogo no clasificado: {len(migrated_images) if 'migrated_images' in locals() else 0}")
            print(f"Errores: {failed_count}")
            print(f"Archivos locales eliminados: {restored_count + (len(migrated_images) if 'migrated_images' in locals() else 0)}")
            
            total_processed = restored_count + (len(migrated_images) if 'migrated_images' in locals() else 0)
            
            if total_processed > 0:
                print(f"\n✅ PROCESAMIENTO COMPLETADO")
                print(f"   🗄️  {total_processed} imágenes ahora referenciadas en la base de datos")
                print(f"   💾 Espacio liberado en servidor local")
                return True
            else:
                print(f"\n❌ No se pudo procesar ninguna imagen")
                return False
            
    except Exception as e:
        print(f"   ❌ Error en procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    
    print("🚀 INICIANDO RESTAURACIÓN MEJORADA DE IMÁGENES")
    print("=" * 60)
    
    # Ejecutar restauración
    success = restore_images_with_fallback()
    
    if success:
        print(f"\n🎉 Restauración completada exitosamente")
        print(f"💡 Las imágenes han sido procesadas y referenciadas en la base de datos")
        return True
    else:
        print(f"\n❌ La restauración no se completó correctamente")
        return False

if __name__ == "__main__":
    main()
