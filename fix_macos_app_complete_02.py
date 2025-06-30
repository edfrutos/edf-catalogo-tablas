import os
import sys
import logging
import shutil
from pathlib import Path
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_auth_routes(main_app_path="main_app.py"):
    """Corrige el problema de las rutas de autenticación"""
    logger.info("🔧 Corrigiendo rutas de autenticación...")
    
    main_app_path = Path(main_app_path)
    if not main_app_path.exists():
        logger.error(f"❌ No se encontró {main_app_path}")
        return False
    
    try:
        with open(main_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"❌ Error leyendo {main_app_path}: {e}")
        return False

    # Verificar y aplicar la corrección (más robusta)
    if "app.register_blueprint(auth_bp, url_prefix='/auth')" in content:
        logger.info("✅ Las rutas de autenticación ya están corregidas")
        return True
    elif "app.register_blueprint(auth_bp, url_prefix='')" in content:
        content = content.replace("app.register_blueprint(auth_bp, url_prefix='')", "app.register_blueprint(auth_bp, url_prefix='/auth')")
        try:
            with open(main_app_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("✅ Rutas de autenticación corregidas")
            return True
        except Exception as e:
            logger.error(f"❌ Error escribiendo {main_app_path}: {e}")
            return False
    else:
        logger.warning("⚠️ No se encontró la línea a corregir en main_app.py.  Revisa manualmente.")
        return False

def fix_launcher_icon(launcher_path="launcher.py"):
    """Configura el icono en el launcher"""
    logger.info("🎨 Configurando icono en launcher...")
    
    launcher_path = Path(launcher_path)
    if not launcher_path.exists():
        logger.error(f"❌ No se encontró {launcher_path}")
        return False
    
    try:
        with open(launcher_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"❌ Error leyendo {launcher_path}: {e}")
        return False

    if "icon=" in content and "favicon.ico" in content:
        logger.info("✅ El icono ya está configurado en launcher.py")
        return True

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if 'webview.create_window(' in line and 'icon=' not in line:
            # Busca el paréntesis de cierre correctamente, manejando casos complejos
            paren_count = 1
            j = i + 1
            while j < len(lines) and paren_count > 0:
                paren_count += lines[j].count('(')
                paren_count -= lines[j].count(')')
                j += 1
            
            if j >= len(lines):
                logger.warning("⚠️ No se pudo encontrar el cierre del paréntesis en webview.create_window()")
                return False

            lines.insert(j, f'                icon="app/static/favicon.ico",') #Añadido indentación para mejor legibilidad.


            try:
                with open(launcher_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                logger.info("✅ Icono configurado en launcher.py")
                return True
            except Exception as e:
                logger.error(f"❌ Error escribiendo {launcher_path}: {e}")
                return False
    
    logger.warning("⚠️ No se pudo configurar el icono automáticamente. Revisa manualmente.")
    return False


def verify_icon_files():
    """Verifica que los archivos de icono existan"""
    logger.info("🔍 Verificando archivos de icono...")
    
    icon_paths = [
        "app/static/favicon.ico",
        "app/static/favicon.icns",
        "app/static/images/favicon.ico"
    ]
    
    found_icons = [icon_path for icon_path in icon_paths if Path(icon_path).exists()]
    
    if found_icons:
        for icon_path in found_icons:
            logger.info(f"✅ Encontrado: {icon_path}")
        logger.info(f"✅ Se encontraron {len(found_icons)} archivos de icono")
        return True
    else:
        logger.error("❌ No se encontraron archivos de icono")
        return False

def create_app_bundle_icon():
    """Crea/actualiza el icono en el bundle de la aplicación"""
    logger.info("📦 Configurando icono en el bundle de la aplicación...")
    
    dist_path = Path("dist")
    if not dist_path.exists():
        logger.warning("⚠️ No se encontró el directorio dist/")
        return False
    
    app_bundles = list(dist_path.glob("*.app"))
    if not app_bundles:
        logger.warning("⚠️ No se encontró bundle de aplicación en dist/")
        return False
    
    app_bundle = app_bundles[0]
    logger.info(f"📱 Trabajando con bundle: {app_bundle.name}")
    
    source_icon = Path("app/static/favicon.icns")
    if not source_icon.exists():
        source_icon = Path("app/static/favicon.ico")
    
    if not source_icon.exists():
        logger.error("❌ No se encontró icono fuente")
        return False
    
    resources_path = app_bundle / "Contents" / "Resources"
    resources_path.mkdir(parents=True, exist_ok=True)
    
    dest_icon = resources_path / "icon.icns"
    
    try:
        shutil.copy2(source_icon, dest_icon)
        logger.info(f"✅ Icono copiado a {dest_icon}")
        return True
    except Exception as e:
        logger.error(f"❌ Error copiando icono: {e}")
        return False

def run_tests():
    """Ejecuta pruebas para verificar que todo funciona"""
    logger.info("🧪 Ejecutando pruebas...")
    
    # Test 1: Verificar que el login funciona (mejorado para manejar errores)
    logger.info("Test 1: Verificando login...")
    try:
        result = subprocess.run([sys.executable, "test_login_real.py"], capture_output=True, text=True, timeout=30, check=True) # check=True lanza excepción si el comando falla
        logger.info("✅ Test de login: EXITOSO")
    except subprocess.CalledProcessError as e:
        logger.error("❌ Test de login: FALLÓ")
        logger.error(f"Salida de error: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("❌ No se encontró el archivo test_login_real.py")
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
    
    # Tareas de reparación con manejo de excepciones más robusto
    if fix_auth_routes(): success_count += 1
    if fix_launcher_icon(): success_count += 1
    if verify_icon_files(): success_count += 1
    if create_app_bundle_icon(): success_count += 1
    if run_tests(): success_count += 1
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE REPARACIÓN")
    logger.info(f"✅ Tareas completadas: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        logger.info("🎉 ¡REPARACIÓN COMPLETA EXITOSA!")
        #Eliminando credenciales por seguridad
        # logger.info("")
        # logger.info("📋 CREDENCIALES DE LOGIN:")
        # logger.info("   Usuario: edefrutos")
        # logger.info("   Contraseña: 123456")
        # logger.info("")
        logger.info("🚀 La aplicación debería funcionar correctamente ahora")
        return True
    else:
        logger.error("❌ La reparación no se completó totalmente")
        logger.error(f"   {total_tasks - success_count} tareas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)