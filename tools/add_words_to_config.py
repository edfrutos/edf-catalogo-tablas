#!/usr/bin/env python3
"""
Script para añadir palabras específicas a la configuración de cSpell
Uso: python tools/add_words_to_config.py palabra1 palabra2 palabra3
"""

import sys
import toml
from typing import List

def add_words_to_config(words: List[str]) -> None:
    """Añadir palabras a la configuración de pyproject.toml"""
    try:
        # Cargar configuración actual
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        # Obtener configuración actual de cSpell
        if 'tool' not in config:
            config['tool'] = {}
        if 'cspell' not in config['tool']:
            config['tool']['cspell'] = {}
        if 'words' not in config['tool']['cspell']:
            config['tool']['cspell']['words'] = []
        
        # Obtener palabras actuales
        current_words = set(config['tool']['cspell']['words'])
        
        # Añadir nuevas palabras
        new_words = []
        for word in words:
            if word not in current_words:
                new_words.append(word)
                current_words.add(word)
        
        if new_words:
            config['tool']['cspell']['words'].extend(sorted(new_words))
            
            # Guardar configuración actualizada
            with open('pyproject.toml', 'w', encoding='utf-8') as f:
                toml.dump(config, f)
            
            print(f"✅ Añadidas {len(new_words)} palabras nuevas a pyproject.toml:")
            for word in sorted(new_words):
                print(f"   + {word}")
        else:
            print("✅ Todas las palabras ya están en la configuración")
            
    except Exception as e:
        print(f"❌ Error al actualizar pyproject.toml: {e}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python tools/add_words_to_config.py palabra1 palabra2 palabra3")
        print("Ejemplo: python tools/add_words_to_config.py Flask MongoDB Python")
        return
    
    words = sys.argv[1:]
    print(f"🔧 Añadiendo {len(words)} palabras a la configuración...")
    add_words_to_config(words)

if __name__ == "__main__":
    main() 