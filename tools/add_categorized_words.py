#!/usr/bin/env python3
"""
Script para agregar palabras desconocidas identificadas por categorías
a sus diccionarios correspondientes
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import toml


def load_categorized_words_from_json(json_file):
    """Cargar palabras categorizadas desde archivo JSON"""
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        # Extraer categorías del JSON
        categories = {}
        if "categories" in data:
            categories = data["categories"]
        elif "categorization" in data:
            categories = data["categorization"]

        return categories
    except Exception as e:
        print(f"❌ Error cargando {json_file}: {e}")
        return {}


def add_words_to_pyproject_toml(categories):
    """Agregar palabras categorizadas a pyproject.toml"""
    try:
        # Leer configuración actual
        with open("pyproject.toml", encoding="utf-8") as f:
            config = toml.load(f)

        # Obtener palabras existentes
        existing_words = set(config.get("tool", {}).get("cspell", {}).get("words", []))

        # Recopilar todas las palabras de todas las categorías
        all_new_words = []
        for _category, words in categories.items():
            if isinstance(words, list):
                all_new_words.extend(words)
            elif isinstance(words, dict) and "words" in words:
                all_new_words.extend(words["words"])

        # Agregar nuevas palabras
        updated_words = list(existing_words | set(all_new_words))
        updated_words.sort()

        # Actualizar configuración
        if "tool" not in config:
            config["tool"] = {}
        if "cspell" not in config["tool"]:
            config["tool"]["cspell"] = {}

        config["tool"]["cspell"]["words"] = updated_words

        # Crear backup
        backup_file = (
            f"pyproject.toml.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        _ = shutil.copy("pyproject.toml", backup_file)

        # Escribir configuración actualizada
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            _ = toml.dump(config, f)

        print(
            f"✅ pyproject.toml actualizado con {len(all_new_words)} palabras categorizadas"
        )
        print(f"📄 Backup creado: {backup_file}")

        return True

    except Exception as e:
        print(f"❌ Error actualizando pyproject.toml: {e}")
        return False


def create_categorized_dictionaries(categories):
    """Crear diccionarios separados por categoría"""
    dict_dir = Path("config/dictionaries")
    dict_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    for category, words in categories.items():
        if isinstance(words, list):
            word_list = words
        elif isinstance(words, dict) and "words" in words:
            word_list = words["words"]
        else:
            continue

        if not word_list:
            continue

        # Crear nombre de archivo para la categoría
        filename = f"{category.lower()}_words.txt"
        filepath = dict_dir / filename

        # Escribir palabras al archivo
        with open(filepath, "w", encoding="utf-8") as f:
            for word in sorted(word_list):
                _ = f.write(f"{word}\n")

        created_files.append((filename, len(word_list)))
        print(f"✅ Diccionario creado: {filename} ({len(word_list)} palabras)")

    return created_files


def update_vscode_settings(categories):
    """Actualizar configuración de VS Code con palabras categorizadas"""
    try:
        vscode_file = Path(".vscode/settings.json")
        if not vscode_file.exists():
            print("❌ Archivo .vscode/settings.json no encontrado")
            return False

        with open(vscode_file, encoding="utf-8") as f:
            settings = json.load(f)

        # Recopilar todas las palabras
        all_new_words = []
        for _category, words in categories.items():
            if isinstance(words, list):
                all_new_words.extend(words)
            elif isinstance(words, dict) and "words" in words:
                all_new_words.extend(words["words"])

        # Actualizar palabras en VS Code
        existing_words = set(settings.get("spellright.words", []))
        updated_words = list(existing_words | set(all_new_words))
        updated_words.sort()

        settings["spellright.words"] = updated_words

        # Crear backup
        backup_file = (
            f".vscode/settings.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        _ = shutil.copy(vscode_file, backup_file)

        # Escribir configuración actualizada
        with open(vscode_file, "w", encoding="utf-8") as f:
            _ = json.dump(settings, f, indent=2, ensure_ascii=False)

        print(
            f"✅ VS Code settings actualizado con {len(all_new_words)} palabras categorizadas"
        )
        print(f"📄 Backup creado: {backup_file}")

        return True

    except Exception as e:
        print(f"❌ Error actualizando VS Code settings: {e}")
        return False


def update_cspell_config(categories):
    """Actualizar configuración de cspell con palabras categorizadas"""
    try:
        cspell_file = Path("cspell.json")
        if not cspell_file.exists():
            print("❌ Archivo cspell.json no encontrado")
            return False

        with open(cspell_file, encoding="utf-8") as f:
            config = json.load(f)

        # Recopilar todas las palabras
        all_new_words = []
        for _category, words in categories.items():
            if isinstance(words, list):
                all_new_words.extend(words)
            elif isinstance(words, dict) and "words" in words:
                all_new_words.extend(words["words"])

        # Actualizar palabras en cspell
        existing_words = set(config.get("words", []))
        updated_words = list(existing_words | set(all_new_words))
        updated_words.sort()

        config["words"] = updated_words

        # Crear backup
        backup_file = f"cspell.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _ = shutil.copy(cspell_file, backup_file)

        # Escribir configuración actualizada
        with open(cspell_file, "w", encoding="utf-8") as f:
            _ = json.dump(config, f, indent=2, ensure_ascii=False)

        print(
            f"✅ cspell.json actualizado con {len(all_new_words)} palabras categorizadas"
        )
        print(f"📄 Backup creado: {backup_file}")

        return True

    except Exception as e:
        print(f"❌ Error actualizando cspell.json: {e}")
        return False


def find_latest_spell_check_results():
    """Encontrar el archivo JSON más reciente de resultados de spell check"""
    json_files = list(Path(".").glob("spell_check_results_*.json"))
    if not json_files:
        return None

    # Ordenar por fecha de modificación (más reciente primero)
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return json_files[0]


def main():
    """Función principal"""
    print("📚 AGREGANDO PALABRAS CATEGORIZADAS A DICCIONARIOS")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not Path("pyproject.toml").exists():
        print("❌ Error: No se encontró pyproject.toml")
        print("   Ejecuta este script desde el directorio raíz del proyecto")
        return 1

    # Buscar archivo JSON de resultados
    json_file = find_latest_spell_check_results()
    if not json_file:
        print("❌ No se encontró archivo de resultados de spell check")
        print("   Ejecuta primero: python tools/quick_spell_check.py README.md")
        print("   Y selecciona la opción 4 para exportar resultados")
        return 1

    print(f"📄 Archivo encontrado: {json_file.name}")

    # Cargar palabras categorizadas
    categories = load_categorized_words_from_json(json_file)
    if not categories:
        print("❌ No se pudieron cargar categorías del archivo JSON")
        return 1

    # Mostrar categorías encontradas
    print("\n📊 Categorías encontradas:")
    total_words = 0
    for category, words in categories.items():
        if isinstance(words, list):
            count = len(words)
        elif isinstance(words, dict) and "words" in words:
            count = len(words["words"])
        else:
            count = 0

        print(f"  📝 {category}: {count} palabras")
        total_words += count

    print(f"\n📋 Total de palabras a agregar: {total_words}")

    if total_words == 0:
        print("❌ No hay palabras para agregar")
        return 0

    # Confirmar acción
    response = (
        input(
            f"\n🤔 ¿Agregar {total_words} palabras categorizadas a los diccionarios? (s/n): "
        )
        .strip()
        .lower()
    )
    if response not in ["s", "si", "sí", "y", "yes"]:
        print("❌ Operación cancelada")
        return 0

    try:
        # Paso 1: Crear diccionarios separados por categoría
        print("\n📋 PASO 1: Creando diccionarios por categoría...")
        created_files = create_categorized_dictionaries(categories)

        # Paso 2: Actualizar pyproject.toml
        print("\n📋 PASO 2: Actualizando pyproject.toml...")
        _ = add_words_to_pyproject_toml(categories)

        # Paso 3: Actualizar VS Code settings
        print("\n📋 PASO 3: Actualizando VS Code settings...")
        _ = update_vscode_settings(categories)

        # Paso 4: Actualizar cspell.json
        print("\n📋 PASO 4: Actualizando cspell.json...")
        _ = update_cspell_config(categories)

        # Resumen final
        print("\n🎉 ¡PALABRAS CATEGORIZADAS AGREGADAS EXITOSAMENTE!")
        print("\n📊 RESUMEN:")
        print(f"  📁 Diccionarios creados: {len(created_files)}")
        for filename, count in created_files:
            print(f"    📄 {filename}: {count} palabras")
        print(f"  📝 Total de palabras agregadas: {total_words}")

        print("\n📋 Próximos pasos:")
        print("  1. Reiniciar VS Code para aplicar cambios")
        print("  2. Probar: python tools/quick_spell_check.py README.md")
        print("  3. Verificar que las palabras ya no aparecen como desconocidas")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
