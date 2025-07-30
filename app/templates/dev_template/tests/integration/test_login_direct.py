#!/usr/bin/env python
"""
Script para probar el login directamente, sin pasar por el navegador.
Este script simula un login y verifica si las credenciales son válidas.
"""

import sys
import traceback
from app.models import get_users_collection, find_user_by_email_or_name
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import base64
import hashlib
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_login')

def verify_password_direct(password, stored_password, password_type=None):
    """Verifica una contraseña contra su hash almacenado."""
    try:
        # Convertir a string si es bytes
        if isinstance(stored_password, bytes):
            stored_password = stored_password.decode('utf-8')
            
        # Determinar el tipo de hash si no se proporciona
        if password_type is None:
            if stored_password.startswith('scrypt:'):
                password_type = 'scrypt'
            elif stored_password.startswith('$2b$'):
                password_type = 'werkzeug'
            else:
                password_type = 'unknown'
        
        logger.info(f"Tipo de contraseña: {password_type}")
        logger.info(f"Hash almacenado: {stored_password[:20]}...")

        if password_type == 'scrypt':
            # Extraer parámetros del hash scrypt
            parts = stored_password.split('$')
            logger.info(f"Partes del hash: {len(parts)}")
            if len(parts) != 3:
                logger.error(f"Formato scrypt inválido: {stored_password}")
                return False
                
            # El formato es: scrypt:N:r:p$salt$hash
            params = parts[0].split(':')  # [scrypt, N, r, p]
            logger.info(f"Parámetros: {params}")
            if len(params) != 4:
                logger.error(f"Parámetros scrypt inválidos: {parts[0]}")
                return False
                
            n = int(params[1])  # 32768
            r = int(params[2])  # 8
            p = int(params[3])  # 1
            
            # Decodificar salt de base64
            try:
                salt = base64.b64decode(parts[1] + '==')
                logger.info(f"Salt decodificado: {len(salt)} bytes")
            except Exception as e:
                logger.error(f"Error decodificando salt: {str(e)}")
                return False
                
            stored_hash = parts[2]
            logger.info(f"Hash almacenado: {stored_hash[:20]}...")
            
            try:
                # Verificar contraseña usando scrypt
                password_hash = base64.b64encode(hashlib.scrypt(password.encode('utf-8'), salt=salt, n=n, r=r, p=p, dklen=64)).decode('utf-8')
                # Eliminar padding si existe
                if password_hash.endswith('=='):
                    password_hash = password_hash[:-2]
                elif password_hash.endswith('='):
                    password_hash = password_hash[:-1]
                    
                logger.info(f"Hash calculado: {password_hash[:20]}...")
                logger.info(f"¿Coinciden los hashes?: {password_hash == stored_hash}")
                
                return password_hash == stored_hash
            except Exception as e:
                logger.error(f"Error verificando contraseña scrypt: {str(e)}")
                return False
        
        elif password_type == 'werkzeug':
            result = check_password_hash(stored_password, password)
            logger.info(f"Verificación werkzeug: {result}")
            return result
        
        else:
            logger.warning(f"Tipo de contraseña desconocido: {password_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error general en verificación de contraseña: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_login(email, password):
    """Prueba el login para un usuario directamente."""
    try:
        print(f"\n=== PROBANDO LOGIN PARA: {email} ===")
        
        # 1. Buscar usuario
        usuario = find_user_by_email_or_name(email)
        if not usuario:
            print(f"❌ Usuario no encontrado: {email}")
            return False
            
        print(f"✅ Usuario encontrado: {email}")
        print(f"   - ID: {usuario['_id']}")
        print(f"   - Rol: {usuario.get('role', 'user')}")
        print(f"   - Tipo de contraseña: {usuario.get('password_type', 'desconocido')}")
        
        # 2. Verificar si está bloqueado
        if usuario.get('locked_until'):
            print(f"❌ La cuenta está bloqueada hasta: {usuario['locked_until']}")
            
            # Desbloquear la cuenta
            get_users_collection().update_one(
                {'_id': usuario['_id']},
                {'$set': {'locked_until': None, 'failed_attempts': 0}}
            )
            print("✅ Cuenta desbloqueada")
        
        # 3. Verificar contraseña
        is_valid = verify_password_direct(password, usuario['password'], usuario.get('password_type'))
        
        if is_valid:
            print(f"✅ Contraseña válida para {email}")
        else:
            print(f"❌ Contraseña inválida para {email}")
            
            # Regenerar contraseña con werkzeug
            print("\n=== REGENERANDO CONTRASEÑA ===")
            new_hash = generate_password_hash(password, method='sha256')
            
            get_users_collection().update_one(
                {'_id': usuario['_id']},
                {'$set': {
                    'password': new_hash,
                    'password_type': 'werkzeug',
                    'password_updated_at': datetime.utcnow().isoformat()
                }}
            )
            
            print(f"✅ Contraseña regenerada usando werkzeug (sha256)")
            print(f"   - Nuevo hash: {new_hash[:25]}...")
            
            # Verificar de nuevo
            usuario = find_user_by_email_or_name(email)
            is_valid = verify_password_direct(password, usuario['password'], usuario.get('password_type'))
            
            if is_valid:
                print(f"✅ Verificación exitosa con la nueva contraseña")
            else:
                print(f"❌ La verificación falló incluso con la nueva contraseña")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error probando login: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== SCRIPT DE PRUEBA DE LOGIN DIRECTO ===")
    
    # Probar admin@example.com
    test_login('admin@example.com', 'admin123')
    
    # Probar edfrutos@gmail.com
    test_login('edfrutos@gmail.com', 'admin123')
    
    print("=== PRUEBAS COMPLETADAS ===")
