#!/usr/bin/env python3
import os
import re

def fix_python38_compatibility():
    """Corrige sintaxis incompatible con Python 3.8"""
    
    # Buscar todos los archivos .py en el directorio app/
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                fix_file(filepath)

def fix_file(filepath):
    """Corrige un archivo específico"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Agregar imports necesarios si no existen
        if 'from typing import' not in content and ('Dict[' in content or 'List[' in content or 'Union[' in content):
            # Buscar línea de imports existentes
            lines = content.split('\n')
            import_line_idx = -1
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_line_idx = i
            
            if import_line_idx >= 0:
                lines.insert(import_line_idx + 1, 'from typing import Dict, List, Union, Optional')
            else:
                lines.insert(0, 'from typing import Dict, List, Union, Optional')
            
            content = '\n'.join(lines)
        
        # Corregir sintaxis de Union types (| -> Union[])
        content = re.sub(r'(\w+)\s*\|\s*(\w+)', r'Union[\1, \2]', content)
        content = re.sub(r'Union\[([^\]]+)\]\s*\|\s*(\w+)', r'Union[\1, \2]', content)
        
        # Corregir dict[] -> Dict[]
        content = re.sub(r'\bdict\[([^\]]+)\]', r'Dict[\1]', content)
        
        # Corregir list[] -> List[]
        content = re.sub(r'\blist\[([^\]]+)\]', r'List[\1]', content)
        
        # Guardar solo si hubo cambios
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Corregido: {filepath}")
        else:
            print(f"⏭️  Sin cambios: {filepath}")
            
    except Exception as e:
        print(f"❌ Error procesando {filepath}: {e}")

if __name__ == '__main__':
    print("🔧 Corrigiendo compatibilidad con Python 3.8...")
    fix_python38_compatibility()
    print("✅ Proceso completado")