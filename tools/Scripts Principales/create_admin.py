#!/usr/bin/env python3
import base64
import hashlib
from datetime import datetime

from app.models import get_users_collection


def create_admin_user():
    # Parámetros de scrypt
    n = 32768  # 2**15
    r = 8
    p = 1

    # Credenciales
    email = "admin@example.com"
    password = "admin123"

    # Generar salt y hash
    salt = base64.b64encode(b'adminsalt12345678').decode('utf-8').rstrip('=')  # Salt fijo para reproducibilidad
    password_hash = base64.b64encode(
        hashlib.scrypt(password.encode('utf-8'),
                       salt=base64.b64decode(salt + '=='),
                       n=n, r=r, p=p, dklen=64)
    ).decode('utf-8').rstrip('=')

    # Formato final del hash
    stored_password = f"scrypt:{n}:{r}:{p}${salt}${password_hash}"

    # Crear documento de usuario
    admin_user = {
        "email": email,
        "username": "administrator",
        "password": stored_password,
        "password_type": "scrypt",
        "role": "admin",
        "created_at": datetime.utcnow().isoformat(),
        "active": True
    }

    # Insertar o actualizar usuario
    result = get_users_collection().replace_one(
        {"email": email},
        admin_user,
        upsert=True
    )

    if result.upserted_id:
        print(f"Usuario admin creado con ID: {result.upserted_id}")
    else:
        print(f"Usuario admin actualizado. Documentos modificados: {result.modified_count}")

    print("\nCredenciales de acceso:")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == '__main__':
    create_admin_user()
