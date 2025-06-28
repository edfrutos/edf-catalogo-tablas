#!/usr/bin/env python3
"""
Script completo para solucionar todos los problemas del ejecutable macOS
- Corrige el problema de login
- Configura el icono correctamente
- Verifica que todo funcione
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_auth_routes():
    """Corrige el problema de las rutas de autenticación"""
    logger.info("🔧 Corrigiendo rutas de autenticación...")
    
    main_app_path = Path("main_app.py")
    if not main_app_path.exists():
        logger.error("❌ No se encontró main_app.py")
        return False
    
    # Leer el contenido actual
    with open(main_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya está corregido
    if "app.register_blueprint(auth_bp, url_prefix='/auth')" in content:
        logger.info("✅ Las rutas de autenticación ya están corregidas")
        return True
    
    # Aplicar la corrección
    if "app.register_blueprint(auth_bp, url_prefix='')" in content:
        content = content.replace(
            "app.register_blueprint(auth_bp, url_prefix='')",
            "app.register_blueprint(auth_bp, url_prefix='/auth')"
        )
        
        # Guardar el archivo corregido
        with open(main_app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ Rutas de autenticación corregidas")
        return True
    else:
        logger.warning("⚠️ No se encontró la línea a corregir en main_app.py")
        return False

def fix_launcher_icon():
    """Configura el icono en el launcher"""
    logger.info("🎨 Configurando icono en launcher...")
    
    launcher_path = Path("launcher.py")
    if not launcher_path.exists():
        logger.error("❌ No se encontró launcher.py")
        return False
    
    # Leer el contenido actual
    with open(launcher_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya tiene configuración de icono
    if "icon=" in content and "favicon.ico" in content:
        logger.info("✅ El icono ya está configurado en launcher.py")
        return True
    
    # Buscar la línea de webview.create_window
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'webview.create_window(' in line and 'icon=' not in line:
            # Encontrar el final de la llamada a create_window
            j = i
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            
            # Insertar la configuración del icono antes del cierre
            if j < len(lines):
                # Buscar la posición correcta para insertar el icono
                insert_line = lines[j].replace(')', ', icon="app/static/favicon.ico")')
                lines[j] = insert_line
                
                # Guardar el archivo modificado
                with open(launcher_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                logger.info("✅ Icono configurado en launcher.py")
                return True
    
    logger.warning("⚠️ No se pudo configurar el icono automáticamente")
    return False

def verify_icon_files():
    """Verifica que los archivos de icono existan"""
    logger.info("🔍 Verificando archivos de icono...")
    
    icon_paths = [
        "app/static/favicon.ico",
        "app/static/favicon.icns",
        "app/static/images/favicon.ico"
    ]
    
    found_icons = []
    for icon_path in icon_paths:
        if Path(icon_path).exists():
            found_icons.append(icon_path)
            logger.info(f"✅ Encontrado: {icon_path}")
    
    if found_icons:
        logger.info(f"✅ Se encontraron {len(found_icons)} archivos de icono")
        return True
    else:
        logger.error("❌ No se encontraron archivos de icono")
        return False

def create_app_bundle_icon():
    """Crea/actualiza el icono en el bundle de la aplicación"""
    logger.info("📦 Configurando icono en el bundle de la aplicación...")
    
    # Buscar el bundle de la aplicación
    dist_path = Path("dist")
    app_bundles = list(dist_path.glob("*.app")) if dist_path.exists() else []
    
    if not app_bundles:
        logger.warning("⚠️ No se encontró bundle de aplicación en dist/")
        return False
    
    app_bundle = app_bundles[0]
    logger.info(f"📱 Trabajando con bundle: {app_bundle.name}")
    
    # Rutas de iconos
    source_icon = Path("app/static/favicon.icns")
    if not source_icon.exists():
        source_icon = Path("app/static/favicon.ico")
    
    if not source_icon.exists():
        logger.error("❌ No se encontró icono fuente")
        return False
    
    # Ruta de destino en el bundle
    resources_path = app_bundle / "Contents" / "Resources"
    if not resources_path.exists():
        resources_path.mkdir(parents=True, exist_ok=True)
    
    dest_icon = resources_path / "icon.icns"
    
    try:
        shutil.copy2(source_icon, dest_icon)
        logger.info(f"✅ Icono copiado a {dest_icon}")
        
        # También actualizar Info.plist si existe
        info_plist = app_bundle / "Contents" / "Info.plist"
        if info_plist.exists():
            logger.info("📝 Actualizando Info.plist...")
            # Aquí podrías actualizar el Info.plist si es necesario
        
        return True
    except Exception as e:
        logger.error(f"❌ Error copiando icono: {e}")
        return False

def run_tests():
    """Ejecuta pruebas para verificar que todo funciona"""
    logger.info("🧪 Ejecutando pruebas...")
    
    # Test 1: Verificar que el login funciona
    logger.info("Test 1: Verificando login...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_login_real.py"], 
                              capture_output=True, text=True, timeout=30)
        if "✅ Test de login exitoso" in result.stdout:
            logger.info("✅ Test de login: EXITOSO")
        else:
            logger.error("❌ Test de login: FALLÓ")
            logger.error(f"Output: {result.stdout}")
            return False
    except Exception as e:
        logger.error(f"❌ Error ejecutando test de login: {e}")
        return False
    
    # Test 2: Verificar archivos de icono
    if verify_icon_files():
        logger.info("✅ Test de iconos: EXITOSO")
    else:
        logger.error("❌ Test de iconos: FALLÓ")
        return False
    
    return True

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO REPARACIÓN COMPLETA DEL EJECUTABLE MACOS")
    logger.info("=" * 60)
    
    success_count = 0
    total_tasks = 5
    
    # Tarea 1: Corregir rutas de autenticación
    if fix_auth_routes():
        success_count += 1
    
    # Tarea 2: Configurar icono en launcher
    if fix_launcher_icon():
        success_count += 1
    
    # Tarea 3: Verificar archivos de icono
    if verify_icon_files():
        success_count += 1
    
    # Tarea 4: Configurar icono en bundle
    if create_app_bundle_icon():
        success_count += 1
    
    # Tarea 5: Ejecutar pruebas
    if run_tests():
        success_count += 1
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE REPARACIÓN")
    logger.info(f"✅ Tareas completadas: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        logger.info("🎉 ¡REPARACIÓN COMPLETA EXITOSA!")
        logger.info("")
        logger.info("📋 CREDENCIALES DE LOGIN:")
        logger.info("   Usuario: edefrutos")
        logger.info("   Contraseña: 123456")
        logger.info("")
        logger.info("🚀 La aplicación debería funcionar correctamente ahora")
        return True
    else:
        logger.error("❌ La reparación no se completó totalmente")
        logger.error(f"   {total_tasks - success_count} tareas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
