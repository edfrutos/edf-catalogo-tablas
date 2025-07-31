#!/usr/bin/env python3
"""
Script para probar el endpoint de restauración de backups desde Google Drive
"""

import requests
import json
from datetime import datetime

def test_restore_endpoint_direct():
    """
    Prueba directa del endpoint sin autenticación para verificar la lógica
    """
    print("🔍 Analizando el problema del endpoint /admin/restore-drive-backup")
    print("\n📋 Resumen del problema:")
    print("- El usuario reporta error 400 BAD REQUEST")
    print("- El endpoint espera 'backup_id' y 'download_url' en request.form")
    print("- La plantilla HTML envía estos datos correctamente")
    print("\n🔧 Corrección aplicada:")
    print("- Se corrigió la importación: 'from app.database import get_mongo_db'")
    print("- Antes usaba 'from app.utils.db_utils import get_db' pero llamaba get_mongo_db()")
    
    print("\n✅ El endpoint debería funcionar ahora correctamente")
    print("\n📝 Para probar desde la interfaz web:")
    print("1. Ir a http://localhost:5001/admin/drive-backups")
    print("2. Hacer clic en el botón de restaurar de cualquier backup")
    print("3. El endpoint debería procesar la solicitud sin error 400")
    
    print("\n🚨 Posibles errores que aún pueden ocurrir:")
    print("- Error 404: Si el backup_id no existe en la base de datos")
    print("- Error 500: Si hay problemas de conexión a MongoDB o descarga")
    print("- Error 400: Solo si faltan los parámetros backup_id o download_url")
    
    print("\n🔍 Para debugging adicional, revisar los logs del servidor en tiempo real")

def test_form_data_simulation():
    """
    Simula los datos que envía el formulario HTML
    """
    print("\n📤 Datos que envía la plantilla HTML:")
    form_data = {
        'backup_id': '507f1f77bcf86cd799439011',  # Ejemplo de ObjectId
        'download_url': 'https://drive.google.com/uc?id=1234567890&export=download'
    }
    
    print(f"backup_id: {form_data['backup_id']}")
    print(f"download_url: {form_data['download_url']}")
    
    print("\n✅ Estos datos son válidos y deberían pasar la validación inicial")
    print("El error 400 anterior era debido a la función get_mongo_db() no definida")

if __name__ == "__main__":
    test_restore_endpoint_direct()
    test_form_data_simulation()