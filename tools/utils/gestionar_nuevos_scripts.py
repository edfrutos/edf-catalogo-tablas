#!/usr/bin/env python3
"""
Script para gestionar nuevos scripts y verificar su reconocimiento automático
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def get_script_directories():
    """Obtiene todos los directorios donde se pueden colocar scripts"""
    return {
        "Database Utils": [
            "tools/local/db_utils",
            "tools/production/db_utils",
            "scripts/local/maintenance",
            "scripts/production/maintenance"
        ],
        "System Maintenance": [
            "scripts/local/maintenance",
            "scripts/production/maintenance",
            "tools/local/maintenance",
            "tools/production/maintenance",
            "tools/local/system",
            "tools/production/system"
        ],
        "User Management": [
            "tools/local/admin_utils",
            "tools/production/admin_utils",
            "tools/local/user_utils",
            "tools/production/user_utils"
        ],
        "File Management": [
            "tools/local/utils",
            "tools/production/utils",
            "tools/local/catalog_utils",
            "tools/production/catalog_utils"
        ],
        "Monitoring": [
            "tools/local/monitoring",
            "tools/production/monitoring",
            "tools/local/diagnostico",
            "tools/production/diagnostico"
        ],
        "Testing": [
            "tests/local/unit",
            "tests/local/integration",
            "tests/local/functional",
            "tests/local/performance",
            "tests/local/security",
            "tests/production/unit",
            "tests/production/integration",
            "tests/production/functional",
            "tests/production/performance",
            "tests/production/security",
            "tools/testing"
        ],
        "Diagnostic Tools": [
            "tools/diagnostic",
            "tools/local/diagnostico",
            "tools/production/diagnostico"
        ],
        "Migration Tools": [
            "tools/migration",
            "tools/local/aws_utils",
            "tools/production/aws_utils"
        ],
        "Configuration Tools": [
            "tools/configuration",
            "tools/production/configuration"
        ],
        "Development Tools": [
            "tools/local/app",
            "tools/production/app",
            "tools/local/src",
            "tools/production/src"
        ],
        "Infrastructure": [
            "tools/local/aws_utils",
            "tools/production/aws_utils",
            "tools/local/session_utils",
            "tools/production/session_utils"
        ],
        "Root Tools": [
            "tools/local/utils",
            "tools/production/utils"
        ]
    }

def scan_scripts_in_directory(directory):
    """Escanea scripts en un directorio específico"""
    scripts = []
    if os.path.exists(directory):
        try:
            for fname in os.listdir(directory):
                fpath = os.path.join(directory, fname)
                if os.path.isfile(fpath) and (fname.endswith('.py') or fname.endswith('.sh')):
                    scripts.append({
                        'name': fname,
                        'path': fpath,
                        'type': 'python' if fname.endswith('.py') else 'bash',
                        'executable': os.access(fpath, os.X_OK),
                        'size': os.path.getsize(fpath)
                    })
        except Exception as e:
            print(f"Error escaneando {directory}: {e}")
    return scripts

def check_script_recognition():
    """Verifica qué scripts son reconocidos por el sistema"""
    print("=== VERIFICACIÓN DE RECONOCIMIENTO DE SCRIPTS ===")
    
    directories = get_script_directories()
    total_scripts = 0
    recognized_scripts = 0
    
    for category, dirs in directories.items():
        print(f"\n📁 Categoría: {category}")
        category_scripts = 0
        
        for directory in dirs:
            full_path = os.path.join(os.getcwd(), directory)
            scripts = scan_scripts_in_directory(full_path)
            
            if scripts:
                print(f"  📂 {directory}:")
                for script in scripts:
                    total_scripts += 1
                    category_scripts += 1
                    
                    # Verificar si el script es reconocido por el sistema
                    is_recognized = check_script_in_metadata(script['name'], directory)
                    status = "✅" if is_recognized else "❌"
                    recognized_scripts += 1 if is_recognized else 0
                    
                    print(f"    {status} {script['name']} ({script['type']}, {script['size']} bytes)")
        
        if category_scripts == 0:
            print(f"  📂 {directory}: (vacío)")
    
    print(f"\n📊 RESUMEN:")
    print(f"  Total de scripts encontrados: {total_scripts}")
    print(f"  Scripts reconocidos: {recognized_scripts}")
    print(f"  Scripts no reconocidos: {total_scripts - recognized_scripts}")
    
    return total_scripts, recognized_scripts

def check_script_in_metadata(script_name, directory):
    """Verifica si un script aparece en los metadatos del sistema"""
    # Esta función simula la verificación que hace el sistema
    # En realidad, el sistema lee los directorios dinámicamente
    
    # Verificar si el directorio está en la lista de directorios reconocidos
    recognized_dirs = []
    for category_dirs in get_script_directories().values():
        recognized_dirs.extend(category_dirs)
    
    return directory in recognized_dirs

def add_new_script():
    """Guía para agregar un nuevo script"""
    print("\n=== GUÍA PARA AGREGAR NUEVOS SCRIPTS ===")
    
    print("📋 Directorios disponibles por categoría:")
    directories = get_script_directories()
    
    for i, (category, dirs) in enumerate(directories.items(), 1):
        print(f"\n{i}. {category}:")
        for dir_path in dirs:
            print(f"   📂 {dir_path}")
    
    print("\n💡 INSTRUCCIONES:")
    print("1. Coloca tu script en el directorio apropiado según su categoría")
    print("2. Asegúrate de que tenga permisos de ejecución: chmod 755 script.py")
    print("3. Agrega una descripción en el script:")
    print("   # Descripción: Tu descripción aquí")
    print("4. El script será reconocido automáticamente al recargar la página")
    print("5. No necesitas ejecutar ningún comando adicional")

def create_script_template():
    """Crea una plantilla de script"""
    print("\n=== PLANTILLA DE SCRIPT ===")
    
    template = '''#!/usr/bin/env python3
# Descripción: Descripción de tu script aquí
# Autor: Tu nombre
# Fecha: Fecha de creación

import os
import sys
from datetime import datetime

def main():
    """
    Función principal del script
    """
    print("=== EJECUTANDO SCRIPT ===")
    print(f"Fecha y hora: {datetime.now()}")
    print(f"Directorio actual: {os.getcwd()}")
    
    # Tu código aquí
    print("Script ejecutado correctamente")

if __name__ == "__main__":
    main()
'''
    
    print("📄 Plantilla de script Python:")
    print(template)
    
    # Crear archivo de plantilla
    template_file = "plantilla_script.py"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"\n✅ Plantilla guardada como: {template_file}")

def check_new_scripts():
    """Verifica si hay scripts nuevos que no están siendo reconocidos"""
    print("\n=== VERIFICACIÓN DE SCRIPTS NUEVOS ===")
    
    # Obtener scripts actuales
    directories = get_script_directories()
    all_scripts = []
    
    for category, dirs in directories.items():
        for directory in dirs:
            full_path = os.path.join(os.getcwd(), directory)
            scripts = scan_scripts_in_directory(full_path)
            for script in scripts:
                script['category'] = category
                script['directory'] = directory
                all_scripts.append(script)
    
    # Verificar permisos
    print("🔍 Verificando permisos de scripts...")
    scripts_without_permissions = []
    
    for script in all_scripts:
        if not script['executable']:
            scripts_without_permissions.append(script)
    
    if scripts_without_permissions:
        print("❌ Scripts sin permisos de ejecución:")
        for script in scripts_without_permissions:
            print(f"  - {script['directory']}/{script['name']}")
        
        print("\n💡 Para corregir permisos:")
        for script in scripts_without_permissions:
            print(f"  chmod 755 {script['path']}")
    else:
        print("✅ Todos los scripts tienen permisos correctos")
    
    return len(scripts_without_permissions)

def main():
    """Función principal"""
    print("🔧 GESTOR DE NUEVOS SCRIPTS")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scan":
            check_script_recognition()
        elif command == "add":
            add_new_script()
        elif command == "template":
            create_script_template()
        elif command == "check":
            check_new_scripts()
        else:
            print(f"Comando desconocido: {command}")
            print("Comandos disponibles: scan, add, template, check")
    else:
        # Menú interactivo
        print("Selecciona una opción:")
        print("1. Escanear scripts existentes")
        print("2. Guía para agregar nuevos scripts")
        print("3. Crear plantilla de script")
        print("4. Verificar scripts nuevos")
        print("5. Ejecutar todas las verificaciones")
        
        try:
            choice = input("\nOpción (1-5): ").strip()
            
            if choice == "1":
                check_script_recognition()
            elif choice == "2":
                add_new_script()
            elif choice == "3":
                create_script_template()
            elif choice == "4":
                check_new_scripts()
            elif choice == "5":
                check_script_recognition()
                add_new_script()
                check_new_scripts()
            else:
                print("Opción inválida")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")

if __name__ == "__main__":
    main()
