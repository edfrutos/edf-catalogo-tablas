#!/usr/bin/env python3
# Script: check_python_intellicode.py
# Descripción: Diagnóstico de configuración de Python e IntelliCode
# Uso: python3 check_python_intellicode.py
# Autor: EDF Developer - 2025-01-28

import os
import sys
import json
import subprocess
from pathlib import Path


def check_python_environment():
    """Verificar el entorno de Python"""
    print("=== DIAGNÓSTICO DE ENTORNO PYTHON ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")

    # Verificar entorno virtual
    venv_path = Path("./venv310")
    if venv_path.exists():
        print(f"✓ Entorno virtual encontrado: {venv_path.absolute()}")
        python_venv = venv_path / "bin" / "python"
        if python_venv.exists():
            print(f"✓ Python del entorno virtual: {python_venv}")
        else:
            print("✗ Python del entorno virtual no encontrado")
    else:
        print("✗ Entorno virtual no encontrado")


def check_vscode_config():
    """Verificar configuración de VS Code/Cursor"""
    print("\n=== CONFIGURACIÓN VS CODE/CURSOR ===")

    vscode_dir = Path(".vscode")
    if vscode_dir.exists():
        print(f"✓ Directorio .vscode encontrado")

        settings_file = vscode_dir / "settings.json"
        if settings_file.exists():
            print(f"✓ Archivo settings.json encontrado")
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                # Verificar configuraciones clave
                python_config = settings.get("python", {})
                if python_config.get("defaultInterpreterPath"):
                    print(
                        f"✓ Interprete Python configurado: {python_config['defaultInterpreterPath']}"
                    )
                else:
                    print("✗ Interprete Python no configurado")

                if python_config.get("analysis", {}).get("typeCheckingMode"):
                    print(
                        f"✓ Modo de verificación de tipos: {python_config['analysis']['typeCheckingMode']}"
                    )
                else:
                    print("✗ Modo de verificación de tipos no configurado")

            except json.JSONDecodeError as e:
                print(f"✗ Error al leer settings.json: {e}")
        else:
            print("✗ Archivo settings.json no encontrado")
    else:
        print("✗ Directorio .vscode no encontrado")


def check_pyright_config():
    """Verificar configuración de Pyright"""
    print("\n=== CONFIGURACIÓN PYRIGHT ===")

    pyright_file = Path("pyrightconfig.json")
    if pyright_file.exists():
        print(f"✓ Archivo pyrightconfig.json encontrado")
        try:
            with open(pyright_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Verificar configuraciones importantes
            if config.get("pythonVersion"):
                print(f"✓ Versión Python: {config['pythonVersion']}")

            if config.get("include"):
                print(f"✓ Directorios incluidos: {config['include']}")

            if config.get("exclude"):
                print(f"✓ Directorios excluidos: {config['exclude']}")

        except json.JSONDecodeError as e:
            print(f"✗ Error al leer pyrightconfig.json: {e}")
    else:
        print("✗ Archivo pyrightconfig.json no encontrado")


def check_pylint_config():
    """Verificar configuración de Pylint"""
    print("\n=== CONFIGURACIÓN PYLINT ===")

    pylint_file = Path(".pylintrc")
    if pylint_file.exists():
        print(f"✓ Archivo .pylintrc encontrado")
        try:
            with open(pylint_file, "r", encoding="utf-8") as f:
                content = f.read()

            if "disable=all" in content:
                print("✓ Pylint deshabilitado globalmente")
            else:
                print("⚠ Pylint puede estar activo")

        except Exception as e:
            print(f"✗ Error al leer .pylintrc: {e}")
    else:
        print("✗ Archivo .pylintrc no encontrado")


def check_extensions():
    """Verificar extensiones instaladas"""
    print("\n=== EXTENSIONES RECOMENDADAS ===")

    extensions_file = Path("extensiones_instaladas.txt")
    if extensions_file.exists():
        print(f"✓ Lista de extensiones encontrada")

        # Verificar extensiones clave
        key_extensions = [
            "ms-python.python",
            "ms-python.black-formatter",
            "ms-python.isort",
        ]

        with open(extensions_file, "r", encoding="utf-8") as f:
            content = f.read()

        for ext in key_extensions:
            if ext in content:
                print(f"✓ {ext} encontrada")
            else:
                print(f"✗ {ext} no encontrada")
    else:
        print("✗ Lista de extensiones no encontrada")


def check_intellicode_compatibility():
    """Verificar compatibilidad con IntelliCode"""
    print("\n=== COMPATIBILIDAD INTELLICODE ===")

    # Verificar si hay configuraciones que puedan causar conflictos
    vscode_dir = Path(".vscode")
    if vscode_dir.exists():
        settings_file = vscode_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                # Verificar configuraciones de IntelliCode
                intellicode_config = settings.get("intellicode", {})
                if intellicode_config.get("python.deepLearning") == "enabled":
                    print("✓ IntelliCode Python habilitado")
                else:
                    print("⚠ IntelliCode Python no configurado explícitamente")

                # Verificar configuraciones de linting que pueden causar conflictos
                python_config = settings.get("python", {})
                if not python_config.get("linting", {}).get("enabled"):
                    print("✓ Linting deshabilitado (compatible con IntelliCode)")
                else:
                    print("⚠ Linting puede estar activo (puede causar conflictos)")

            except json.JSONDecodeError:
                print("✗ Error al leer configuración de IntelliCode")
    else:
        print("✗ Configuración de VS Code no encontrada")


def main():
    """Función principal"""
    print("DIAGNÓSTICO DE CONFIGURACIÓN PYTHON + INTELLICODE")
    print("=" * 50)

    check_python_environment()
    check_vscode_config()
    check_pyright_config()
    check_pylint_config()
    check_extensions()
    check_intellicode_compatibility()

    print("\n=== RECOMENDACIONES ===")
    print("1. Reinicia VS Code/Cursor después de aplicar los cambios")
    print("2. Verifica que el interprete Python esté correctamente configurado")
    print(
        "3. Desactiva temporalmente otras extensiones de linting si persisten los problemas"
    )
    print("4. Revisa la ventana de salida 'Python' para errores específicos")
    print("5. Revisa la ventana de salida 'VS IntelliCode' para errores específicos")


if __name__ == "__main__":
    main()
