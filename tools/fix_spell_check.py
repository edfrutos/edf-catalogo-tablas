#!/usr/bin/env python3
"""
Script simplificado para solucionar problemas de spell check
"""

import subprocess
import sys
from pathlib import Path


def check_and_install_toml():
    """Verificar e instalar toml si es necesario"""
    try:
        # Solo verificar si el módulo está disponible
        import importlib

        _ = importlib.import_module("toml")
        print("✅ Módulo toml ya está instalado")
        return True
    except ImportError:
        print("❌ Módulo toml no encontrado. Instalando...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "toml"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ Módulo toml instalado exitosamente")
                return True
            else:
                print(f"❌ Error instalando toml: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def run_script_safely(script_path, description):
    """Ejecutar script de forma segura"""
    print(f"\n🚀 {description}")
    print("-" * 50)

    if not Path(script_path).exists():
        print(f"❌ Script no encontrado: {script_path}")
        return False

    try:
        # Usar el mismo intérprete de Python
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            print("✅ Script ejecutado exitosamente")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Error en script: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Script se interrumpió por timeout (5 minutos)")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        return False


def main():
    """Función principal"""
    print("🔧 SOLUCIONANDO PROBLEMAS DE SPELL CHECK")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not Path("pyproject.toml").exists():
        print("❌ Error: No se encontró pyproject.toml")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return 1

    # Paso 1: Verificar e instalar dependencias
    print("\n📋 PASO 1: Verificando dependencias...")
    if not check_and_install_toml():
        print("❌ No se pudo instalar toml. Saliendo...")
        return 1

    # Paso 2: Configurar IDEs
    print("\n📋 PASO 2: Configurando IDEs...")
    _ = run_script_safely("tools/setup_ide_spell_check.py", "Configurando IDEs")

    # Paso 3: Ejecutar flujo completo (con timeout)
    print("\n📋 PASO 3: Ejecutando flujo completo...")
    success = run_script_safely(
        "tools/complete_spell_check_workflow.py", "Flujo completo"
    )

    if not success:
        print("\n⚠️  El flujo completo se interrumpió. Verificando archivos creados...")

    # Paso 4: Verificar archivos creados
    print("\n📋 PASO 4: Verificando archivos creados...")

    files_to_check = [
        ".vscode/settings.json",
        "cspell.json",
        "pycharm_spell_check_config.json",
        "SPELL_CHECK_SETUP.md",
        "config/dictionaries/spell_check_config.json",
    ]

    created_files = []
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            created_files.append((file_path, size))
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (no encontrado)")

    # Paso 5: Mostrar resumen
    print("\n📊 RESUMEN:")
    print(f"  📁 Archivos de configuración creados: {len(created_files)}")

    if Path("config/dictionaries").exists():
        dict_files = list(Path("config/dictionaries").glob("*.txt"))
        print(f"  📚 Diccionarios creados: {len(dict_files)}")
        for dict_file in dict_files:
            try:
                with open(dict_file, encoding="utf-8") as f:
                    lines = len(f.readlines())
                print(f"    📄 {dict_file.name}: {lines:,} palabras")
            except Exception as e:
                print(f"    ❌ Error leyendo {dict_file.name}: {e}")

    print("\n✅ ¡Proceso completado!")
    print("\n📋 Próximos pasos:")
    print("  1. Instalar extensiones de VS Code:")
    print("     - Code Spell Checker (cspell)")
    print("     - Spell Right")
    print("  2. Instalar cspell globalmente:")
    print("     npm install -g cspell")
    print("  3. Configurar PyCharm según pycharm_spell_check_config.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
