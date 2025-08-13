#!/usr/bin/env python3
"""
Script para diagnosticar y corregir problemas de ejecución de scripts en producción
"""

import os
import sys
import subprocess
import json
import traceback
from pathlib import Path

def check_script_runner():
    """Verifica el estado del script_runner.py"""
    print("=== VERIFICACIÓN DE SCRIPT_RUNNER.PY ===")
    
    script_runner_path = os.path.join(os.getcwd(), "tools", "script_runner.py")
    
    if not os.path.exists(script_runner_path):
        print(f"❌ script_runner.py no encontrado en: {script_runner_path}")
        return False
    
    print(f"✅ script_runner.py encontrado en: {script_runner_path}")
    
    # Verificar permisos
    is_executable = os.access(script_runner_path, os.X_OK)
    print(f"  Permisos de ejecución: {'✅' if is_executable else '❌'}")
    
    if not is_executable:
        try:
            os.chmod(script_runner_path, 0o755)
            print("  ✅ Permisos corregidos")
        except Exception as e:
            print(f"  ❌ Error al corregir permisos: {e}")
            return False
    
    # Probar ejecución
    try:
        result = subprocess.run(
            [sys.executable, script_runner_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 1 and "Debe especificar la ruta del script" in result.stdout:
            print("  ✅ script_runner.py se ejecuta correctamente")
            return True
        else:
            print(f"  ⚠️ script_runner.py se ejecuta pero con salida inesperada")
            print(f"    stdout: {result.stdout}")
            print(f"    stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error al ejecutar script_runner.py: {str(e)}")
        return False

def test_script_execution():
    """Prueba la ejecución de un script específico"""
    print("\n=== PRUEBA DE EJECUCIÓN DE SCRIPT ===")
    
    # Script a probar
    script_path = "tools/production/db_utils/test_date_format.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Script no encontrado: {script_path}")
        return False
    
    print(f"✅ Script encontrado: {script_path}")
    
    # Verificar permisos
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)
            print("✅ Permisos corregidos")
        except Exception as e:
            print(f"❌ Error al corregir permisos: {e}")
            return False
    
    # Probar ejecución directa
    print("\n--- Ejecución directa ---")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        print(f"Código de salida: {result.returncode}")
        print(f"Salida estándar:\n{result.stdout}")
        if result.stderr:
            print(f"Error estándar:\n{result.stderr}")
        
        if result.returncode == 0:
            print("✅ Ejecución directa exitosa")
        else:
            print("❌ Ejecución directa falló")
            
    except Exception as e:
        print(f"❌ Error en ejecución directa: {e}")
        return False
    
    # Probar ejecución con script_runner
    print("\n--- Ejecución con script_runner ---")
    script_runner_path = os.path.join(os.getcwd(), "tools", "script_runner.py")
    
    try:
        result = subprocess.run(
            [sys.executable, script_runner_path, script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        print(f"Código de salida: {result.returncode}")
        
        # Intentar parsear JSON
        try:
            json_result = json.loads(result.stdout)
            print("✅ script_runner devolvió JSON válido")
            print(f"Resultado: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"❌ script_runner no devolvió JSON válido: {e}")
            print(f"Salida recibida:\n{result.stdout}")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error en ejecución con script_runner: {e}")
        return False
    
    return True

def check_web_routes():
    """Verifica las rutas web para ejecución de scripts"""
    print("\n=== VERIFICACIÓN DE RUTAS WEB ===")
    
    # Verificar archivo de rutas
    routes_file = "app/routes/scripts_routes.py"
    if not os.path.exists(routes_file):
        print(f"❌ Archivo de rutas no encontrado: {routes_file}")
        return False
    
    print(f"✅ Archivo de rutas encontrado: {routes_file}")
    
    # Verificar que las rutas estén correctamente configuradas
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if '/run/<path:script_path>' in content:
        print("✅ Ruta /run/ encontrada")
    else:
        print("❌ Ruta /run/ no encontrada")
        return False
    
    if '/execute' in content:
        print("✅ Ruta /execute encontrada")
    else:
        print("❌ Ruta /execute no encontrada")
        return False
    
    return True

def fix_script_execution_issues():
    """Corrige los problemas de ejecución de scripts"""
    print("\n=== CORRECCIÓN DE PROBLEMAS ===")
    
    # 1. Corregir permisos de script_runner
    script_runner_path = os.path.join(os.getcwd(), "tools", "script_runner.py")
    if os.path.exists(script_runner_path):
        try:
            os.chmod(script_runner_path, 0o755)
            print("✅ Permisos de script_runner corregidos")
        except Exception as e:
            print(f"❌ Error al corregir permisos de script_runner: {e}")
    
    # 2. Corregir permisos de scripts de producción
    production_scripts_dir = os.path.join(os.getcwd(), "tools", "production", "db_utils")
    if os.path.exists(production_scripts_dir):
        for file in os.listdir(production_scripts_dir):
            if file.endswith('.py'):
                script_path = os.path.join(production_scripts_dir, file)
                try:
                    os.chmod(script_path, 0o755)
                    print(f"✅ Permisos corregidos para: {file}")
                except Exception as e:
                    print(f"❌ Error al corregir permisos de {file}: {e}")
    
    # 3. Verificar que el script_runner devuelva JSON válido
    print("\n--- Verificando salida JSON del script_runner ---")
    script_runner_path = os.path.join(os.getcwd(), "tools", "script_runner.py")
    test_script = os.path.join(os.getcwd(), "tools", "production", "db_utils", "test_date_format.py")
    
    if os.path.exists(script_runner_path) and os.path.exists(test_script):
        try:
            result = subprocess.run(
                [sys.executable, script_runner_path, test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                try:
                    json.loads(result.stdout)
                    print("✅ script_runner devuelve JSON válido")
                except json.JSONDecodeError:
                    print("❌ script_runner no devuelve JSON válido")
                    print(f"Salida actual:\n{result.stdout}")
            else:
                print(f"❌ script_runner falló con código {result.returncode}")
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error al probar script_runner: {e}")

def main():
    """Función principal"""
    print("🔧 DIAGNÓSTICO Y CORRECCIÓN DE SCRIPTS EN PRODUCCIÓN")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("tools"):
        print("❌ No se encontró el directorio 'tools'. Asegúrate de ejecutar desde el directorio raíz del proyecto.")
        return
    
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Realizar verificaciones
    script_runner_ok = check_script_runner()
    execution_ok = test_script_execution()
    routes_ok = check_web_routes()
    
    # Aplicar correcciones si es necesario
    if not script_runner_ok or not execution_ok:
        fix_script_execution_issues()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    print(f"Script Runner: {'✅ OK' if script_runner_ok else '❌ PROBLEMA'}")
    print(f"Ejecución de Scripts: {'✅ OK' if execution_ok else '❌ PROBLEMA'}")
    print(f"Rutas Web: {'✅ OK' if routes_ok else '❌ PROBLEMA'}")
    
    if script_runner_ok and execution_ok and routes_ok:
        print("\n🎉 Todos los sistemas funcionando correctamente")
    else:
        print("\n⚠️ Se detectaron problemas. Revisa los mensajes anteriores.")
        print("💡 Recomendaciones:")
        print("   1. Verifica que todos los scripts tengan permisos de ejecución (755)")
        print("   2. Asegúrate de que script_runner.py devuelva JSON válido")
        print("   3. Verifica que las rutas web estén correctamente configuradas")
        print("   4. Revisa los logs del servidor web para errores adicionales")

if __name__ == "__main__":
    main()
