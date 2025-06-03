#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymongo import MongoClient
from datetime import datetime, timedelta
import sys

def connect_to_db():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['edefrutos']
        return db
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        sys.exit(1)

def check_security_logs():
    db = connect_to_db()
    
    # Verificar logs de seguridad
    security_logs = db['security_logs']
    print("\n=== Logs de Seguridad (últimos 7 días) ===")
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs = security_logs.find({
        'timestamp': {'$gte': seven_days_ago}
    }).sort('timestamp', -1)
    
    log_count = 0
    for log in logs:
        log_count += 1
        print(f"\nEvento: {log.get('event_type', 'N/A')}")
        print(f"Usuario: {log.get('user_id', 'N/A')}")
        print(f"Fecha: {log.get('timestamp', 'N/A')}")
        print(f"IP: {log.get('ip_address', 'N/A')}")
        print(f"Detalles: {log.get('details', 'N/A')}")
    
    if log_count == 0:
        print("No se encontraron logs de seguridad en los últimos 7 días")
    
    # Verificar intentos de inicio de sesión
    login_attempts = db['login_attempts']
    print("\n=== Intentos de Inicio de Sesión ===")
    attempts = login_attempts.find().sort('timestamp', -1)
    
    attempt_count = 0
    for attempt in attempts:
        attempt_count += 1
        print(f"\nUsuario: {attempt.get('user_id', 'N/A')}")
        print(f"Fecha: {attempt.get('timestamp', 'N/A')}")
        print(f"Éxito: {attempt.get('success', False)}")
        print(f"IP: {attempt.get('ip_address', 'N/A')}")
    
    if attempt_count == 0:
        print("No se encontraron intentos de inicio de sesión")

if __name__ == '__main__':
    check_security_logs() 