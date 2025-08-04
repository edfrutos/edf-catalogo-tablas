#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Simular el formato de fecha que devuelve Google Drive
def test_date_formats():
    """Prueba diferentes formatos de fecha para entender el problema"""
    print("=== PRUEBA DE FORMATOS DE FECHA ===\n")
    
    # Formato típico que devuelve Google Drive (ejemplo)
    google_drive_date = "2025-08-04T18:33:45.123Z"  # UTC
    print(f"Fecha de Google Drive (UTC): {google_drive_date}")
    
    # Probar parsing con diferentes métodos
    try:
        # Método 1: Parse directo
        dt1 = datetime.fromisoformat(google_drive_date.replace('Z', '+00:00'))
        print(f"Método 1 (fromisoformat): {dt1}")
        print(f"  Local: {dt1.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Método 2: Parse con strptime
        dt2 = datetime.strptime(google_drive_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        print(f"Método 2 (strptime): {dt2}")
        print(f"  Local: {dt2.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Método 3: Parse sin microsegundos
        dt3 = datetime.strptime(google_drive_date.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        print(f"Método 3 (sin microsegundos): {dt3}")
        print(f"  Local: {dt3.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error parsing: {e}")
    
    # Simular el nombre del archivo
    filename = "backup_20250804_200054.json.gz"
    print(f"\nNombre del archivo: {filename}")
    
    # Extraer fecha del nombre del archivo
    if "backup_" in filename and ".json.gz" in filename:
        date_part = filename.replace("backup_", "").replace(".json.gz", "")
        try:
            file_date = datetime.strptime(date_part, "%Y%m%d_%H%M%S")
            print(f"Fecha del nombre del archivo: {file_date}")
            print(f"  Formato: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error parsing filename date: {e}")
    
    # Comparar fechas
    print(f"\n=== COMPARACIÓN ===")
    print(f"Nombre archivo indica: 2025-08-04 20:00:54")
    print(f"Google Drive muestra:   2025-08-04 18:33:45")
    print(f"Diferencia: ~1 hora 27 minutos")
    print(f"\nPosibles causas:")
    print(f"1. Diferencia de zona horaria (UTC vs local)")
    print(f"2. El archivo se subió a una hora diferente")
    print(f"3. Problema en el parsing de la fecha")

if __name__ == "__main__":
    test_date_formats() 