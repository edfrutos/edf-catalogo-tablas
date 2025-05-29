# Script: test_password.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_password.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

import scrypt
import base64
from app.routes.auth_routes import verify_password
from app.models import get_users_collection
from bson.objectid import ObjectId

def test_password_verification():
    # Obtener usuario de prueba
    user = get_users_collection().find_one({"email": "admin@example.com"})
    if not user:
        print("Usuario no encontrado")
        return

    print("Datos del usuario:")
    print(f"Email: {user['email']}")
    print(f"Password type: {user.get('password_type', 'no especificado')}")
    print(f"Password hash: {user['password']}")
    
    # Probar verificación
    test_password = "admin123"
    result = verify_password(test_password, user['password'], user.get('password_type'))
    print(f"\nProbando contraseña '{test_password}':")
    print(f"Resultado: {'Válida' if result else 'Inválida'}")

    # Mostrar más detalles si es scrypt
    if user.get('password_type') == 'scrypt':
        stored_pass = user['password']
        parts = stored_pass.split('$')
        if len(parts) == 3:
            params = parts[0].split(':')
            print("\nDetalles del hash scrypt:")
            print(f"Parámetros: {params}")
            print(f"Salt (base64): {parts[1]}")
            print(f"Hash (base64): {parts[2]}")
            
            # Generar nuevo hash para comparar
            salt = base64.b64decode(parts[1] + '==')
            n = int(params[1])
            r = int(params[2])
            p = int(params[3])
            
            new_hash = base64.b64encode(scrypt.hash(test_password.encode('utf-8'), 
                                                   salt, N=n, r=r, p=p)).decode('utf-8')
            if new_hash.endswith('=='):
                new_hash = new_hash[:-2]
            elif new_hash.endswith('='):
                new_hash = new_hash[:-1]
                
            print(f"\nHash generado: {new_hash}")
            print(f"Hash almacenado: {parts[2]}")
            print(f"¿Coinciden?: {new_hash == parts[2]}")

if __name__ == '__main__':
    test_password_verification()
