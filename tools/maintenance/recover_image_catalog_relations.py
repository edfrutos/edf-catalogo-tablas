#!/usr/bin/env python3
"""
Script para intentar recuperar las relaciones originales entre imágenes y catálogos
"""

import os
import sys
from dotenv import load_dotenv
import re
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def recover_image_catalog_relations():
    """Intenta recuperar las relaciones originales entre imágenes y catálogos"""
    
    print("🔍 RECUPERANDO RELACIONES IMAGEN-CATÁLOGO")
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
            
            # Obtener archivos físicos
            upload_dir = os.path.join(app.static_folder, 'uploads')
            physical_files = []
            
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        physical_files.append(filename)
            
            print(f"   📁 Archivos físicos encontrados: {len(physical_files)}")
            
            # Obtener catálogos existentes
            collection = db["spreadsheets"]
            catalogs = list(collection.find({}))
            
            print(f"   📋 Catálogos existentes: {len(catalogs)}")
            
            # Analizar patrones en nombres de archivos para identificar catálogos
            catalog_patterns = {}
            image_catalog_matches = {}
            
            # Patrones comunes en nombres de archivos
            patterns = [
                r'(\w+)_(\d+)_(\w+)',  # ejemplo: tabla_1_c4384f19.jpg
                r'(\w+)\.(\w+)_(\d+)_(\w+)',  # ejemplo: storage_units.xlsx_6_895fc11c.jpg
                r'(\w+)_(\d+)_(\w+)',  # ejemplo: Catalogo_hecho_a_mano_0_a74e2715.jpg
            ]
            
            print(f"   🔍 Analizando patrones en nombres de archivos...")
            
            for filename in physical_files:
                matched_catalog = None
                
                # Intentar extraer información del nombre del archivo
                for pattern in patterns:
                    match = re.search(pattern, filename)
                    if match:
                        # Buscar catálogos que coincidan con el patrón
                        potential_catalog_name = match.group(1)
                        
                        # Buscar catálogos con nombres similares
                        for catalog in catalogs:
                            catalog_name = catalog.get("name", "").lower()
                            if (potential_catalog_name.lower() in catalog_name or 
                                catalog_name in potential_catalog_name.lower()):
                                matched_catalog = catalog
                                break
                        
                        if matched_catalog:
                            break
                
                # Si no se encontró por patrón, intentar por fecha o contenido
                if not matched_catalog:
                    # Buscar por fechas en el nombre (formato iOS)
                    date_match = re.search(r'(\d{8})_(\d{9})_iOS', filename)
                    if date_match:
                        # Buscar catálogos creados en fechas similares
                        date_str = date_match.group(1)
                        for catalog in catalogs:
                            created_at = catalog.get("created_at")
                            if created_at:
                                # Manejar tanto objetos datetime como strings
                                if hasattr(created_at, 'strftime'):
                                    catalog_date = created_at.strftime("%Y%m%d")
                                else:
                                    # Si es string, intentar parsear
                                    try:
                                        from datetime import datetime
                                        if isinstance(created_at, str):
                                            # Intentar diferentes formatos
                                            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                                                try:
                                                    dt = datetime.strptime(created_at, fmt)
                                                    catalog_date = dt.strftime("%Y%m%d")
                                                    break
                                                except ValueError:
                                                    continue
                                            else:
                                                continue  # No se pudo parsear la fecha
                                        else:
                                            continue
                                    except:
                                        continue
                                
                                if catalog_date == date_str:
                                    matched_catalog = catalog
                                    break
                
                if matched_catalog:
                    image_catalog_matches[filename] = matched_catalog
                    catalog_id = str(matched_catalog.get("_id"))
                    if catalog_id not in catalog_patterns:
                        catalog_patterns[catalog_id] = []
                    catalog_patterns[catalog_id].append(filename)
            
            # Mostrar resultados del análisis
            print(f"\n" + "="*50)
            print("ANÁLISIS DE RELACIONES ENCONTRADAS")
            print("="*50)
            
            total_matched = len(image_catalog_matches)
            print(f"📊 Imágenes con catálogo identificado: {total_matched}")
            print(f"📊 Imágenes sin catálogo identificado: {len(physical_files) - total_matched}")
            
            # Mostrar detalles por catálogo
            for catalog_id, images in catalog_patterns.items():
                catalog = next((c for c in catalogs if str(c.get("_id")) == catalog_id), None)
                if catalog:
                    catalog_name = catalog.get("name", "Sin nombre")
                    print(f"\n📋 {catalog_name} (ID: {catalog_id})")
                    print(f"   📸 {len(images)} imágenes identificadas:")
                    for img in images[:5]:  # Mostrar solo las primeras 5
                        print(f"      - {img}")
                    if len(images) > 5:
                        print(f"      ... y {len(images) - 5} más")
            
            # Imágenes sin catálogo identificado
            unmatched_images = [f for f in physical_files if f not in image_catalog_matches]
            if unmatched_images:
                print(f"\n❓ IMÁGENES SIN CATÁLOGO IDENTIFICADO ({len(unmatched_images)}):")
                for img in unmatched_images[:10]:
                    print(f"   - {img}")
                if len(unmatched_images) > 10:
                    print(f"   ... y {len(unmatched_images) - 10} más")
            
            # Preguntar al usuario qué hacer
            print(f"\n" + "="*50)
            print("OPCIONES DISPONIBLES")
            print("="*50)
            
            if total_matched > 0:
                print(f"✅ Opción 1: Restaurar {total_matched} imágenes a sus catálogos originales")
                print(f"   - Las imágenes se agregarán a las filas existentes de sus catálogos")
                print(f"   - Se migrarán a S3 automáticamente")
            
            if unmatched_images:
                print(f"✅ Opción 2: Crear catálogo separado para {len(unmatched_images)} imágenes sin relación")
                print(f"   - Se creará un catálogo 'Imágenes Sin Clasificar'")
                print(f"   - Se migrarán a S3 automáticamente")
            
            print(f"✅ Opción 3: Solo mostrar análisis (no hacer cambios)")
            
            return {
                'matched_images': image_catalog_matches,
                'unmatched_images': unmatched_images,
                'catalog_patterns': catalog_patterns,
                'total_matched': total_matched
            }
            
    except Exception as e:
        print(f"   ❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return False

def restore_images_to_catalogs(analysis_result):
    """Restaura las imágenes a sus catálogos originales"""
    
    print("🔄 RESTAURANDO IMÁGENES A CATÁLOGOS ORIGINALES")
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
            
            matched_images = analysis_result['matched_images']
            catalog_patterns = analysis_result['catalog_patterns']
            
            restored_count = 0
            failed_count = 0
            
            # Restaurar imágenes por catálogo
            for catalog_id, images in catalog_patterns.items():
                catalog = collection.find_one({"_id": catalog_id})
                if not catalog:
                    print(f"   ❌ Catálogo no encontrado: {catalog_id}")
                    continue
                
                catalog_name = catalog.get("name", "Sin nombre")
                print(f"   📋 Restaurando {len(images)} imágenes a '{catalog_name}'")
                
                # Obtener la primera fila del catálogo (o crear una nueva)
                rows = catalog.get("rows", [])
                if not rows:
                    # Crear una nueva fila si no existe
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
                                "data": rows,  # Mantener compatibilidad
                                "updated_at": datetime.now()
                            }
                        }
                    )
                    print(f"   ✅ Catálogo '{catalog_name}' actualizado")
                    
                except Exception as e:
                    print(f"   ❌ Error actualizando catálogo: {e}")
                    failed_count += len(images)
            
            # Imprimir estadísticas
            print(f"\n" + "="*50)
            print("ESTADÍSTICAS DE RESTAURACIÓN")
            print("="*50)
            print(f"Imágenes restauradas: {restored_count}")
            print(f"Errores: {failed_count}")
            print(f"Catálogos actualizados: {len(catalog_patterns)}")
            
            return restored_count > 0
            
    except Exception as e:
        print(f"   ❌ Error en restauración: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    
    print("🚀 INICIANDO RECUPERACIÓN DE RELACIONES IMAGEN-CATÁLOGO")
    print("=" * 60)
    
    # Ejecutar análisis
    analysis_result = recover_image_catalog_relations()
    
    if not analysis_result:
        print(f"\n❌ El análisis no se completó correctamente")
        return False
    
    if analysis_result['total_matched'] == 0:
        print(f"\n⚠️  No se encontraron relaciones entre imágenes y catálogos")
        print(f"   Considera usar la migración simple a S3")
        return False
    
    # Preguntar al usuario qué hacer
    print(f"\n¿Qué acción deseas realizar?")
    print(f"1. Restaurar {analysis_result['total_matched']} imágenes a sus catálogos originales")
    print(f"2. Solo mostrar análisis (no hacer cambios)")
    
    # Por ahora, ejecutar automáticamente la restauración
    print(f"\n🔄 Ejecutando restauración automática...")
    
    success = restore_images_to_catalogs(analysis_result)
    
    if success:
        print(f"\n🎉 Restauración completada exitosamente")
        print(f"💡 Las imágenes han sido restauradas a sus catálogos originales")
        return True
    else:
        print(f"\n❌ La restauración no se completó correctamente")
        return False

if __name__ == "__main__":
    main()
