#!/usr/bin/env python3
"""
Script de limpieza masiva del código
Aplica correcciones automáticas de linting a todos los archivos Python
"""

import os
import subprocess
import sys
from pathlib import Path


def find_python_files():
    """Encuentra todos los archivos Python del proyecto"""
    python_files = []
    project_root = Path(".")

    # Directorios a excluir
    exclude_dirs = {".venv", "venv", ".venv310", "__pycache__", ".git", "node_modules"}

    for py_file in project_root.rglob("*.py"):
        # Excluir directorios específicos
        if any(exclude_dir in py_file.parts for exclude_dir in exclude_dirs):
            continue
        python_files.append(py_file)

    return sorted(python_files)


def run_autopep8(file_path):
    """Ejecuta autopep8 en un archivo"""
    try:
        cmd = [
            "autopep8",
            "--in-place",
            "--aggressive",
            "--aggressive",
            "--max-line-length=88",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️  autopep8 no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "autopep8"])
        return run_autopep8(file_path)


def run_isort(file_path):
    """Ejecuta isort para ordenar imports"""
    try:
        cmd = ["isort", "--profile", "black", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️  isort no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "isort"])
        return run_isort(file_path)


def run_black(file_path):
    """Ejecuta black para formateo"""
    try:
        cmd = ["black", "--line-length=88", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️  black no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "black"])
        return run_black(file_path)


def cleanup_file(file_path):
    """Limpia un archivo Python específico"""
    print(f"🔧 Limpiando: {file_path}")

    # 1. Ordenar imports
    if run_isort(file_path):
        print(f"  ✅ Imports ordenados")

    # 2. Aplicar autopep8
    if run_autopep8(file_path):
        print(f"  ✅ PEP 8 aplicado")

    # 3. Aplicar black (formateo final)
    if run_black(file_path):
        print(f"  ✅ Black aplicado")

    return True


def main():
    """Función principal de limpieza masiva"""
    print("🧹 LIMPIEZA MASIVA DE CÓDIGO PYTHON")
    print("=" * 50)

    # Encontrar archivos Python
    python_files = find_python_files()
    print(f"📁 Encontrados {len(python_files)} archivos Python")

    if not python_files:
        print("❌ No se encontraron archivos Python")
        return

    # Mostrar archivos que se van a limpiar
    print("\n📋 Archivos a procesar:")
    for i, file_path in enumerate(python_files[:10], 1):
        print(f"  {i}. {file_path}")
    if len(python_files) > 10:
        print(f"  ... y {len(python_files) - 10} archivos más")

    # Procesar archivos automáticamente
    processed = 0
    errors = 0

    for file_path in python_files:
        try:
            if cleanup_file(file_path):
                processed += 1
            else:
                errors += 1
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
            errors += 1

    # Resumen
    print("\n" + "=" * 50)
    print(f"🎉 LIMPIEZA COMPLETADA:")
    print(f"  ✅ Archivos procesados: {processed}")
    print(f"  ❌ Errores: {errors}")
    print(f"  📊 Total: {len(python_files)} archivos")

    if errors == 0:
        print("\n🚀 ¡Todos los archivos limpiados exitosamente!")
    else:
        print(f"\n⚠️  {errors} archivos tuvieron problemas")


if __name__ == "__main__":
    main()
