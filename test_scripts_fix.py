#!/usr/bin/env python3
"""
Script de prueba para verificar que la corrección de scripts funciona correctamente
"""

import requests
import json
import sys
import os

def test_scripts_api():
    """Prueba la API de scripts para verificar que detecta los scripts correctamente"""
    
    print("🧪 Iniciando prueba de la API de scripts...")
    
    # URL base de la aplicación (ajustar según sea necesario)
    base_url = "http://localhost:5000"
    
    try:
        # Probar la API de metadatos de scripts
        print(f"📡 Probando: {base_url}/admin/tools/api/scripts_metadata")
        
        response = requests.get(f"{base_url}/admin/tools/api/scripts_metadata")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API respondió correctamente")
            print(f"📊 Categorías encontradas: {len(data)}")
            
            total_scripts = 0
            for categoria in data:
                scripts_count = len(categoria['scripts'])
                total_scripts += scripts_count
                print(f"   📁 {categoria['categoria']}: {scripts_count} scripts")
                
                # Mostrar algunos ejemplos de scripts
                if scripts_count > 0:
                    for i, script in enumerate(categoria['scripts'][:3]):  # Primeros 3
                        print(f"      📄 {script['nombre']}: {script['descripcion'][:50]}...")
                    if scripts_count > 3:
                        print(f"      ... y {scripts_count - 3} más")
            
            print(f"🎯 Total de scripts detectados: {total_scripts}")
            
            if total_scripts == 0:
                print("❌ ERROR: No se detectaron scripts. Revisar la configuración.")
                return False
            else:
                print("✅ Scripts detectados correctamente")
                return True
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("💡 Asegúrate de que la aplicación Flask esté ejecutándose en http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_local_directory():
    """Prueba local para verificar que los directorios y scripts existen"""
    
    print("\n🔍 Verificando estructura local de directorios...")
    
    # Directorio base
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(base_dir, 'tools')
    
    print(f"📁 Directorio base: {base_dir}")
    print(f"📁 Directorio tools: {tools_dir}")
    
    if not os.path.exists(tools_dir):
        print("❌ ERROR: El directorio tools/ no existe")
        return False
    
    print("✅ Directorio tools/ existe")
    
    # Verificar scripts en directorio raíz
    scripts_root = []
    for file in os.listdir(tools_dir):
        if file.endswith('.py') or file.endswith('.sh'):
            if os.path.isfile(os.path.join(tools_dir, file)):
                scripts_root.append(file)
    
    print(f"📄 Scripts en tools/ (raíz): {len(scripts_root)}")
    if len(scripts_root) > 0:
        for script in scripts_root[:5]:  # Primeros 5
            print(f"   - {script}")
        if len(scripts_root) > 5:
            print(f"   ... y {len(scripts_root) - 5} más")
    
    # Verificar subdirectorios
    subdirs = ['admin_utils', 'db_utils', 'diagnostico', 'maintenance']
    total_subdir_scripts = 0
    
    for subdir in subdirs:
        subdir_path = os.path.join(tools_dir, subdir)
        if os.path.exists(subdir_path):
            scripts_in_subdir = []
            for file in os.listdir(subdir_path):
                if file.endswith('.py') or file.endswith('.sh'):
                    if os.path.isfile(os.path.join(subdir_path, file)):
                        scripts_in_subdir.append(file)
            
            print(f"📁 {subdir}/: {len(scripts_in_subdir)} scripts")
            total_subdir_scripts += len(scripts_in_subdir)
        else:
            print(f"❌ {subdir}/: directorio no existe")
    
    total_local_scripts = len(scripts_root) + total_subdir_scripts
    print(f"🎯 Total de scripts locales: {total_local_scripts}")
    
    return total_local_scripts > 0

def main():
    """Función principal"""
    print("🚀 Iniciando verificación de corrección de scripts")
    print("=" * 60)
    
    # Prueba local
    local_ok = test_local_directory()
    
    # Prueba de API (solo si hay scripts locales)
    if local_ok:
        api_ok = test_scripts_api()
        
        if api_ok:
            print("\n✅ ÉXITO: La corrección de scripts funciona correctamente")
            print("💡 Ahora puedes acceder a 'Script y Herramientas' en la aplicación")
        else:
            print("\n⚠️  ADVERTENCIA: Scripts detectados localmente pero la API no responde")
            print("💡 Verifica que la aplicación esté ejecutándose")
    else:
        print("\n❌ ERROR: No se encontraron scripts en el sistema")
        print("💡 Verifica la estructura de directorios")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
