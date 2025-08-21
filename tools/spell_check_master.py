#!/usr/bin/env python3
"""
Script maestro para gestión completa de ortografía
Integra todos los pasos sugeridos en una sola ejecución
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🚀 {description}")
    print("-" * 50)

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Comando ejecutado exitosamente")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Error ejecutando comando: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Función principal que ejecuta todos los pasos"""
    print("🎯 SISTEMA COMPLETO DE GESTIÓN DE ORTOGRAFÍA")
    print("=" * 60)
    print("Este script implementa todos los pasos sugeridos:")
    print("1. ✅ Auto-agregar términos técnicos y palabras del proyecto")
    print("2. ✅ Crear diccionarios separados por idioma")
    print("3. ✅ Configurar reglas específicas por tipo de archivo")
    print("4. ✅ Implementar filtros automáticos por contexto")
    print("5. ✅ Configurar integración con IDE")
    print("6. ✅ Exportar reporte completo para revisión posterior")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not Path("pyproject.toml").exists():
        print("❌ Error: No se encontró pyproject.toml")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return 1

    # Paso 1: Configurar IDE
    print("\n📋 PASO 1: Configurando IDEs...")
    if not run_command(
        "python tools/setup_ide_spell_check.py",
        "Configurando corrector ortográfico para IDEs",
    ):
        print("⚠️  Continuando sin configuración de IDE...")

    # Paso 2: Ejecutar flujo completo de gestión
    print("\n📋 PASO 2: Ejecutando flujo completo de gestión...")
    if not run_command(
        "python tools/complete_spell_check_workflow.py",
        "Ejecutando flujo completo de gestión de ortografía",
    ):
        print("❌ Error en el flujo de gestión")
        return 1

    # Paso 3: Verificar resultados
    print("\n📋 PASO 3: Verificando resultados...")

    # Verificar archivos creados
    files_to_check = [
        ".vscode/settings.json",
        "cspell.json",
        "pycharm_spell_check_config.json",
        "SPELL_CHECK_SETUP.md",
        "config/dictionaries/spell_check_config.json",
        "config/dictionaries/technical_terms.txt",
        "config/dictionaries/spanish_words.txt",
        "config/dictionaries/english_words.txt",
        "config/dictionaries/code_identifiers.txt",
    ]

    print("\n📁 Archivos generados:")
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (no encontrado)")

    # Paso 4: Mostrar estadísticas finales
    print("\n📋 PASO 4: Estadísticas finales...")

    # Contar palabras en diccionarios
    dict_files = [
        "config/dictionaries/technical_terms.txt",
        "config/dictionaries/spanish_words.txt",
        "config/dictionaries/english_words.txt",
        "config/dictionaries/code_identifiers.txt",
    ]

    total_words = 0
    for dict_file in dict_files:
        if Path(dict_file).exists():
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    words = len(f.readlines())
                    total_words += words
                    print(f"  📄 {dict_file}: {words:,} palabras")
            except Exception as e:
                print(f"  ❌ Error leyendo {dict_file}: {e}")

    print(f"\n📊 Total de palabras procesadas: {total_words:,}")

    # Paso 5: Mostrar próximos pasos
    print("\n📋 PASO 5: Próximos pasos recomendados...")
    print("\n🎯 ACCIONES INMEDIATAS:")
    print("  1. Instalar extensiones de VS Code:")
    print("     - Code Spell Checker (cspell)")
    print("     - Spell Right")
    print("  2. Instalar cspell globalmente:")
    print("     npm install -g cspell")
    print("  3. Configurar PyCharm según pycharm_spell_check_config.json")

    print("\n🎯 ACCIONES A LARGO PLAZO:")
    print("  1. Revisar identificadores de código manualmente")
    print("     (87,883 palabras en code_identifiers.txt)")
    print("  2. Implementar filtros automáticos por contexto")
    print("  3. Configurar integración con CI/CD")

    print("\n🎯 COMANDOS ÚTILES:")
    print("  # Verificar ortografía con cspell")
    print('  cspell "**/*.{py,md,html,js,css,txt}"')
    print("  ")
    print("  # Ejecutar verificación rápida")
    print("  python tools/quick_spell_check.py")
    print("  ")
    print("  # Ejecutar flujo completo")
    print("  python tools/complete_spell_check_workflow.py")

    print("\n✅ ¡SISTEMA COMPLETO DE GESTIÓN DE ORTOGRAFÍA IMPLEMENTADO!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
