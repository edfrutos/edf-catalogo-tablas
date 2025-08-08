#!/usr/bin/env python3
# Script para diagnosticar problemas con las URLs de los scripts
# Creado: 17/05/2025

import os
import sys
import glob


def print_header(message):
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)


def main():
    # Definir directorios importantes
    project_root = os.getcwd()  # Directorio actual para desarrollo local
    scripts_dir = os.path.join(project_root, "scripts")
    tools_dir = os.path.join(project_root, "tools")

    print_header("DIAGNÓSTICO DE SCRIPTS")
    print(f"Directorio raíz del proyecto: {project_root}")
    print(f"Directorio de scripts: {scripts_dir}")
    print(f"Directorio de herramientas: {tools_dir}")

    # Verificar si los directorios existen
    print_header("VERIFICACIÓN DE DIRECTORIOS")
    for directory in [project_root, scripts_dir, tools_dir]:
        print(f"{directory}: {'Existe' if os.path.exists(directory) else 'No existe'}")

    # Listar subdirectorios en scripts_dir
    print_header("SUBDIRECTORIOS EN SCRIPTS")
    if os.path.exists(scripts_dir):
        subdirs = [
            d
            for d in os.listdir(scripts_dir)
            if os.path.isdir(os.path.join(scripts_dir, d))
        ]
        for subdir in subdirs:
            subdir_path = os.path.join(scripts_dir, subdir)
            script_count = len(glob.glob(os.path.join(subdir_path, "*.sh"))) + len(
                glob.glob(os.path.join(subdir_path, "*.py"))
            )
            print(f"{subdir}: {script_count} scripts")
    else:
        print("El directorio de scripts no existe")

    # Verificar scripts en el directorio de mantenimiento
    maintenance_dir = os.path.join(scripts_dir, "maintenance")
    print_header("SCRIPTS DE MANTENIMIENTO")
    if os.path.exists(maintenance_dir):
        scripts = glob.glob(os.path.join(maintenance_dir, "*.sh")) + glob.glob(
            os.path.join(maintenance_dir, "*.py")
        )
        for script in scripts:
            print(f"Script: {os.path.basename(script)}")
            print(f"  Ruta completa: {script}")
            print(f"  Existe: {'Sí' if os.path.exists(script) else 'No'}")
            print(
                f"  Permisos de ejecución: {'Sí' if os.access(script, os.X_OK) else 'No'}"
            )
            print(f"  Tamaño: {os.path.getsize(script)} bytes")
            print()
    else:
        print("El directorio de mantenimiento no existe")

    # Verificar scripts en tools/maintenance
    tools_maintenance_dir = os.path.join(tools_dir, "maintenance")
    print_header("SCRIPTS EN TOOLS/MAINTENANCE")
    if os.path.exists(tools_maintenance_dir):
        scripts = glob.glob(os.path.join(tools_maintenance_dir, "*.sh")) + glob.glob(
            os.path.join(tools_maintenance_dir, "*.py")
        )
        for script in scripts:
            print(f"Script: {os.path.basename(script)}")
            print(f"  Ruta completa: {script}")
            print(f"  Existe: {'Sí' if os.path.exists(script) else 'No'}")
            print(
                f"  Permisos de ejecución: {'Sí' if os.access(script, os.X_OK) else 'No'}"
            )
            print(f"  Tamaño: {os.path.getsize(script)} bytes")
            print()
    else:
        print("El directorio tools/maintenance no existe")

    # Verificar rutas absolutas vs. relativas
    print_header("PRUEBA DE RUTAS")
    test_path = "/scripts/maintenance/monitor_socket.sh"
    print(f"Ruta de prueba: {test_path}")
    print(f"  Existe: {'Sí' if os.path.exists(test_path) else 'No'}")

    # Prueba de rutas absolutas con os.path.abspath
    abs_test_path = os.path.abspath(test_path)
    print(f"Ruta absoluta: {abs_test_path}")
    print(f"  Existe: {'Sí' if os.path.exists(abs_test_path) else 'No'}")
    print(f"  ¿Son iguales?: {'Sí' if test_path == abs_test_path else 'No'}")

    # Prueba de rutas relativas
    rel_test_path = os.path.relpath(test_path, project_root)
    print(f"Ruta relativa: {rel_test_path}")
    joined_path = os.path.join(project_root, rel_test_path)
    print(f"  Ruta unida: {joined_path}")
    print(f"  Existe: {'Sí' if os.path.exists(joined_path) else 'No'}")
    print(f"  ¿Son iguales?: {'Sí' if test_path == joined_path else 'No'}")

    print_header("RECOMENDACIONES")
    print("1. Asegúrese de que todos los scripts tengan permisos de ejecución")
    print("2. Utilice rutas absolutas en lugar de relativas")
    print("3. Verifique que los scripts existan en las ubicaciones esperadas")
    print(
        "4. Ejecute el script copy_scripts.sh para copiar los scripts al directorio tools"
    )


if __name__ == "__main__":
    main()
