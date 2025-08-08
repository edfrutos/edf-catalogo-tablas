#!/usr/bin/env python3
from datetime import datetime, timedelta
import time

def convert_utc_to_local(utc_date_str):
    """Convierte fecha UTC a zona horaria local"""
    if not utc_date_str:
        return ''
    try:
        # Parsear fecha UTC (formato: 2025-08-04T18:33:45.123Z)
        if utc_date_str.endswith('Z'):
            # Remover 'Z' y agregar '+00:00' para indicar UTC
            utc_date_str = utc_date_str[:-1] + '+00:00'
        
        # Parsear la fecha UTC
        dt_utc = datetime.fromisoformat(utc_date_str)
        
        # Convertir a zona horaria local (CEST = UTC+2)
        # Obtener offset local
        local_offset = time.timezone if time.daylight == 0 else time.altzone
        local_offset_hours = -local_offset / 3600  # Convertir segundos a horas
        
        # Aplicar offset manualmente
        dt_local = dt_utc + timedelta(hours=local_offset_hours)
        
        # Formatear como string
        return dt_local.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error convirtiendo fecha {utc_date_str}: {e}")
        return utc_date_str

def test_date_conversion():
    """Prueba la conversión de fechas"""
    print("=== PRUEBA DE CONVERSIÓN DE FECHAS ===\n")
    
    # Fecha de ejemplo que podría venir de Google Drive
    test_dates = [
        "2025-08-04T18:33:45.123Z",
        "2025-08-04T18:00:54.000Z",
        "2025-08-04T20:00:54.000Z"
    ]
    
    print(f"Zona horaria del sistema: {'CEST' if time.daylight else 'CET'}")
    print(f"Offset: {time.altzone if time.daylight else time.timezone} segundos")
    print(f"Offset en horas: {-time.altzone/3600 if time.daylight else -time.timezone/3600}\n")
    
    for utc_date in test_dates:
        local_date = convert_utc_to_local(utc_date)
        print(f"UTC: {utc_date}")
        print(f"Local: {local_date}")
        print()
    
    # Probar con el caso específico del problema
    print("=== CASO ESPECÍFICO ===")
    filename = "backup_20250804_200054.json.gz"
    print(f"Nombre del archivo: {filename}")
    
    # Extraer fecha del nombre del archivo
    if "backup_" in filename and ".json.gz" in filename:
        date_part = filename.replace("backup_", "").replace(".json.gz", "")
        try:
            file_date = datetime.strptime(date_part, "%Y%m%d_%H%M%S")
            print(f"Fecha del nombre del archivo: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error parsing filename date: {e}")
    
    # Simular fecha de Google Drive
    google_drive_utc = "2025-08-04T18:33:45.123Z"
    google_drive_local = convert_utc_to_local(google_drive_utc)
    print(f"Google Drive UTC: {google_drive_utc}")
    print(f"Google Drive Local: {google_drive_local}")
    
    # Comparar
    print(f"\nComparación:")
    print(f"Nombre archivo: 2025-08-04 20:00:54")
    print(f"Google Drive:    {google_drive_local}")
    
    # Calcular diferencia
    try:
        file_dt = datetime.strptime("2025-08-04 20:00:54", "%Y-%m-%d %H:%M:%S")
        drive_dt = datetime.strptime(google_drive_local, "%Y-%m-%d %H:%M:%S")
        diff = abs((file_dt - drive_dt).total_seconds() / 60)  # en minutos
        print(f"Diferencia: {diff:.0f} minutos")
    except Exception as e:
        print(f"Error calculando diferencia: {e}")

if __name__ == "__main__":
    test_date_conversion() 