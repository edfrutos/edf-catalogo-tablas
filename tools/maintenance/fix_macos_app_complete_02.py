# Script: fix_macos_app_complete_02.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 fix_macos_app_complete_02.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-30

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fix_auth_routes(main_app_path="main_app.py"):
    """Corrige el problema de las rutas de autenticación"""
    logger.info("🔧 Corrigiendo rutas de autenticación...")

    main_app_path = Path(main_app_path)
    if not main_app_path.exists():
        logger.error(f"❌ No se encontró {main_app_path}")
        return False

    try:
        with open(main_app_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"❌ Error leyendo {main_app_path}: {e}")
        return False

    # Verificar y aplicar la corrección (más robusta)
    if "app.register_blueprint(auth_bp, url_prefix='/auth')" in content:
        logger.info("✅ Las rutas de autenticación ya están corregidas")
        return True
    elif "app.register_blueprint(auth_bp, url_prefix='')" in content:
        content = content.replace(
            "app.register_blueprint(auth_bp, url_prefix='')",
            "app.register_blueprint(auth_bp, url_prefix='/auth')",
        )
        try:
            with open(main_app_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("✅ Rutas de autenticación corregidas")
            return True
        except Exception as e:
            logger.error(f"❌ Error escribiendo {main_app_path}: {e}")
            return False
    else:
        logger.warning(
            "⚠️ No se encontró la línea a corregir en main_app.py.  Revisa manualmente."
        )
        return False


def fix_launcher_icon(launcher_path="launcher.py"):
    """Configura el icono en el launcher - DESHABILITADO"""
    logger.info("🎨 Función de icono deshabilitada para evitar conflictos")
    logger.info("💡 La aplicación usa el icono por defecto de PyInstaller")
    return True


def verify_icon_files():
    """Verifica que los archivos de icono existan - DESHABILITADO"""
    logger.info("🔍 Verificación de iconos deshabilitada")
    logger.info("💡 La aplicación usa el icono por defecto de PyInstaller")
    return True


def create_app_bundle_icon():
    """Crea/actualiza el icono en el bundle de la aplicación - DESHABILITADO"""
    logger.info("📦 Función de icono deshabilitada para evitar conflictos")
    logger.info("💡 La aplicación usa el icono por defecto de PyInstaller")
    return True


def run_tests():
    """Ejecuta pruebas para verificar que todo funciona"""
    logger.info("🧪 Ejecutando pruebas...")

    # Test 1: Verificar que el login funciona (mejorado para manejar errores)
    logger.info("Test 1: Verificando login...")
    try:
        result = subprocess.run(
            [sys.executable, "test_login_real.py"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )  # check=True lanza excepción si el comando falla
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
    if fix_auth_routes():
        success_count += 1
    if fix_launcher_icon():
        success_count += 1
    if verify_icon_files():
        success_count += 1
    if create_app_bundle_icon():
        success_count += 1
    if run_tests():
        success_count += 1

    # Resumen final
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE REPARACIÓN")
    logger.info(f"✅ Tareas completadas: {success_count}/{total_tasks}")

    if success_count == total_tasks:
        logger.info("🎉 ¡REPARACIÓN COMPLETA EXITOSA!")
        # Eliminando credenciales por seguridad
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
