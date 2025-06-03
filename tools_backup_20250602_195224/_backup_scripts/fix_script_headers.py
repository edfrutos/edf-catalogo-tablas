#!/usr/bin/env python3
# Script para verificar y corregir las líneas shebang en los scripts
# Creado: 17/05/2025

import os
import sys
import glob
import re

def print_header(message):
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80)

def fix_shebang(file_path):
    """Verifica y corrige la línea shebang en un script"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Verificar si el archivo ya tiene una línea shebang
        has_shebang = content.startswith('#!')
        
        # Determinar el tipo de script por su extensión
        _, ext = os.path.splitext(file_path)
        
        if ext == '.py':
            correct_shebang = '#!/usr/bin/env python3'
        elif ext == '.sh':
            correct_shebang = '#!/bin/bash'
        else:
            return False, "Tipo de archivo no soportado"
        
        # Si no tiene shebang o es incorrecto, corregirlo
        if not has_shebang:
            with open(file_path, 'w') as f:
                f.write(f"{correct_shebang}\n{content}")
            return True, "Añadida línea shebang"
        elif not content.startswith(correct_shebang):
            # Reemplazar la primera línea con el shebang correcto
            lines = content.split('\n')
            lines[0] = correct_shebang
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            return True, "Corregida línea shebang"
        
        return False, "Ya tiene la línea shebang correcta"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Definir el directorio raíz
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(root_dir, "scripts")
    tools_dir = os.path.join(root_dir, "tools")
    
    print_header("VERIFICACIÓN Y CORRECCIÓN DE LÍNEAS SHEBANG")
    print(f"Fecha y hora: {os.popen('date').read().strip()}")
    print(f"Directorio raíz: {root_dir}")
    
    # Verificar y corregir scripts en el directorio scripts/
    print_header("SCRIPTS EN DIRECTORIO SCRIPTS/")
    scripts_py = glob.glob(os.path.join(scripts_dir, "**", "*.py"), recursive=True)
    scripts_sh = glob.glob(os.path.join(scripts_dir, "**", "*.sh"), recursive=True)
    
    total_fixed = 0
    total_checked = 0
    
    for script in scripts_py + scripts_sh:
        total_checked += 1
        fixed, message = fix_shebang(script)
        if fixed:
            total_fixed += 1
            print(f"Corregido: {script} - {message}")
    
    print(f"Total de scripts verificados: {total_checked}")
    print(f"Scripts corregidos: {total_fixed}")
    
    # Verificar y corregir scripts en el directorio tools/
    print_header("SCRIPTS EN DIRECTORIO TOOLS/")
    tools_py = glob.glob(os.path.join(tools_dir, "**", "*.py"), recursive=True)
    tools_sh = glob.glob(os.path.join(tools_dir, "**", "*.sh"), recursive=True)
    
    total_fixed = 0
    total_checked = 0
    
    for script in tools_py + tools_sh:
        total_checked += 1
        fixed, message = fix_shebang(script)
        if fixed:
            total_fixed += 1
            print(f"Corregido: {script} - {message}")
    
    print(f"Total de scripts verificados: {total_checked}")
    print(f"Scripts corregidos: {total_fixed}")
    
    print_header("RECOMENDACIONES")
    print("1. Asegúrese de que todos los scripts tengan la línea shebang correcta:")
    print("   - Scripts Python: #!/usr/bin/env python3")
    print("   - Scripts Bash: #!/bin/bash")
    print("2. Reinicie el servidor Gunicorn después de realizar cambios importantes")
    print("3. Verifique los logs de errores si persisten problemas de ejecución")

if __name__ == "__main__":
    main()
