#!/usr/bin/env python3
# Descripción: Corrige automáticamente los puertos incorrectos en todos los scripts

import os
import re
import glob

def fix_port_configuration():
    """Corrige automáticamente los puertos incorrectos en los scripts"""
    
    print("🔧 CORRIGIENDO CONFIGURACIÓN DE PUERTOS")
    print("=" * 50)
    
    # Configuración
    wrong_port = "5001"
    correct_port = "8000"
    tools_dir = "tools"
    
    # Contadores
    files_checked = 0
    files_modified = 0
    total_replacements = 0
    
    print(f"🔍 Buscando archivos con puerto {wrong_port}...")
    
    # Buscar todos los archivos Python en tools
    python_files = glob.glob(f"{tools_dir}/**/*.py", recursive=True)
    
    for file_path in python_files:
        files_checked += 1
        file_modified = False
        
        try:
            # Leer archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar ocurrencias del puerto incorrecto
            pattern = f"localhost:{wrong_port}"
            matches = re.findall(pattern, content)
            
            if matches:
                print(f"   📄 {file_path}: {len(matches)} ocurrencias encontradas")
                
                # Reemplazar puerto incorrecto
                new_content = content.replace(f"localhost:{wrong_port}", f"localhost:{correct_port}")
                
                # Escribir archivo modificado
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                files_modified += 1
                total_replacements += len(matches)
                file_modified = True
                
                print(f"      ✅ Corregidas {len(matches)} ocurrencias")
        
        except Exception as e:
            print(f"   ❌ Error procesando {file_path}: {e}")
    
    print(f"\n📊 RESUMEN DE CORRECCIONES:")
    print(f"   📁 Archivos revisados: {files_checked}")
    print(f"   🔧 Archivos modificados: {files_modified}")
    print(f"   🔄 Total de reemplazos: {total_replacements}")
    
    if total_replacements > 0:
        print(f"\n✅ CORRECCIÓN COMPLETADA")
        print(f"   🎯 Puerto {wrong_port} → {correct_port}")
        print(f"   📂 Directorio: {tools_dir}")
    else:
        print(f"\nℹ️  No se encontraron archivos con puerto {wrong_port}")
    
    return files_modified, total_replacements

def verify_corrections():
    """Verifica que las correcciones se aplicaron correctamente"""
    
    print(f"\n🔍 VERIFICANDO CORRECCIONES")
    print("=" * 30)
    
    tools_dir = "tools"
    wrong_port = "5001"
    correct_port = "8000"
    
    # Verificar que no queden puertos incorrectos
    remaining_wrong = glob.glob(f"{tools_dir}/**/*.py", recursive=True)
    remaining_wrong = [f for f in remaining_wrong if wrong_port in open(f, 'r').read()]
    
    if remaining_wrong:
        print(f"   ⚠️  Archivos que aún contienen puerto {wrong_port}:")
        for f in remaining_wrong:
            print(f"      • {f}")
    else:
        print(f"   ✅ No quedan archivos con puerto {wrong_port}")
    
    # Verificar puertos correctos
    correct_files = glob.glob(f"{tools_dir}/**/*.py", recursive=True)
    correct_files = [f for f in correct_files if f"localhost:{correct_port}" in open(f, 'r').read()]
    
    print(f"   📊 Archivos con puerto {correct_port}: {len(correct_files)}")

if __name__ == "__main__":
    # Ejecutar corrección
    files_modified, total_replacements = fix_port_configuration()
    
    # Verificar correcciones
    verify_corrections()
    
    print(f"\n🎉 PROCESO COMPLETADO")
    if total_replacements > 0:
        print(f"   💡 Reinicia Gunicorn para aplicar cambios en scripts de producción")
