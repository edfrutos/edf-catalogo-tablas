#!/usr/bin/env python3
# Script: clear_python_cache.py
# Descripción: Limpiar cachés de Python que pueden causar conflictos con IntelliCode
# Uso: python3 clear_python_cache.py
# Autor: EDF Developer - 2025-01-28

import os
import shutil
import subprocess
from pathlib import Path


def clear_python_cache():
    """Limpiar cachés de Python"""
    print("=== LIMPIANDO CACHÉS DE PYTHON ===")

    # Directorios a limpiar
    cache_dirs = ["__pycache__", ".pytest_cache", ".mypy_cache", ".pyright_cache"]

    # Archivos a eliminar
    cache_files = ["*.pyc", "*.pyo", "*.pyd"]

    workspace = Path(".")

    for cache_dir in cache_dirs:
        for pycache in workspace.rglob(cache_dir):
            if pycache.is_dir():
                try:
                    shutil.rmtree(pycache)
                    print(f"✓ Eliminado: {pycache}")
                except Exception as e:
                    print(f"✗ Error eliminando {pycache}: {e}")

    # Limpiar archivos .pyc
    for pattern in cache_files:
        for pyc_file in workspace.rglob(pattern):
            if pyc_file.is_file():
                try:
                    pyc_file.unlink()
                    print(f"✓ Eliminado: {pyc_file}")
                except Exception as e:
                    print(f"✗ Error eliminando {pyc_file}: {e}")


def clear_vscode_cache():
    """Limpiar cachés de VS Code/Cursor"""
    print("\n=== LIMPIANDO CACHÉS DE VS CODE/CURSOR ===")

    # Directorios de caché de VS Code
    vscode_cache_dirs = [
        ".vscode/.ropeproject",
        ".vscode/.pytest_cache",
        ".vscode/.mypy_cache",
    ]

    for cache_dir in vscode_cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            try:
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                else:
                    cache_path.unlink()
                print(f"✓ Eliminado: {cache_path}")
            except Exception as e:
                print(f"✗ Error eliminando {cache_path}: {e}")


def restart_python_language_server():
    """Reiniciar el servidor de lenguaje Python"""
    print("\n=== REINICIANDO SERVIDOR DE LENGUAJE PYTHON ===")

    # Comando para reiniciar el servidor de lenguaje
    try:
        # Esto es más una sugerencia, ya que el reinicio real debe hacerse desde VS Code
        print("✓ Para reiniciar el servidor de lenguaje Python:")
        print("  1. Abre la paleta de comandos (Cmd+Shift+P)")
        print("  2. Ejecuta 'Python: Restart Language Server'")
        print("  3. O presiona Ctrl+Shift+P y busca 'Python: Restart Language Server'")
    except Exception as e:
        print(f"✗ Error: {e}")


def check_python_environment():
    """Verificar que el entorno Python esté funcionando"""
    print("\n=== VERIFICANDO ENTORNO PYTHON ===")

    try:
        # Verificar que Python funcione
        result = subprocess.run(
            [sys.executable, "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✓ Python funcionando: {result.stdout.strip()}")
        else:
            print(f"✗ Error con Python: {result.stderr}")
    except Exception as e:
        print(f"✗ Error verificando Python: {e}")

    # Verificar entorno virtual
    venv_path = Path("./venv310")
    if venv_path.exists():
        python_venv = venv_path / "bin" / "python"
        if python_venv.exists():
            try:
                result = subprocess.run(
                    [str(python_venv), "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"✓ Entorno virtual funcionando: {result.stdout.strip()}")
                else:
                    print(f"✗ Error con entorno virtual: {result.stderr}")
            except Exception as e:
                print(f"✗ Error verificando entorno virtual: {e}")
        else:
            print("✗ Python del entorno virtual no encontrado")
    else:
        print("✗ Entorno virtual no encontrado")


def main():
    """Función principal"""
    print("LIMPIEZA DE CACHÉS PARA RESOLVER CONFLICTOS INTELLICODE")
    print("=" * 60)

    clear_python_cache()
    clear_vscode_cache()
    restart_python_language_server()
    check_python_environment()

    print("\n=== PASOS ADICIONALES ===")
    print("1. Reinicia VS Code/Cursor completamente")
    print("2. Abre la paleta de comandos (Cmd+Shift+P)")
    print("3. Ejecuta 'Developer: Reload Window'")
    print("4. Verifica que el interprete Python esté seleccionado correctamente")
    print(
        "5. Si persisten los problemas, desactiva temporalmente otras extensiones de Python"
    )


if __name__ == "__main__":
    import sys

    main()
