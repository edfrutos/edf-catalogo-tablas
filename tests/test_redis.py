# Script: test_redis.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_redis.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from redis import Redis
import sys

try:
    redis_client = Redis(
        host='localhost',
        port=6379,
        db=0,
        socket_timeout=1
    )
    
    # Probar escribir y leer un valor
    redis_client.set('test_key', 'test_value')
    value = redis_client.get('test_key')
    print(f"Valor leído de Redis: {value}")
    
    # Limpiar el valor de prueba
    redis_client.delete('test_key')
    print("Conexión a Redis exitosa")
    sys.exit(0)
    
except Exception as e:
    print(f"Error al conectar con Redis: {str(e)}")
    sys.exit(1)
