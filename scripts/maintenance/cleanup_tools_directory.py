#!/usr/bin/env python3
# Script para revisar, depurar y organizar scripts en el directorio /tools
# Creado: 18/05/2025

import datetime
import json
import os
import shutil
import subprocess
import sys

# Configuración
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")


def print_header(message):
    print("\n" + "=" * 80)
    print(f"{message}".center(80))
    print("=" * 80)


def ensure_directory(directory):
    """Asegura que un directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"✅ Directorio creado: {directory}")
    return directory


def find_duplicate_scripts():
    """Encuentra scripts duplicados en el directorio /tools"""
    print("Buscando scripts duplicados...")

    # Diccionario para almacenar scripts por nombre
    scripts_by_name = {}

    # Recorrer todos los archivos en /tools y subdirectorios
    for root, _, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".sh"):
                # Ignorar enlaces simbólicos
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue

                # Añadir al diccionario
                if file in scripts_by_name:
                    scripts_by_name[file].append(file_path)
                else:
                    scripts_by_name[file] = [file_path]

    # Encontrar duplicados
    duplicates = {
        name: paths for name, paths in scripts_by_name.items() if len(paths) > 1
    }

    if duplicates:
        print(f"Se encontraron {len(duplicates)} scripts duplicados:")
        for name, paths in duplicates.items():
            print(f"  Script: {name}")
            for path in paths:
                print(f"    - {path}")
    else:
        print("No se encontraron scripts duplicados")

    return duplicates


def check_script_quality(script_path):
    """Verifica la calidad de un script"""
    issues = []

    # Verificar si es un archivo
    if not os.path.isfile(script_path) or os.path.islink(script_path):
        return []

    # Verificar extensión
    if not script_path.endswith(".py") and not script_path.endswith(".sh"):
        return []

    try:
        # Leer el contenido del script
        with open(script_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Verificar shebang
        first_line = content.split("\n")[0] if content else ""
        if not first_line.startswith("#!"):
            issues.append("Falta shebang (#!)")

        # Verificar comentarios
        if content.count("#") < 3 and script_path.endswith(".py"):
            issues.append("Pocos comentarios")

        # Verificar imports en scripts Python
        if script_path.endswith(".py"):
            if "import" not in content:
                issues.append("No hay imports")

            # Verificar errores de sintaxis
            try:
                compile(content, script_path, "exec")
            except SyntaxError as e:
                issues.append(f"Error de sintaxis: {str(e)}")

        # Verificar permisos de ejecución
        if not os.access(script_path, os.X_OK):
            issues.append("No tiene permisos de ejecución")

        # Verificar tamaño
        if len(content) < 50:
            issues.append("Script muy pequeño")

        # Verificar líneas vacías al final
        if content.endswith("\n\n\n"):
            issues.append("Múltiples líneas vacías al final")

        return issues

    except Exception as e:
        return [f"Error al analizar: {str(e)}"]


def review_scripts():
    """Revisa la calidad de los scripts en /tools"""
    print("Revisando calidad de scripts...")

    # Diccionario para almacenar scripts con problemas
    problematic_scripts = {}

    # Recorrer todos los archivos en /tools y subdirectorios
    for root, _, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".sh"):
                # Ignorar enlaces simbólicos
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue

                # Verificar calidad
                issues = check_script_quality(file_path)
                if issues:
                    problematic_scripts[file_path] = issues

    if problematic_scripts:
        print(f"Se encontraron {len(problematic_scripts)} scripts con problemas:")
        for path, issues in problematic_scripts.items():
            print(f"  Script: {os.path.basename(path)}")
            print(f"    Ruta: {path}")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("No se encontraron scripts con problemas")

    return problematic_scripts


def fix_script_permissions():
    """Corrige los permisos de los scripts en /tools"""
    print("Corrigiendo permisos de scripts...")

    # Contador de scripts corregidos
    fixed_scripts = 0

    # Recorrer todos los archivos en /tools y subdirectorios
    for root, _, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".sh"):
                # Ignorar enlaces simbólicos
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue

                # Verificar permisos
                if not os.access(file_path, os.X_OK):
                    try:
                        os.chmod(file_path, 0o755)
                        print(f"  ✅ Permisos corregidos: {file_path}")
                        fixed_scripts += 1
                    except Exception as e:
                        print(
                            f"  ❌ Error al corregir permisos: {file_path} - {str(e)}"
                        )

    print(f"Se corrigieron los permisos de {fixed_scripts} scripts")
    return fixed_scripts


def add_missing_shebangs():
    """Añade shebangs faltantes a los scripts"""
    print("Añadiendo shebangs faltantes...")

    # Contador de scripts corregidos
    fixed_scripts = 0

    # Recorrer todos los archivos en /tools y subdirectorios
    for root, _, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".sh"):
                # Ignorar enlaces simbólicos
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue

                try:
                    # Leer el contenido del script
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Verificar shebang
                    first_line = content.split("\n")[0] if content else ""
                    if not first_line.startswith("#!"):
                        # Añadir shebang
                        if file.endswith(".py"):
                            new_content = "#!/usr/bin/env python3\n" + content
                        elif file.endswith(".sh"):
                            new_content = "#!/bin/bash\n" + content
                        else:
                            continue

                        # Guardar el archivo
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)

                        print(f"  ✅ Shebang añadido: {file_path}")
                        fixed_scripts += 1

                except Exception as e:
                    print(f"  ❌ Error al añadir shebang: {file_path} - {str(e)}")

    print(f"Se añadieron shebangs a {fixed_scripts} scripts")
    return fixed_scripts


def organize_scripts_in_root():
    """Organiza los scripts que están directamente en /tools"""
    print("Organizando scripts en el directorio raíz de /tools...")

    # Definir categorías y patrones de nombres de archivos
    categories = {
        "admin_utils": ["admin", "user", "permission", "role", "unlock"],
        "db_utils": ["db", "mongo", "database", "collection", "catalog"],
        "maintenance": [
            "maintenance",
            "backup",
            "clean",
            "update",
            "monitor",
            "supervise",
            "start",
            "stop",
            "restart",
        ],
        "monitoring": ["monitor", "check", "diagnose", "log", "status", "health"],
        "aws_utils": ["aws", "s3", "bucket", "cloud"],
        "image_utils": ["image", "photo", "picture", "thumbnail"],
        "session_utils": ["session", "cookie", "auth", "login"],
        "system": ["system", "os", "process", "service", "daemon"],
        "utils": ["util", "helper", "tool", "test"],
    }

    # Asegurar que los subdirectorios existen
    for category in categories:
        ensure_directory(os.path.join(TOOLS_DIR, category))

    # Listar todos los scripts en el directorio raíz de /tools
    scripts_moved = 0
    for item in os.listdir(TOOLS_DIR):
        source_item = os.path.join(TOOLS_DIR, item)

        # Solo procesar archivos, no directorios ni enlaces simbólicos
        if (
            os.path.isfile(source_item)
            and not os.path.islink(source_item)
            and (item.endswith(".py") or item.endswith(".sh"))
        ):
            # Ignorar archivos específicos que deben permanecer en el directorio raíz
            if item in [
                "script_runner.py",
                "fix_script_paths.py",
                "migrate_scripts.py",
                "cleanup_tools_directory.py",
                "__init__.py",
            ]:
                continue

            # Determinar la categoría del script
            category = None
            for cat, patterns in categories.items():
                for pattern in patterns:
                    if pattern in item.lower():
                        category = cat
                        break
                if category:
                    break

            # Si no se encontró una categoría, usar 'utils'
            if not category:
                category = "utils"

            # Mover el script a su categoría
            target_dir = os.path.join(TOOLS_DIR, category)
            target_item = os.path.join(target_dir, item)

            # Verificar si el archivo ya existe en el destino
            if os.path.exists(target_item):
                print(f"  ⚠️ El archivo ya existe en el destino: {target_item}")
                continue

            # Mover el archivo
            shutil.move(source_item, target_item)
            print(f"  ✅ Archivo categorizado: {item} -> {category}")
            scripts_moved += 1

    print(f"Se categorizaron {scripts_moved} scripts del directorio raíz")
    return scripts_moved


def remove_broken_symlinks():
    """Elimina enlaces simbólicos rotos"""
    print("Eliminando enlaces simbólicos rotos...")

    # Contador de enlaces eliminados
    removed_links = 0

    # Recorrer todos los archivos en /tools
    for item in os.listdir(TOOLS_DIR):
        item_path = os.path.join(TOOLS_DIR, item)

        # Verificar si es un enlace simbólico roto
        if os.path.islink(item_path) and not os.path.exists(os.readlink(item_path)):
            try:
                os.unlink(item_path)
                print(f"  ✅ Enlace roto eliminado: {item_path}")
                removed_links += 1
            except Exception as e:
                print(f"  ❌ Error al eliminar enlace: {item_path} - {str(e)}")

    print(f"Se eliminaron {removed_links} enlaces simbólicos rotos")
    return removed_links


def run_fix_script_paths():
    """Ejecuta el script fix_script_paths.py"""
    print("Ejecutando fix_script_paths.py...")

    fix_script = os.path.join(TOOLS_DIR, "fix_script_paths.py")
    if not os.path.exists(fix_script):
        print(f"❌ No se encontró el script {fix_script}")
        return False

    try:
        result = subprocess.run(
            [fix_script], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print("✅ fix_script_paths.py ejecutado correctamente")
            return True
        else:
            print(f"❌ Error al ejecutar fix_script_paths.py: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error al ejecutar fix_script_paths.py: {str(e)}")
        return False


def restart_service():
    """Reinicia el servicio edefrutos2025"""
    print("Reiniciando el servicio edefrutos2025...")

    try:
        result = subprocess.run(
            ["systemctl", "restart", "edefrutos2025"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✅ Servicio reiniciado correctamente")

            # Verificar el estado del servicio
            status_result = subprocess.run(
                ["systemctl", "status", "edefrutos2025"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "Active: active (running)" in status_result.stdout:
                print("✅ El servicio está activo y en ejecución")
                return True
            else:
                print(f"❌ El servicio no está en ejecución: {status_result.stdout}")
                return False
        else:
            print(f"❌ Error al reiniciar el servicio: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error al reiniciar el servicio: {str(e)}")
        return False


def test_script_execution():
    """Prueba la ejecución de algunos scripts desde la interfaz web"""
    print("Probando la ejecución de scripts...")

    # Lista de scripts a probar
    test_scripts = [
        "test_script.sh",
        "supervise_gunicorn_web.sh",
        "check_logs.py",
        "check_mongodb.py",
    ]

    # Probar cada script
    success_count = 0
    for script in test_scripts:
        print(f"  Probando script: {script}")

        # Buscar el script
        script_found = False
        script_path = None

        # Buscar en el directorio raíz (enlaces simbólicos)
        root_path = os.path.join(TOOLS_DIR, script)
        if os.path.exists(root_path):
            script_found = True
            script_path = root_path

        # Si no se encuentra, buscar en subdirectorios
        if not script_found:
            for root, _, files in os.walk(TOOLS_DIR):
                if script in files:
                    script_found = True
                    script_path = os.path.join(root, script)
                    break

        if not script_found:
            print(f"    ❌ Script no encontrado: {script}")
            continue

        # Probar la ejecución del script
        try:
            # Usar script_runner.py para ejecutar el script
            runner_path = os.path.join(TOOLS_DIR, "script_runner.py")
            if not os.path.exists(runner_path):
                print("    ❌ script_runner.py no encontrado")
                continue

            result = subprocess.run(
                [sys.executable, runner_path, script_path],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # Verificar el resultado
            try:
                result_json = json.loads(result.stdout)
                exit_code = result_json.get("exit_code")

                if exit_code == 0:
                    print("    ✅ Script ejecutado correctamente")
                    success_count += 1
                else:
                    print(f"    ⚠️ Script ejecutado con errores (código {exit_code})")
            except Exception as e:
                print(f"    ❌ Error al analizar la salida: {str(e)}")

        except Exception as e:
            print(f"    ❌ Error al ejecutar el script: {str(e)}")

    print(f"Se ejecutaron correctamente {success_count} de {len(test_scripts)} scripts")
    return success_count == len(test_scripts)


def main():
    print_header("LIMPIEZA Y ORGANIZACIÓN DEL DIRECTORIO /TOOLS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Encontrar scripts duplicados
    print_header("BUSCANDO SCRIPTS DUPLICADOS")
    duplicates = find_duplicate_scripts()

    # Revisar calidad de scripts
    print_header("REVISANDO CALIDAD DE SCRIPTS")
    problematic_scripts = review_scripts()

    # Corregir permisos de scripts
    print_header("CORRIGIENDO PERMISOS DE SCRIPTS")
    fixed_permissions = fix_script_permissions()

    # Añadir shebangs faltantes
    print_header("AÑADIENDO SHEBANGS FALTANTES")
    fixed_shebangs = add_missing_shebangs()

    # Organizar scripts en el directorio raíz
    print_header("ORGANIZANDO SCRIPTS EN EL DIRECTORIO RAÍZ")
    organized_scripts = organize_scripts_in_root()

    # Eliminar enlaces simbólicos rotos
    print_header("ELIMINANDO ENLACES SIMBÓLICOS ROTOS")
    removed_links = remove_broken_symlinks()

    # Ejecutar fix_script_paths.py
    print_header("EJECUTANDO FIX_SCRIPT_PATHS.PY")
    run_fix_script_paths()

    # Reiniciar el servicio
    print_header("REINICIANDO EL SERVICIO")
    service_restarted = restart_service()

    # Probar la ejecución de scripts
    print_header("PROBANDO LA EJECUCIÓN DE SCRIPTS")
    scripts_executable = test_script_execution()

    print_header("LIMPIEZA Y ORGANIZACIÓN COMPLETADA")
    print("Se han realizado las siguientes acciones:")
    print(f"1. Se encontraron {len(duplicates)} scripts duplicados")
    print(f"2. Se encontraron {len(problematic_scripts)} scripts con problemas")
    print(f"3. Se corrigieron los permisos de {fixed_permissions} scripts")
    print(f"4. Se añadieron shebangs a {fixed_shebangs} scripts")
    print(f"5. Se organizaron {organized_scripts} scripts del directorio raíz")
    print(f"6. Se eliminaron {removed_links} enlaces simbólicos rotos")
    print("7. Se ejecutó fix_script_paths.py para crear enlaces simbólicos")
    print(
        f"8. {'✅' if service_restarted else '❌'} El servicio edefrutos2025 se "
        f"reinició {'correctamente' if service_restarted else 'con errores'}"
    )
    print(
        f"9. {'✅' if scripts_executable else '❌'} Los scripts son "
        f"{'accesibles y ejecutables' if scripts_executable else 'no accesibles o ejecutables'}"
    )

    if not service_restarted or not scripts_executable:
        print("\n⚠️ Se encontraron problemas que requieren atención:")
        if not service_restarted:
            print("  - El servicio edefrutos2025 no se reinició correctamente")
        if not scripts_executable:
            print("  - Algunos scripts no son accesibles o ejecutables")
    else:
        print(
            "\n✅ Todo funciona correctamente.\n"
            "   Los scripts están organizados y son accesibles y ejecutables."
        )


if __name__ == "__main__":
    main()
