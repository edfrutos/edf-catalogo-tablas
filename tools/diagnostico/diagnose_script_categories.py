#!/usr/bin/env python3
"""
Script para diagnosticar las categorías de scripts
"""

import os
import sys


def check_script_categories():
    """Verifica qué scripts se encuentran en cada categoría"""
    print("🔍 DIAGNÓSTICO DE CATEGORÍAS DE SCRIPTS")
    print("=" * 60)

    # Definir el directorio raíz
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Categorías de producción (como están definidas en scripts_routes.py)
    categorias_produccion = {
        "Database Utils": [
            "tools/production/db_utils",
            "scripts/production/maintenance",
        ],
        "System Maintenance": [
            "scripts/production/maintenance",
            "tools/production/maintenance",
            "tools/production/system",
        ],
        "User Management": [
            "tools/production/admin_utils",
            "tools/production/user_utils",
        ],
        "File Management": [
            "tools/production/utils",
            "tools/production/catalog_utils",
        ],
        "Monitoring": ["tools/production/monitoring", "tools/production/diagnostico"],
        "Testing": [
            "tests/production/unit",
            "tests/production/integration",
            "tests/production/functional",
            "tests/production/performance",
            "tests/production/security",
        ],
        "Diagnostic Tools": [
            "tools/production/diagnostico",
        ],
        "Migration Tools": [
            "tools/production/aws_utils",
        ],
        "Configuration Tools": [
            "tools/production/configuration",
        ],
        "Development Tools": ["tools/production/app", "tools/production/src"],
        "Infrastructure": [
            "tools/production/aws_utils",
            "tools/production/session_utils",
        ],
        "Root Tools": ["tools/production/utils"],
    }

    # Categorías locales
    categorias_local = {
        "Database Utils": ["tools/local/db_utils", "scripts/local/maintenance"],
        "System Maintenance": [
            "scripts/local/maintenance",
            "tools/local/maintenance",
            "tools/local/system",
        ],
        "User Management": ["tools/local/admin_utils", "tools/local/user_utils"],
        "File Management": [
            "tools/local/utils",
            "tools/local/catalog_utils",
        ],
        "Monitoring": ["tools/local/monitoring", "tools/local/diagnostico"],
        "Testing": [
            "tests/local/unit",
            "tests/local/integration",
            "tests/local/functional",
            "tests/local/performance",
            "tests/local/security",
            "tools/testing",
        ],
        "Diagnostic Tools": [
            "tools/diagnostic",
            "tools/local/diagnostico",
        ],
        "Migration Tools": [
            "tools/migration",
            "tools/local/aws_utils",
        ],
        "Configuration Tools": [
            "tools/configuration",
        ],
        "Development Tools": ["tools/local/app", "tools/local/src"],
        "Infrastructure": ["tools/local/aws_utils", "tools/local/session_utils"],
        "Root Tools": ["tools/local/utils"],
    }

    def scan_category(categoria, directorios, entorno):
        """Escanea una categoría específica"""
        print(f"\n📁 {entorno} - {categoria}")
        print("-" * 40)

        scripts_encontrados = []

        for directorio in directorios:
            dir_path = os.path.join(ROOT_DIR, directorio)
            print(f"  🔍 Buscando en: {directorio}")

            if not os.path.exists(dir_path):
                print(f"    ❌ Directorio no existe: {dir_path}")
                continue

            if not os.path.isdir(dir_path):
                print(f"    ❌ No es un directorio: {dir_path}")
                continue

            try:
                archivos = os.listdir(dir_path)
                scripts_en_dir = []

                for fname in archivos:
                    fpath = os.path.join(dir_path, fname)
                    if os.path.isfile(fpath) and (
                        fname.endswith(".py") or fname.endswith(".sh")
                    ):
                        scripts_en_dir.append(fname)
                        scripts_encontrados.append(f"{directorio}/{fname}")

                if scripts_en_dir:
                    print(f"    ✅ Encontrados: {len(scripts_en_dir)} scripts")
                    for script in scripts_en_dir:
                        print(f"      - {script}")
                else:
                    print("    ⚠️  No se encontraron scripts")

            except Exception as e:
                print(f"    ❌ Error accediendo al directorio: {e}")

        if not scripts_encontrados:
            print("  ⚠️  No se encontraron scripts en esta categoría")
        else:
            print(f"  📊 Total: {len(scripts_encontrados)} scripts")

        return scripts_encontrados

    # Escanear categorías de producción
    print("\n🏭 CATEGORÍAS DE PRODUCCIÓN")
    print("=" * 60)

    total_produccion = 0
    for categoria, directorios in categorias_produccion.items():
        scripts = scan_category(categoria, directorios, "PRODUCCIÓN")
        total_produccion += len(scripts)

    # Escanear categorías locales
    print("\n💻 CATEGORÍAS LOCALES")
    print("=" * 60)

    total_local = 0
    for categoria, directorios in categorias_local.items():
        scripts = scan_category(categoria, directorios, "LOCAL")
        total_local += len(scripts)

    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✅ Scripts en Producción: {total_produccion}")
    print(f"✅ Scripts en Local: {total_local}")
    print(f"✅ Total: {total_produccion + total_local}")

    # Verificar scripts que podrían estar fuera de las categorías
    print("\n🔍 SCRIPTS FUERA DE CATEGORÍAS")
    print("=" * 60)

    def find_orphan_scripts(base_dir):
        """Encuentra scripts que no están en las categorías definidas"""
        orphan_scripts = []

        for root, dirs, files in os.walk(os.path.join(ROOT_DIR, base_dir)):
            for file in files:
                if file.endswith((".py", ".sh")):
                    rel_path = os.path.relpath(os.path.join(root, file), ROOT_DIR)
                    orphan_scripts.append(rel_path)

        return orphan_scripts

    # Buscar scripts huérfanos
    orphan_production = find_orphan_scripts("scripts/production")
    orphan_local = find_orphan_scripts("scripts/local")
    orphan_tools = find_orphan_scripts("tools")

    print(f"Scripts en scripts/production: {len(orphan_production)}")
    for script in orphan_production[:10]:  # Mostrar solo los primeros 10
        print(f"  - {script}")

    print(f"\nScripts en scripts/local: {len(orphan_local)}")
    for script in orphan_local[:10]:
        print(f"  - {script}")

    print(f"\nScripts en tools: {len(orphan_tools)}")
    for script in orphan_tools[:10]:
        print(f"  - {script}")

    return total_produccion + total_local


def test_script_execution():
    """Prueba la ejecución de algunos scripts"""
    print("\n🧪 PRUEBA DE EJECUCIÓN DE SCRIPTS")
    print("=" * 60)

    test_scripts = [
        "scripts/production/maintenance/supervise_gunicorn.sh",
        "scripts/local/maintenance/clean_old_logs.py",
        "tools/local/db_utils/conexion_MongoDB.py",
    ]

    for script_path in test_scripts:
        print(f"\n🔧 Probando: {script_path}")

        if not os.path.exists(script_path):
            print("  ❌ Script no existe")
            continue

        try:
            import json
            import subprocess

            # Ejecutar con script_runner
            result = subprocess.run(
                [sys.executable, "tools/script_runner.py", script_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                try:
                    json_output = json.loads(result.stdout)
                    print("  ✅ Ejecutado exitosamente")
                    print(f"     Exit code: {json_output.get('exit_code', 'N/A')}")
                    if json_output.get("error"):
                        print(f"     Error: {json_output['error']}")
                except json.JSONDecodeError:
                    print("  ⚠️  Ejecutado pero no devolvió JSON válido")
            else:
                print("  ❌ Error en ejecución")
                print(f"     Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("  ⚠️  Timeout (script de larga duración)")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def main():
    """Función principal"""
    total_scripts = check_script_categories()
    test_script_execution()

    print("\n🎯 DIAGNÓSTICO COMPLETADO")
    print(f"Total de scripts encontrados: {total_scripts}")

    return total_scripts > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
