#!/usr/bin/env python3
"""
Script interactivo para unificar/sincronizar contenido de archivos txt
Autor: EDF Developer - 2025
"""

import glob
import os
from typing import List, Optional

# Importar funciones del script original
from unify_files import (
    compare_files,
    sync_files,
    unify_append,
    unify_merge,
)


def get_file_list(directory: str = ".") -> List[str]:
    """Obtiene lista de archivos txt en el directorio."""
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    # Filtrar solo archivos (no directorios) y obtener nombres base
    file_list = []
    for f in txt_files:
        if os.path.isfile(f):
            file_list.append(os.path.basename(f))
    return sorted(file_list)


def select_directory() -> str:
    """Permite al usuario seleccionar el directorio de búsqueda."""
    print("\n📂 Selección de directorio de búsqueda:")
    print("  1. Directorio actual")
    print("  2. Directorio raíz del proyecto")
    print("  3. Directorio específico")
    print("  4. Explorar directorios")

    while True:
        choice = input("\n🔢 Selecciona una opción: ").strip()

        if choice == "1":
            return "."
        elif choice == "2":
            # Buscar el directorio raíz del proyecto (donde está config.py)
            current_dir = os.getcwd()
            while current_dir != "/":
                if os.path.exists(os.path.join(current_dir, "config.py")):
                    return current_dir
                current_dir = os.path.dirname(current_dir)
            return "."
        elif choice == "3":
            while True:
                dir_path = input("\n📁 Ingresa la ruta del directorio: ").strip()
                if not dir_path:
                    print("❌ Por favor ingresa una ruta válida.")
                    continue

                # Expandir ~ si está presente
                dir_path = os.path.expanduser(dir_path)

                if os.path.isdir(dir_path):
                    return dir_path
                else:
                    print(f"❌ El directorio '{dir_path}' no existe.")
                    create = (
                        input("¿Quieres crear este directorio? (s/n): ").strip().lower()
                    )
                    if create in ["s", "si", "sí", "y", "yes"]:
                        try:
                            os.makedirs(dir_path, exist_ok=True)
                            print(f"✅ Directorio '{dir_path}' creado.")
                            return dir_path
                        except Exception as e:
                            print(f"❌ Error creando directorio: {e}")
                    else:
                        print("❌ Operación cancelada.")
        elif choice == "4":
            return explore_directories()
        else:
            print("❌ Opción inválida. Intenta de nuevo.")


def explore_directories() -> str:
    """Explora directorios de forma interactiva."""
    current_dir = os.getcwd()

    while True:
        print(f"\n📂 Directorio actual: {current_dir}")

        # Obtener subdirectorios
        try:
            items = os.listdir(current_dir)
            directories = []
            for item in items:
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    directories.append(item)

            if directories:
                print("\n📁 Subdirectorios disponibles:")
                for i, dir_name in enumerate(sorted(directories), 1):
                    print(f"  {i}. {dir_name}/")

            print("\n🔧 Opciones:")
            print("  0. Usar este directorio")
            print("  .. Subir un nivel")
            print("  / Ir al directorio raíz")
            print("  ~ Ir al directorio home")
            print("  cancel Cancelar")

            choice = input("\n🔢 Selecciona una opción: ").strip()

            if choice == "0":
                return current_dir
            elif choice == "..":
                parent_dir = os.path.dirname(current_dir)
                if parent_dir != current_dir:
                    current_dir = parent_dir
                else:
                    print("❌ Ya estás en el directorio raíz.")
            elif choice == "/":
                current_dir = "/"
            elif choice == "~":
                current_dir = os.path.expanduser("~")
            elif choice.lower() in ["cancel", "c", "salir", "s"]:
                return "."
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(directories):
                    current_dir = os.path.join(current_dir, directories[choice_num - 1])
                else:
                    print("❌ Número inválido.")
            else:
                print("❌ Opción inválida.")

        except PermissionError:
            print(f"❌ No tienes permisos para acceder a {current_dir}")
            return "."
        except Exception as e:
            print(f"❌ Error: {e}")
            return "."


def select_file_from_list(
    files: List[str], prompt: str, directory: str = "."
) -> Optional[str]:
    """Permite al usuario seleccionar un archivo de una lista."""
    if not files:
        print("❌ No hay archivos .txt en el directorio especificado")
        print(f"📂 Directorio: {directory}")
        print(f"🔍 Buscando archivos .txt...")
        return None

    print(f"\n{prompt}")
    print("📁 Archivos disponibles:")

    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")

    print("  0. Cancelar")

    while True:
        try:
            choice = input("\n🔢 Selecciona un número: ").strip()
            if choice == "0":
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(files):
                # Retornar ruta completa si no es el directorio actual
                if directory != ".":
                    return os.path.join(directory, files[choice_num - 1])
                else:
                    return files[choice_num - 1]
            else:
                print("❌ Número inválido. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")


def input_file_path(prompt: str) -> Optional[str]:
    """Permite al usuario ingresar la ruta de un archivo."""
    while True:
        file_path = input(f"\n{prompt} (o 'cancel' para cancelar): ").strip()

        if file_path.lower() in ["cancel", "c", "salir", "s"]:
            return None

        if not file_path:
            print("❌ Por favor ingresa una ruta válida.")
            continue

        # Expandir ~ si está presente
        file_path = os.path.expanduser(file_path)

        if os.path.exists(file_path):
            return file_path
        else:
            print(f"❌ El archivo '{file_path}' no existe.")
            create = input("¿Quieres crear este archivo? (s/n): ").strip().lower()
            if create in ["s", "si", "sí", "y", "yes"]:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("")
                    print(f"✅ Archivo '{file_path}' creado.")
                    return file_path
                except Exception as e:
                    print(f"❌ Error creando archivo: {e}")
            else:
                print("❌ Operación cancelada.")


def select_operation() -> Optional[str]:
    """Permite al usuario seleccionar la operación."""
    operations = {"1": "append", "2": "merge", "3": "sync", "4": "compare"}

    print("\n🛠️  Operaciones disponibles:")
    print("  1. Append - Añadir contenido del archivo2 al final del archivo1")
    print("  2. Merge - Combinar archivos eliminando duplicados")
    print("  3. Sync - Sincronizar ambos archivos con el mismo contenido")
    print("  4. Compare - Comparar archivos y mostrar diferencias")
    print("  0. Salir")

    while True:
        choice = input("\n🔢 Selecciona una operación: ").strip()

        if choice == "0":
            return None

        if choice in operations:
            return operations[choice]
        else:
            print("❌ Opción inválida. Intenta de nuevo.")


def interactive_mode():
    """Modo interactivo principal."""
    print("🎯 Modo Interactivo - Unificador de Archivos TXT")
    print("=" * 50)

    # Seleccionar directorio de búsqueda
    search_directory = select_directory()
    print(f"\n📂 Directorio de búsqueda seleccionado: {search_directory}")

    # Obtener archivos disponibles del directorio seleccionado
    available_files = get_file_list(search_directory)

    # Seleccionar primer archivo
    print(f"\n📂 Directorio actual: {os.getcwd()}")

    file1 = None
    if available_files:
        print("\n¿Cómo quieres seleccionar el primer archivo?")
        print("  1. Seleccionar de la lista")
        print("  2. Ingresar ruta manualmente")

        choice = input("🔢 Opción: ").strip()

        if choice == "1":
            file1 = select_file_from_list(
                available_files, "Selecciona el primer archivo:", search_directory
            )
        elif choice == "2":
            file1 = input_file_path("Ingresa la ruta del primer archivo:")
    else:
        file1 = input_file_path("Ingresa la ruta del primer archivo:")

    if not file1:
        print("❌ Operación cancelada.")
        return

    # Seleccionar segundo archivo
    file2 = None
    if available_files:
        print("\n¿Cómo quieres seleccionar el segundo archivo?")
        print("  1. Seleccionar de la lista")
        print("  2. Ingresar ruta manualmente")

        choice = input("🔢 Opción: ").strip()

        if choice == "1":
            file2 = select_file_from_list(
                available_files, "Selecciona el segundo archivo:", search_directory
            )
        elif choice == "2":
            file2 = input_file_path("Ingresa la ruta del segundo archivo:")
    else:
        file2 = input_file_path("Ingresa la ruta del segundo archivo:")

    if not file2:
        print("❌ Operación cancelada.")
        return

    # Seleccionar operación
    operation = select_operation()
    if not operation:
        print("❌ Operación cancelada.")
        return

    # Ejecutar operación
    print(f"\n🚀 Ejecutando operación: {operation}")
    print(f"📄 Archivo 1: {file1}")
    print(f"📄 Archivo 2: {file2}")

    try:
        if operation == "append":
            success = unify_append(file1, file2)
        elif operation == "merge":
            success = unify_merge(file1, file2)
        elif operation == "sync":
            success = sync_files(file1, file2)
        elif operation == "compare":
            success = compare_files(file1, file2)

        if success:
            print("\n✅ Operación completada exitosamente!")
        else:
            print("\n❌ Error en la operación.")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def batch_mode():
    """Modo batch para procesar múltiples archivos."""
    print("📦 Modo Batch - Procesamiento de Múltiples Archivos")
    print("=" * 50)

    # Seleccionar directorio de búsqueda
    search_directory = select_directory()
    print(f"\n📂 Directorio de búsqueda seleccionado: {search_directory}")

    # Obtener archivos del directorio seleccionado
    available_files = get_file_list(search_directory)

    if len(available_files) < 2:
        print("❌ Se necesitan al menos 2 archivos .txt para el modo batch.")
        return

    print(f"\n📁 Archivos disponibles: {', '.join(available_files)}")

    # Seleccionar archivos a procesar
    print("\n¿Qué archivos quieres procesar?")
    print("  1. Todos los archivos .txt")
    print("  2. Seleccionar archivos específicos")

    choice = input("🔢 Opción: ").strip()

    files_to_process = []
    if choice == "1":
        files_to_process = available_files
    elif choice == "2":
        print("\nSelecciona los archivos (números separados por comas):")
        for i, file in enumerate(available_files, 1):
            print(f"  {i}. {file}")

        try:
            selections = input("🔢 Números: ").strip().split(",")
            for sel in selections:
                idx = int(sel.strip()) - 1
                if 0 <= idx < len(available_files):
                    files_to_process.append(available_files[idx])
        except ValueError:
            print("❌ Formato inválido.")
            return
    else:
        print("❌ Opción inválida.")
        return

    if len(files_to_process) < 2:
        print("❌ Se necesitan al menos 2 archivos para procesar.")
        return

    # Seleccionar operación
    operation = select_operation()
    if not operation:
        print("❌ Operación cancelada.")
        return

    # Procesar archivos
    print(
        f"\n🚀 Procesando {len(files_to_process)} archivos con operación: {operation}"
    )

    for i in range(len(files_to_process) - 1):
        file1 = files_to_process[i]
        file2 = files_to_process[i + 1]

        print(f"\n📄 Procesando: {file1} + {file2}")

        try:
            if operation == "append":
                success = unify_append(file1, file2)
            elif operation == "merge":
                success = unify_merge(file1, file2)
            elif operation == "sync":
                success = sync_files(file1, file2)
            elif operation == "compare":
                success = compare_files(file1, file2)

            if success:
                print(f"✅ {file1} + {file2} procesados exitosamente!")
            else:
                print(f"❌ Error procesando {file1} + {file2}")

        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Función principal."""
    print("🎯 Unificador Interactivo de Archivos TXT")
    print("=" * 50)

    while True:
        print("\n📋 Modos disponibles:")
        print("  1. Modo Interactivo (archivos individuales)")
        print("  2. Modo Batch (múltiples archivos)")
        print("  3. Modo Comando (argumentos)")
        print("  0. Salir")

        choice = input("\n🔢 Selecciona un modo: ").strip()

        if choice == "0":
            print("👋 ¡Hasta luego!")
            break
        elif choice == "1":
            interactive_mode()
        elif choice == "2":
            batch_mode()
        elif choice == "3":
            print("\n💡 Para usar el modo comando, ejecuta:")
            print(
                "   python3 tools/utils/unify_files.py archivo1.txt archivo2.txt --mode merge"
            )
            print("   ./tools/utils/unify_files.sh archivo1.txt archivo2.txt merge")
            break
        else:
            print("❌ Opción inválida. Intenta de nuevo.")


if __name__ == "__main__":
    main()
