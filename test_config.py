# Script: test_config.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_config.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

import os

class TestConfig:
    MONGO_URI = "mongodb+srv://edfrutos:3Utitwr3piFt4LVf@cluster0.abpvipa.mongodb.net/app_catalogotablas_nueva?retryWrites=true&w=majority&appName=Cluster0"
    MONGODB_DB = "app_catalogotablas_nueva"
    MONGO_DB = "app_catalogotablas_nueva"
    
    MONGODB_SETTINGS = {
        'connect': False,
        'tlsAllowInvalidCertificates': True
    }
