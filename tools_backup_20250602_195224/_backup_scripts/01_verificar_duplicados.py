#!/usr/bin/env python3
from pymongo import MongoClient
from collections import defaultdict
import json
from bson import ObjectId
from datetime import datetime
import os
import sys

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

def crear_backup(collection, backup_dir='backups'):
    """
    Crea un backup de la colección antes de realizar cambios
    """
    try:
        # Crear directorio de backups si no existe
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
        
        # Obtener todos los documentos
        documentos = list(collection.find({}))
        
        # Guardar en archivo JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(documentos, f, cls=JSONEncoder, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Backup creado exitosamente: {backup_file}")
        return True
    except Exception as e:
        print(f"\n❌ Error al crear backup: {e}")
        return False

def contar_informacion(doc):
    """
    Calcula una puntuación basada en la cantidad de información del registro.
    """
    puntuacion = 0
    campos_no_vacios = 0
    
    for key, value in doc.items():
        if key != '_id':
            if value:
                campos_no_vacios += 1
                if key in ['Descripción', 'Precio', 'Stock', 'Valor']:
                    puntuacion += 2
                elif key == 'Imagenes' and isinstance(value, list):
                    puntuacion += len(value) * 2
                else:
                    puntuacion += 1
                
                if isinstance(value, str):
                    puntuacion += len(value.strip()) * 0.01

    return puntuacion, campos_no_vacios

def mostrar_registro(doc):
    """
    Muestra un registro de forma legible
    """
    print("\nDetalles del registro:")
    print("-" * 50)
    for key, value in doc.items():
        print(f"{key}: {value}")

def restaurar_backup(backup_file):
    """
    Restaura un backup específico
    """
    uri = "mongodb+srv://cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?authSource=%24external&authMechanism=MONGODB-AWS&retryWrites=true&w=majority"
    
    try:
        # Establecer conexión
        client = MongoClient(uri)
        db = client.app_catalogojoyero_nueva
        collection = db['67b8c24a7fdc72dd4d8703cf']
        
        # Verificar la conexión
        client.admin.command('ping')
        print("✅ Conexión establecida correctamente")
        
        # Verificar que el archivo existe
        if not os.path.exists(backup_file):
            print(f"\n❌ Error: El archivo de backup no existe: {backup_file}")
            return False
        
        # Crear backup del estado actual antes de restaurar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_antes_restauracion = f'backups/pre_restauracion_{timestamp}.json'
        print("\nCreando backup del estado actual antes de restaurar...")
        crear_backup(collection)
        
        print(f"\nRestaurando desde backup: {backup_file}")
        with open(backup_file, 'r', encoding='utf-8') as f:
            documentos = json.load(f)
        
        # Convertir strings de ObjectId de vuelta a ObjectId
        for doc in documentos:
            doc['_id'] = ObjectId(doc['_id'])
        
        # Eliminar documentos actuales
        resultado_delete = collection.delete_many({})
        print(f"Documentos eliminados: {resultado_delete.deleted_count}")
        
        # Insertar documentos del backup
        resultado_insert = collection.insert_many(documentos)
        print(f"Documentos restaurados: {len(resultado_insert.inserted_ids)}")
        
        print(f"\n✅ Backup restaurado exitosamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al restaurar backup: {e}")
        return False
        
    finally:
        client.close()

def verificar_y_gestionar_duplicados():
    """
    Verifica y gestiona duplicados en la base de datos
    """
    uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/?retryWrites=true&w=majority"
    
    try:
        client = MongoClient(uri)
        db = client.app_catalogojoyero_nueva
        collection = db['67b8c24a7fdc72dd4d8703cf']
        
        # Verificar la conexión
        client.admin.command('ping')
        print("✅ Conexión establecida correctamente")
        
        # Crear backup antes de cualquier modificación
        print("\nCreando backup de seguridad...")
        if not crear_backup(collection):
            print("❌ No se pudo crear el backup. Operación cancelada.")
            return
        
        descripciones = defaultdict(list)
        print("\nBuscando duplicados...")
        
        # Obtener todos los documentos
        documentos = collection.find({})
        
        # Agrupar por descripción
        for doc in documentos:
            if 'Descripción' in doc:
                desc = doc.get('Descripción', '').strip().lower()
                if desc:
                    descripciones[desc].append(doc)
        
        # Procesar duplicados
        total_duplicados = 0
        total_eliminados = 0
        
        for desc, items in descripciones.items():
            if len(items) > 1:
                total_duplicados += 1
                print(f"\n{'='*80}")
                print(f"\nDuplicados encontrados para descripción: '{desc}'")
                print(f"Número de registros duplicados: {len(items)}")
                
                # Evaluar cada registro
                registros_evaluados = []
                for doc in items:
                    puntuacion, campos = contar_informacion(doc)
                    registros_evaluados.append((doc, puntuacion, campos))
                
                registros_evaluados.sort(key=lambda x: (x[1], x[2]), reverse=True)
                
                print("\nAnálisis de registros:")
                for i, (doc, puntuacion, campos) in enumerate(registros_evaluados, 1):
                    print(f"\nRegistro {i}:")
                    print(f"Puntuación: {puntuacion:.2f}")
                    print(f"Campos con información: {campos}")
                    mostrar_registro(doc)
                
                registro_mantener = registros_evaluados[0][0]
                print("\n✅ Se mantendrá el registro más completo:")
                mostrar_registro(registro_mantener)
                
                # Eliminar duplicados
                for doc, _, _ in registros_evaluados[1:]:
                    collection.delete_one({'_id': doc['_id']})
                    total_eliminados += 1
                
                print(f"\nSe eliminaron {len(items)-1} registros duplicados")
        
        # Resumen final
        print("\n" + "="*80)
        print(f"\nResumen de la operación:")
        print(f"Total de grupos de duplicados encontrados: {total_duplicados}")
        print(f"Total de registros eliminados: {total_eliminados}")
        
        if total_duplicados == 0:
            print("\nNo se encontraron descripciones duplicadas.")
        
        print("\nNota: Se ha creado un backup antes de realizar los cambios.")
        print("Para restaurar el backup en caso necesario, use la función restaurar_backup()")
    
    except Exception as e:
        print(f"Error al conectar con MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Para verificar duplicados:")
        print("    python3 verificar_duplicados.py --check")
        print("  Para restaurar un backup:")
        print("    python3 verificar_duplicados.py --restore backups/nombre_backup.json")
        print("  Para listar backups disponibles:")
        print("    python3 verificar_duplicados.py --list")
        sys.exit(1)

    if sys.argv[1] == '--check':
        print("Iniciando verificación de duplicados...")
        verificar_y_gestionar_duplicados()
    elif sys.argv[1] == '--restore':
        if len(sys.argv) != 3:
            print("Error: Debe especificar el archivo de backup")
            print("Uso: python3 verificar_duplicados.py --restore backups/nombre_backup.json")
            sys.exit(1)
        backup_file = sys.argv[2]
        print(f"Restaurando backup desde: {backup_file}")
        restaurar_backup(backup_file)
    elif sys.argv[1] == '--list':
        if not os.path.exists('backups'):
            print("No hay backups disponibles")
        else:
            print("\nBackups disponibles:")
            for backup in sorted(os.listdir('backups')):
                if backup.endswith('.json'):
                    backup_path = os.path.join('backups', backup)
                    size = os.path.getsize(backup_path) / 1024  # KB
                    fecha = datetime.fromtimestamp(os.path.getctime(backup_path))
                    print(f"- {backup}")
                    print(f"  Creado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Tamaño: {size:.2f} KB")
    else:
        print("Opción no válida")
        print("Use --check para verificar duplicados")
        print("Use --restore para restaurar un backup")
        print("Use --list para ver backups disponibles")