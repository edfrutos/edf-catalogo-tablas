#!/usr/bin/env python3
"""
Script rápido para verificar palabras desconocidas en archivos específicos
Uso: python tools/quick_spell_check.py [archivo_o_directorio]
"""

import sys
import re
from pathlib import Path
from typing import Set
import toml

def load_known_words() -> Set[str]:
    """Cargar palabras conocidas desde pyproject.toml"""
    try:
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            config = toml.load(f)
        words = config.get('tool', {}).get('cspell', {}).get('words', [])
        return set(words)
    except Exception as e:
        print(f"❌ Error al cargar pyproject.toml: {e}")
        return set()

def extract_words(text: str) -> Set[str]:
    """Extraer palabras únicas de un texto"""
    word_pattern = r'\b[a-zA-ZÀ-ÿ\u00C0-\u017F][a-zA-ZÀ-ÿ\u00C0-\u017F0-9_-]*\b'
    words = re.findall(word_pattern, text)
    return {word for word in words if 3 <= len(word) <= 30}

def check_file(file_path: Path, known_words: Set[str]) -> Set[str]:
    """Verificar palabras desconocidas en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        words = extract_words(content)
        unknown = words - known_words
        
        # Filtrar palabras comunes
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero',
            'en', 'con', 'por', 'para', 'de', 'del', 'al', 'se', 'que', 'como',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be',
            'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'tener', 'tiene', 'tenido', 'hacer', 'hace', 'hecho', 'puede', 'debe'
        }
        
        return unknown - common_words
    except Exception as e:
        print(f"⚠️ Error al leer {file_path}: {e}")
        return set()

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    target_path = Path(target)
    
    print(f"🔍 Verificando palabras desconocidas en: {target_path}")
    
    known_words = load_known_words()
    print(f"✅ Cargadas {len(known_words)} palabras conocidas")
    
    unknown_words = set()
    
    if target_path.is_file():
        # Verificar un archivo específico
        unknown = check_file(target_path, known_words)
        if unknown:
            print(f"\n📝 Palabras desconocidas en {target_path.name}:")
            for word in sorted(unknown):
                print(f"   • {word}")
        else:
            print("✅ No se encontraron palabras desconocidas")
    else:
        # Verificar directorio
        extensions = ['.py', '.md', '.html', '.js', '.css', '.txt']
        for file_path in target_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                if any(part in ['venv', '__pycache__', 'node_modules', '.git'] for part in file_path.parts):
                    continue
                    
                unknown = check_file(file_path, known_words)
                if unknown:
                    print(f"\n📝 {file_path.name}:")
                    for word in sorted(unknown):
                        print(f"   • {word}")
                    unknown_words.update(unknown)
        
        if not unknown_words:
            print("✅ No se encontraron palabras desconocidas")
        else:
            print(f"\n📊 Total de palabras desconocidas únicas: {len(unknown_words)}")

if __name__ == "__main__":
    main() 