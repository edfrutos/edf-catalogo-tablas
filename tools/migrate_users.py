#!/usr/bin/env python3
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import scrypt
import base64
from app.models import get_users_collection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database('app_catalogojoyero_nueva')

# Colecciones
users = get_users_collection()
users_unified = db['users_unified']

def convert_scrypt_to_werkzeug(scrypt_hash, password):
    """Convierte un hash scrypt a formato Werkzeug."""
    try:
        # Extraer parámetros del hash scrypt
        parts = scrypt_hash.split(':')
        if len(parts) != 4:
            return None
            
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt_and_hash = parts[4]
        
        # Extraer salt
        salt, _ = salt_and_hash.split('$')
        salt = bytes.fromhex(salt)
        
        # Verificar si la contraseña coincide con el hash scrypt
        if scrypt.hash(password.encode('utf-8'), salt, N=n, r=r, p=p).hex() == salt_and_hash.split('$')[1]:
            # Si coincide, generar un nuevo hash Werkzeug
            return generate_password_hash(password)
        
        return None
    except Exception as e:
        logger.error(f"Error convirtiendo scrypt a werkzeug: {str(e)}")
        return None

def migrate_user(user_id):
    try:
        # Obtener datos de ambas colecciones
        user = users.find_one({'_id': user_id})
        unified = users_unified.find_one({'_id': user_id})
        
        # Si no existe en ninguna colección, saltar
        if not user and not unified:
            logger.error(f"Usuario no encontrado en ninguna colección: {user_id}")
            return
            
        # Usar el formato de 'users' como base
        merged_user = {
            '_id': user_id,
            'nombre': (user or {}).get('nombre', (unified or {}).get('nombre', (unified or {}).get('name', ''))),
            'email': (user or {}).get('email', (unified or {}).get('email', '')),
            'role': (user or {}).get('role', (unified or {}).get('role', 'user')),
            'created_at': (user or {}).get('created_at', datetime.utcnow().isoformat()),
            'updated_at': (user or {}).get('updated_at', datetime.utcnow().isoformat()),
            'last_login': (user or {}).get('last_login', None),
            'last_ip': (user or {}).get('last_ip', ''),
            'failed_attempts': (user or {}).get('failed_attempts', 0),
            'locked_until': (user or {}).get('locked_until', None),
            'num_tables': (user or {}).get('num_tables', 0),
            'tables_updated_at': (user or {}).get('tables_updated_at', None)
        }

        # Manejar el password
        password = None
        if user and 'password' in user:
            password = user['password']
        elif unified and 'password' in unified:
            password = unified['password']

        if password:
            # Convertir a string si es bytes
            if isinstance(password, bytes):
                password = password.decode('utf-8')
                
            # Determinar el tipo de hash
            if password.startswith('scrypt:'):
                merged_user['password'] = password
                merged_user['password_type'] = 'scrypt'
            elif password.startswith('$2b$'):
                merged_user['password'] = password
                merged_user['password_type'] = 'werkzeug'
            else:
                logger.warning(f"Formato de contraseña desconocido para {merged_user['email']}")
                merged_user['password'] = password
                merged_user['password_type'] = 'unknown'

        # Actualizar en la colección users
        result = users.update_one(
            {'_id': user_id},
            {'$set': merged_user},
            upsert=True
        )
        
        if result.modified_count > 0 or result.upserted_id:
            logger.info(f"Usuario migrado exitosamente: {merged_user['email']}")
            
            # Eliminar de users_unified si existe
            if unified:
                users_unified.delete_one({'_id': user_id})
                logger.info(f"Usuario eliminado de users_unified: {merged_user['email']}")
        
    except Exception as e:
        logger.error(f"Error migrando usuario {user_id}: {str(e)}")

def main():
    try:
        # Obtener todos los IDs únicos de ambas colecciones
        all_ids = set()
        for user in users.find({}, {'_id': 1}):
            all_ids.add(user['_id'])
        for user in users_unified.find({}, {'_id': 1}):
            all_ids.add(user['_id'])
            
        logger.info(f"Iniciando migración de {len(all_ids)} usuarios")
        
        # Migrar cada usuario
        for user_id in all_ids:
            migrate_user(user_id)
            
        logger.info("Migración completada")
        
    except Exception as e:
        logger.error(f"Error en la migración: {str(e)}")

if __name__ == "__main__":
    main()
