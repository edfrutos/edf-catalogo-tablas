# Implementación del Sistema de Autenticación

## 1. Tecnologías y Dependencias

### 1.1 Principales Tecnologías
- **Flask**: Framework web para Python
- **MongoDB**: Base de datos NoSQL
- **Bcrypt**: Biblioteca principal para hash de contraseñas
- **Werkzeug**: Soporte legacy para contraseñas antiguas
- **Flask-Mail**: Para envío de correos electrónicos

### 1.2 Dependencias Python
```python
from flask import Flask, session, request, flash, redirect, url_for
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import re
```

## 2. Estructura de la Base de Datos

### 2.1 Colección 'users'
```javascript
{
    "_id": ObjectId,
    "nombre": String,
    "email": String,
    "password": Binary,  // Hash bcrypt almacenado como bytes
    "role": String,      // "admin" o "normal"
    "created_at": String // Formato: "YYYY-MM-DD HH:MM:SS"
}
```

### 2.2 Colección 'resets'
```javascript
{
    "_id": ObjectId,
    "token": String,
    "user_id": ObjectId,
    "email": String,
    "created_at": DateTime,
    "expires_at": DateTime,
    "used": Boolean
}
```

## 3. Funcionalidades Implementadas

### 3.1 Sistema de Autenticación Híbrido
- **Soporte Legacy**: Mantiene compatibilidad con contraseñas antiguas (Werkzeug)
- **Migración Automática**: Actualiza a bcrypt en el primer login exitoso
- **Verificación en Dos Pasos**:
  1. Intenta verificar con bcrypt
  2. Si falla, intenta con Werkzeug y migra si es exitoso

### 3.2 Registro de Usuarios
```python
def register():
    # 1. Validación de entrada
    password = request.form.get("password").strip()
    
    # 2. Generación de hash con bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # 3. Almacenamiento en la base de datos
    nuevo_usuario = {
        "password": hashed,  # Se almacena como bytes
        "role": "normal",
        # otros campos...
    }
```

### 3.3 Inicio de Sesión
```python
def login():
    # 1. Verificación con bcrypt
    try:
        verification_result = bcrypt.checkpw(
            password.encode('utf-8'), 
            stored_password
        )
    except ValueError:
        # 2. Verificación con Werkzeug si bcrypt falla
        verification_result = check_password_hash(
            stored_password.decode('utf-8'), 
            password
        )
        
        # 3. Migración automática a bcrypt
        if verification_result:
            new_hash = bcrypt.hashpw(
                password.encode('utf-8'), 
                bcrypt.gensalt()
            )
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": new_hash}}
            )
```

### 3.4 Recuperación de Contraseña
- Generación de token seguro con `secrets.token_urlsafe()`
- Expiración automática después de 30 minutos
- Validación de requisitos de contraseña
- Almacenamiento del nuevo hash en formato bcrypt

## 4. Seguridad

### 4.1 Hash de Contraseñas
- **Método Principal**: bcrypt con salt automático
- **Formato de Almacenamiento**: Bytes en MongoDB
- **Migración Transparente**: De Werkzeug a bcrypt

### 4.2 Validación de Contraseñas
```python
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True
```

### 4.3 Medidas de Seguridad
- Sanitización de entradas
- Normalización de emails
- Tokens de un solo uso
- Expiración de sesiones
- Logging seguro (sin datos sensibles)

## 5. Sistema de Logging

### 5.1 Niveles de Log
- **INFO**: Operaciones normales
- **WARNING**: Intentos fallidos
- **ERROR**: Errores de sistema

### 5.2 Información Registrada
```python
app.logger.info(f'[LOGIN] Password type: {type(stored_password)}')
app.logger.info(f'[LOGIN] Verification method: {method}')
app.logger.info(f'[LOGIN] Migration status: {status}')
```

## 6. Mejores Prácticas

### 6.1 Almacenamiento
- Nunca almacenar contraseñas en texto plano
- Usar tipos de datos apropiados (bytes para hashes)
- Mantener índices para búsqueda eficiente

### 6.2 Migración
- Migración transparente para el usuario
- Mantener compatibilidad con sistemas legacy
- Actualización progresiva de la base de datos

### 6.3 Manejo de Errores
- Mensajes de error genéricos al usuario
- Logging detallado para debugging
- Captura de excepciones específicas

## 7. Mantenimiento

### 7.1 Monitoreo
- Revisar logs de errores
- Monitorear intentos fallidos
- Verificar tiempos de respuesta

### 7.2 Actualizaciones
- Mantener dependencias actualizadas
- Revisar nuevas vulnerabilidades
- Actualizar métodos de hash según necesidad
