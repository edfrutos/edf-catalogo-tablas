# Script: cache_system.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 cache_system.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

"""
Sistema de caché en memoria para reducir la dependencia en MongoDB.
Almacena temporalmente resultados de consultas frecuentes.
"""

import time
import logging
import threading
import json
import os
from functools import wraps

# Configuración de logging (solo consola para evitar errores de permisos)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [CACHE] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Cache en memoria principal con capacidad limitada
_memory_cache = {}
_cache_lock = threading.RLock()
_cache_file = None  # Desactivamos el archivo de respaldo para evitar problemas de permisos
_max_cache_size = 100  # Reducido a 100 para minimizar el uso de memoria

# Contadores de estadísticas
_cache_hit_count = 0
_cache_miss_count = 0

# No necesitamos crear el directorio /tmp ya que siempre existe

def set_cache(key, value, ttl=1800):  # TTL reducido a 30 minutos por defecto
    """
    Almacena un valor en la caché con un tiempo de vida específico.
    Implementa control de tamaño máximo para evitar fugas de memoria.
    
    Args:
        key: Clave única para identificar el valor
        value: Valor a almacenar (debe ser serializable)
        ttl: Tiempo de vida en segundos (por defecto 30 minutos para conservar memoria)
    """
    global _memory_cache, _max_cache_size
    
    # Convertir cualquier valor no serializable a string
    if hasattr(value, '__dict__'):
        value = str(value)
    
    expires_at = time.time() + ttl
    
    with _cache_lock:
        # Limpiar entradas antiguas si el caché excede el tamaño máximo
        if len(_memory_cache) >= _max_cache_size:
            # Eliminar las entradas más antiguas
            now = time.time()
            expired_keys = [k for k, v in _memory_cache.items() 
                           if v['expires_at'] < now]
            
            # Eliminar primero las entradas expiradas
            for k in expired_keys:
                del _memory_cache[k]
                
            # Si todavía excede el tamaño máximo, eliminar las más antiguas
            if len(_memory_cache) >= _max_cache_size:
                # Ordenar por tiempo de expiración y eliminar el 20% más antiguo
                sorted_items = sorted(_memory_cache.items(), 
                                     key=lambda x: x[1]['expires_at'])
                items_to_remove = int(len(sorted_items) * 0.2)  # Eliminar el 20%
                
                for i in range(items_to_remove):
                    if i < len(sorted_items):
                        del _memory_cache[sorted_items[i][0]]
        
        # Almacenar el nuevo valor
        _memory_cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    # Guardar caché en disco periódicamente
    if len(_memory_cache) % 10 == 0:  # Cada 10 entradas
        _save_cache_to_disk()
    
    logging.debug(f"Valor almacenado en caché: {key} (expira en {ttl} segundos)")
    return True

def get_cache(key):
    """
    Recupera un valor de la caché si existe y no ha expirado.
    
    Args:
        key: Clave del valor a recuperar
        
    Returns:
        El valor almacenado o None si no existe o ha expirado
    """
    global _memory_cache, _cache_hit_count, _cache_miss_count
    
    with _cache_lock:
        if key not in _memory_cache:
            _cache_miss_count += 1
            return None
        
        cache_item = _memory_cache[key]
        
        # Verificar si el valor ha expirado
        if time.time() > cache_item['expires_at']:
            del _memory_cache[key]
            _cache_miss_count += 1
            logging.debug(f"Valor expirado en caché: {key}")
            return None
        
        _cache_hit_count += 1
        logging.debug(f"Valor recuperado de caché: {key}")
        return cache_item['value']

def delete_cache(key):
    """Elimina un valor de la caché"""
    global _memory_cache
    
    with _cache_lock:
        if key in _memory_cache:
            del _memory_cache[key]
            logging.debug(f"Valor eliminado de caché: {key}")
            return True
    
    return False

def clear_cache():
    """Limpia toda la caché"""
    global _memory_cache
    
    with _cache_lock:
        _memory_cache.clear()
    
    logging.info("Caché limpiada completamente")
    return True

def _save_cache_to_disk():
    """Guarda una copia de la caché en disco para persistencia básica"""
    global _cache_file
    
    # Si _cache_file es None, no intentamos guardar en disco
    if _cache_file is None:
        logging.debug("Guardado en disco desactivado (_cache_file es None)")
        return
        
    try:
        serializable_cache = {}
        
        # Filtrar solo los valores que no han expirado y son serializables
        current_time = time.time()
        with _cache_lock:
            for key, item in _memory_cache.items():
                if item['expires_at'] > current_time:
                    try:
                        # Verificar si el valor es serializable
                        json.dumps(item['value'])
                        serializable_cache[key] = item
                    except (TypeError, OverflowError):
                        # Si no es serializable, lo omitimos
                        pass
        
        # Guardar en disco solo si _cache_file tiene un valor
        with open(_cache_file, 'w') as f:
            json.dump(serializable_cache, f)
        
        logging.debug(f"Caché guardada en disco: {len(serializable_cache)} elementos")
    except Exception as e:
        logging.error(f"Error al guardar caché en disco: {str(e)}")

def _load_cache_from_disk():
    """Carga la caché desde disco si existe"""
    global _memory_cache, _cache_file
    
    # Si _cache_file es None, no intentamos cargar desde disco
    if _cache_file is None:
        logging.debug("Carga desde disco desactivada (_cache_file es None)")
        return
    
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, 'r') as f:
                disk_cache = json.load(f)
            
            # Filtrar elementos expirados
            current_time = time.time()
            valid_items = {
                k: v for k, v in disk_cache.items() 
                if v['expires_at'] > current_time
            }
            
            with _cache_lock:
                _memory_cache.update(valid_items)
            
            logging.info(f"Caché cargada desde disco: {len(valid_items)} elementos válidos")
    except Exception as e:
        logging.error(f"Error al cargar caché desde disco: {str(e)}")

# Decorador para cachear funciones
def cached(ttl=3600, key_prefix=''):
    """
    Decorador para cachear el resultado de una función.
    
    Args:
        ttl: Tiempo de vida en segundos (por defecto 1 hora)
        key_prefix: Prefijo para la clave de caché
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar una clave única basada en la función y sus argumentos
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Intentar obtener el resultado de la caché
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Si no está en caché, ejecutar la función
            result = func(*args, **kwargs)
            
            # Almacenar el resultado en la caché
            set_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def get_cache_stats():
    """
    Devuelve estadísticas de la caché: hits, misses, hit_rate, tamaño actual.
    """
    global _memory_cache, _cache_hit_count, _cache_miss_count
    size = len(_memory_cache)
    hits = _cache_hit_count
    misses = _cache_miss_count
    total = hits + misses
    hit_rate = (hits / total) * 100 if total > 0 else 0.0
    return {
        'hit_count': hits,
        'miss_count': misses,
        'hit_rate': round(hit_rate, 2),
        'size': size
    }

# Cargar la caché desde disco al iniciar
_load_cache_from_disk()

# Iniciar un hilo para guardar la caché periódicamente
def _periodic_cache_save():
    while True:
        time.sleep(300)  # Cada 5 minutos
        _save_cache_to_disk()

save_thread = threading.Thread(target=_periodic_cache_save)
save_thread.daemon = True
save_thread.start()

# Hacer un guardado inicial
_save_cache_to_disk()
