#!/usr/bin/env python3
# Configuración de sesión optimizada para Flask
# Actualizado para mayor rendimiento y seguridad
# Última actualización: 2025-05-20

import os
from datetime import timedelta

# Usar variables de entorno para información sensible
SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Configuración optimizada para cookie-based sessions (menos carga en servidor)
SESSION_TYPE = 'cookie'
SESSION_COOKIE_NAME = 'edefrutos2025_session'
SESSION_COOKIE_SECURE = True  # Cookies solo por HTTPS
SESSION_COOKIE_HTTPONLY = True  # No accesible por JavaScript
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF

# Reducción del tiempo de vida de la sesión para menor sobrecarga
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = 14400  # 4 horas (reducido de 24 horas)

# Configuraciones adicionales de rendimiento
SESSION_REFRESH_EACH_REQUEST = False  # No renovar en cada petición (menos I/O)
SESSION_USE_SIGNER = True  # Firmar cookies para mayor seguridad

# Configuración para desarrollo local - solo activa en entorno de desarrollo
if os.environ.get('FLASK_ENV') == 'development':
    SESSION_COOKIE_SECURE = False  # Permitir HTTP en desarrollo
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas en desarrollo
