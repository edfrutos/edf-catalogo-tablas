#!/usr/bin/env python3
import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
import hashlib
from datetime import datetime

def main():
    # Cargar variables de entorno
    load_dotenv()
    MONGO_URI = os.getenv('MONGO_URI')
    
    # Conectar a MongoDB
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        retryWrites=True,
        w='majority'
    )
    db = client['app_catalogojoyero_nueva']
    catalog_collection = db['67b8c24a7fdc72dd4d8703cf']
    
    # Obtener todas las tablas únicas
    tables = catalog_collection.distinct('table')
    print(f"Encontradas {len(tables)} tablas únicas")
    
    total_duplicates = 0
    total_processed = 0
    
    for table in tables:
        print(f"\nProcesando tabla: {table}")
        
        # Obtener todos los registros de la tabla
        records = list(catalog_collection.find({'table': table}))
        print(f"Total registros encontrados: {len(records)}")
        
        # Diccionario para almacenar registros únicos por tabla
        unique_records = {}
        duplicates = []
        
        for record in records:
            # Crear un diccionario con los valores de los campos (excluyendo campos de sistema)
            values = {k: v for k, v in record.items() if k not in ['_id', 'table', 'Número', 'owner_email', 'owner_name', 'owner_username', 'created_at', 'created_by', 'row_hash', 'import_batch']}
            
            # Crear hash de los valores
            row_values = [str(v) for v in values.values() if v is not None]
            row_hash = hashlib.md5(''.join(row_values).encode()).hexdigest()
            
            # Solo buscar duplicados dentro de la misma tabla
            if row_hash in unique_records:
                duplicates.append(record['_id'])
            else:
                unique_records[row_hash] = record
                # Actualizar el registro con el hash
                catalog_collection.update_one(
                    {'_id': record['_id']},
                    {'$set': {'row_hash': row_hash}}
                )
        
        # Eliminar duplicados
        if duplicates:
            result = catalog_collection.delete_many({'_id': {'$in': duplicates}})
            print(f"Eliminados {result.deleted_count} registros duplicados")
            total_duplicates += result.deleted_count
        
        total_processed += len(records)
        
        # Renumerar los registros restantes
        remaining = list(catalog_collection.find({'table': table}).sort('created_at', 1))
        for idx, record in enumerate(remaining, 1):
            catalog_collection.update_one(
                {'_id': record['_id']},
                {'$set': {'Número': idx}}
            )
        
        print(f"Registros únicos después de limpieza: {len(remaining)}")
    
    print(f"\nResumen final:")
    print(f"Total de registros procesados: {total_processed}")
    print(f"Total de duplicados eliminados: {total_duplicates}")
    print(f"Porcentaje de duplicación: {(total_duplicates/total_processed*100):.2f}%")

if __name__ == '__main__':
    main()
