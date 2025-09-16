#!/usr/bin/env python3
"""
Script para iniciar múltiples instancias del servidor Flask
Permite tener sesiones separadas en diferentes puertos
"""

import threading
import time
from wsgi import app

def run_server(port, name):
    """Ejecuta el servidor en un puerto específico"""
    print(f"🚀 Iniciando servidor {name} en puerto {port}...")
    app.run(debug=False, port=port, host="0.0.0.0", use_reloader=False)

if __name__ == "__main__":
    print("🔧 Configuración para múltiples sesiones:")
    print("   - Puerto 5001: Sesión principal")
    print("   - Puerto 5002: Sesión secundaria")
    print("   - Puerto 5003: Sesión de prueba")
    print()
    
    # Crear hilos para cada servidor
    server1 = threading.Thread(target=run_server, args=(5001, "Principal"))
    server2 = threading.Thread(target=run_server, args=(5002, "Secundario"))
    server3 = threading.Thread(target=run_server, args=(5003, "Prueba"))
    
    # Iniciar servidores
    server1.start()
    time.sleep(2)  # Esperar un poco entre inicios
    server2.start()
    time.sleep(2)
    server3.start()
    
    print("✅ Todos los servidores iniciados")
    print("📋 URLs disponibles:")
    print("   - http://localhost:5001 (Sesión 1)")
    print("   - http://localhost:5002 (Sesión 2)")  
    print("   - http://localhost:5003 (Sesión 3)")
    print()
    print("💡 Uso recomendado:")
    print("   - Puerto 5001: Administrador")
    print("   - Puerto 5002: Usuario normal")
    print("   - Puerto 5003: Usuario de prueba")
    
    try:
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Cerrando servidores...")
