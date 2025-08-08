#!/usr/bin/env python3
# Script: verificar_configuracion.py
# Descripción: Verifica que la configuración de Python e IntelliCode esté correcta
# Autor: EDF Developer - 2025-01-XX

import os
import sys
import json
from pathlib import Path


def verificar_configuracion():
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN PYTHON + INTELLICODE")
    print("=" * 60)

    # Verificar directorio .vscode
    vscode_dir = Path(".vscode")
    if not vscode_dir.exists():
        print("❌ Directorio .vscode no encontrado")
        return False

    print("✅ Directorio .vscode encontrado")

    # Verificar settings.json
    settings_file = vscode_dir / "settings.json"
    if not settings_file.exists():
        print("❌ Archivo settings.json no encontrado")
        return False

    print("✅ Archivo settings.json encontrado")

    # Leer y verificar settings.json
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ Error al leer settings.json: {e}")
        return False

    # Verificar configuración del intérprete Python
    python_path = settings.get("python.defaultInterpreterPath", "")
    if python_path:
        if python_path.startswith("./venv310/bin/python"):
            print("✅ Intérprete Python configurado correctamente (ruta relativa)")
        else:
            print(f"⚠️  Intérprete Python configurado: {python_path}")
    else:
        print("❌ Intérprete Python no configurado")

    # Verificar modo de verificación de tipos
    type_checking = settings.get("python.analysis.typeCheckingMode", "")
    if type_checking:
        print(f"✅ Modo de verificación de tipos: {type_checking}")
    else:
        print("❌ Modo de verificación de tipos no configurado")

    # Verificar configuración de IntelliCode
    intellicode_configs = [
        "intellicode.python.deepLearning",
        "intellicode.completions.enabled",
        "intellicode.insights.enabled",
    ]

    print("\n🔧 CONFIGURACIÓN INTELLICODE:")
    for config in intellicode_configs:
        value = settings.get(config, "no configurado")
        if value != "no configurado":
            print(f"✅ {config}: {value}")
        else:
            print(f"❌ {config}: no configurado")

    # Verificar extensiones
    extensions_file = vscode_dir / "extensions.json"
    if extensions_file.exists():
        try:
            with open(extensions_file, "r", encoding="utf-8") as f:
                extensions = json.load(f)

            print("\n📦 EXTENSIONES RECOMENDADAS:")
            for ext in extensions.get("recommendations", []):
                if ext.startswith("ms-python."):
                    print(f"✅ {ext}")
        except Exception as e:
            print(f"❌ Error al leer extensions.json: {e}")

    # Verificar entorno virtual
    venv_path = Path("venv310")
    if venv_path.exists():
        python_exe = venv_path / "bin" / "python"
        if python_exe.exists():
            print(f"\n✅ Entorno virtual encontrado: {venv_path}")
            print(f"✅ Python del entorno: {python_exe}")
        else:
            print(f"❌ Python no encontrado en {python_exe}")
    else:
        print(f"❌ Entorno virtual no encontrado en {venv_path}")

    print("\n🎯 RECOMENDACIONES:")
    print("1. Reinicia VS Code/Cursor después de aplicar los cambios")
    print("2. Verifica que el intérprete Python esté correctamente configurado")
    print("3. Asegúrate de que las extensiones estén instaladas")
    print("4. Revisa la ventana de salida 'Python' para errores específicos")
    print("5. Revisa la ventana de salida 'VS IntelliCode' para errores específicos")

    return True


if __name__ == "__main__":
    verificar_configuracion()
