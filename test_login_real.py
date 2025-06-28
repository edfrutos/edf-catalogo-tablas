#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import hashlib
import base64
from werkzeug.security import check_password_hash

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def verify_password_test(password, stored_password):
    """Función de prueba para verificar contraseñas"""
    try:
        logger.info(f"Probando verificación de contraseña")
        logger.info(f"Password ingresada: {password}")
        logger.info(f"Hash almacenado: {stored_password[:50]}...")
        
        # Detectar tipo de hash
        if stored_password.startswith('scrypt:'):
            logger.info("Detectado hash tipo scrypt")
            
            # Primero probar con check_password_hash de Werkzeug
            try:
                result = check_password_hash(stored_password, password)
                logger.info(f"Resultado con check_password_hash: {result}")
                if result:
                    return True
            except Exception as e:
                logger.error(f"Error con check_password_hash: {e}")
            
            # Probar verificación manual de scrypt
            try:
                parts = stored_password.split('$')
                if len(parts) != 3:
                    logger.error(f"Formato scrypt inválido: {len(parts)} partes")
                    return False
                    
                params = parts[0].split(':')  # [scrypt, N, r, p]
                if len(params) != 4:
                    logger.error(f"Parámetros scrypt inválidos: {len(params)} parámetros")
                    return False
                    
                n = int(params[1])  # 32768
                r = int(params[2])  # 8
                p = int(params[3])  # 1
                
                logger.info(f"Parámetros scrypt: n={n}, r={r}, p={p}")
                
                # Decodificar salt
                try:
                    salt = base64.b64decode(parts[1] + '==')
                    logger.info(f"Salt decodificado: {len(salt)} bytes")
                except Exception as e:
                    logger.error(f"Error decodificando salt: {e}")
                    return False
                
                stored_hash = parts[2]
                logger.info(f"Hash almacenado: {stored_hash[:20]}...")
                
                # Calcular hash con hashlib.scrypt
                hashed_bytes = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=n, r=r, p=p, dklen=64)
                
                # Probar tanto hex como base64
                password_hash_hex = hashed_bytes.hex()
                password_hash_b64 = base64.b64encode(hashed_bytes).decode('utf-8').rstrip('=')
                
                logger.info(f"Hash calculado (hex): {password_hash_hex[:20]}...")
                logger.info(f"Hash calculado (b64): {password_hash_b64[:20]}...")
                
                if password_hash_hex == stored_hash:
                    logger.info("✅ Match con formato hex")
                    return True
                elif password_hash_b64 == stored_hash:
                    logger.info("✅ Match con formato base64")
                    return True
                else:
                    logger.error("❌ No hay match con ningún formato")
                    return False
                    
            except Exception as e:
                logger.error(f"Error en verificación manual scrypt: {e}")
                return False
        else:
            # Probar con check_password_hash para otros tipos
            result = check_password_hash(stored_password, password)
            logger.info(f"Resultado con check_password_hash (no-scrypt): {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error general en verificación: {e}")
        return False

def test_login():
    try:
        # Conectar a MongoDB
        mongodb_uri = os.getenv('MONGO_URI')
        if not mongodb_uri:
            logger.error("MONGO_URI no encontrada en variables de entorno")
            return False
            
        client = MongoClient(mongodb_uri, tlsCAFile=certifi.where())
        db = client.get_database('app_catalogojoyero_nueva')
        users_collection = db['users']
        
        logger.info("Conectado a MongoDB")
        
        # Buscar usuario edefrutos
        usuario = users_collection.find_one({'username': 'edefrutos'})
        if not usuario:
            logger.error("Usuario 'edefrutos' no encontrado")
            return False
            
        logger.info(f"Usuario encontrado: {usuario['email']}")
        logger.info(f"Rol: {usuario.get('role')}")
        
        # Probar diferentes contraseñas
        passwords_to_test = ['123456', 'admin123', 'password', 'edefrutos']
        
        for password in passwords_to_test:
            logger.info(f"\n=== Probando contraseña: {password} ===")
            result = verify_password_test(password, usuario['password'])
            logger.info(f"Resultado: {'✅ ÉXITO' if result else '❌ FALLO'}")
            
            if result:
                logger.info(f"🎉 Contraseña correcta encontrada: {password}")
                return True
        
        logger.error("❌ Ninguna contraseña funcionó")
        return False
        
    except Exception as e:
        logger.error(f"Error en test_login: {e}")
        return False

if __name__ == '__main__':
    logger.info("=== PRUEBA DE LOGIN REAL ===")
    success = test_login()
    if success:
        logger.info("✅ Test de login exitoso")
    else:
        logger.error("❌ Test de login falló")
