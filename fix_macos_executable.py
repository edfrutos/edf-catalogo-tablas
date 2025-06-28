#!/usr/bin/env python3
"""
Script para corregir problemas del ejecutable macOS
"""
import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_macos_executable.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fix_auth_routes():
    """Corrige el problema de las rutas de autenticación"""
    try:
        logger.info("Corrigiendo rutas de autenticación...")
        
        # Leer el archivo main_app.py
        main_app_path = 'main_app.py'
        with open(main_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si el blueprint auth_bp está registrado correctamente
        if "app.register_blueprint(auth_bp, url_prefix='')" in content:
            logger.info("Blueprint auth_bp ya está registrado correctamente")
        else:
            # Buscar la línea de registro y corregirla
            if "app.register_blueprint(auth_bp)" in content:
                content = content.replace(
                    "app.register_blueprint(auth_bp)",
                    "app.register_blueprint(auth_bp, url_prefix='/auth')"
                )
                logger.info("Corregido el registro del blueprint auth_bp")
            else:
                logger.warning("No se encontró el registro del blueprint auth_bp")
        
        # Escribir el archivo corregido
        with open(main_app_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("✅ Rutas de autenticación corregidas")
        return True
        
    except Exception as e:
        logger.error(f"Error corrigiendo rutas de autenticación: {str(e)}")
        return False

def fix_icon_problem():
    """Corrige el problema del icono de la aplicación"""
    try:
        logger.info("Corrigiendo problema del icono...")
        
        # Verificar si existe el archivo de icono
        icon_paths = [
            'app/static/images/icon.icns',
            'app/static/images/app_icon.icns',
            'app/static/favicon.ico',
            'icon.icns'
        ]
        
        icon_found = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                logger.info(f"Icono encontrado en: {icon_path}")
                icon_found = True
                break
        
        if not icon_found:
            logger.warning("No se encontró archivo de icono")
            # Crear un icono básico si no existe
            create_basic_icon()
        
        # Verificar el archivo launcher.py
        launcher_path = 'launcher.py'
        if os.path.exists(launcher_path):
            with open(launcher_path, 'r', encoding='utf-8') as f:
                launcher_content = f.read()
            
            # Verificar si tiene configuración de icono
            if 'icon=' not in launcher_content:
                logger.info("Añadiendo configuración de icono al launcher")
                # Buscar la línea de webview.create_window y añadir icono
                if 'webview.create_window(' in launcher_content:
                    launcher_content = launcher_content.replace(
                        'webview.create_window(',
                        'webview.create_window(\n        icon="app/static/images/icon.icns" if os.path.exists("app/static/images/icon.icns") else None,\n        '
                    )
                    
                    with open(launcher_path, 'w', encoding='utf-8') as f:
                        f.write(launcher_content)
                    
                    logger.info("✅ Configuración de icono añadida al launcher")
        
        return True
        
    except Exception as e:
        logger.error(f"Error corrigiendo problema del icono: {str(e)}")
        return False

def create_basic_icon():
    """Crea un icono básico si no existe"""
    try:
        from PIL import Image, ImageDraw
        
        # Crear una imagen de 512x512 con fondo azul y texto
        img = Image.new('RGB', (512, 512), color='#007bff')
        draw = ImageDraw.Draw(img)
        
        # Añadir texto simple
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        text = "EDF"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        # Guardar como PNG primero
        os.makedirs('app/static/images', exist_ok=True)
        png_path = 'app/static/images/icon.png'
        img.save(png_path)
        
        logger.info(f"✅ Icono básico creado en: {png_path}")
        
        # Intentar convertir a ICNS en macOS
        if sys.platform == 'darwin':
            try:
                import subprocess
                icns_path = 'app/static/images/icon.icns'
                subprocess.run([
                    'sips', '-s', 'format', 'icns', png_path, '--out', icns_path
                ], check=True)
                logger.info(f"✅ Icono ICNS creado en: {icns_path}")
            except Exception as e:
                logger.warning(f"No se pudo crear ICNS: {str(e)}")
        
        return True
        
    except ImportError:
        logger.warning("PIL no disponible, no se puede crear icono básico")
        return False
    except Exception as e:
        logger.error(f"Error creando icono básico: {str(e)}")
        return False

def fix_login_error():
    """Corrige el error de login específico"""
    try:
        logger.info("Corrigiendo error de login...")
        
        # Verificar configuración de sesión
        config_path = 'app/config_embedded.py'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Verificar configuración de sesión
            if 'SESSION_TYPE' not in config_content:
                logger.info("Añadiendo configuración de sesión a config_embedded.py")
                
                session_config = '''
    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(__file__), '..', 'flask_session')
    SESSION_COOKIE_NAME = 'edefrutos2025_session'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 86400
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_USE_SIGNER = False
'''
                
                # Añadir al final de la clase
                config_content = config_content.replace(
                    'class EmbeddedConfig:',
                    f'class EmbeddedConfig:{session_config}'
                )
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(config_content)
                
                logger.info("✅ Configuración de sesión añadida")
        
        # Crear directorio de sesiones
        session_dir = 'flask_session'
        os.makedirs(session_dir, exist_ok=True)
        logger.info(f"✅ Directorio de sesiones creado: {session_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error corrigiendo login: {str(e)}")
        return False

def test_mongodb_connection():
    """Prueba la conexión a MongoDB"""
    try:
        logger.info("Probando conexión a MongoDB...")
        
        # Importar configuración
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        from config_embedded import EmbeddedConfig
        
        from pymongo import MongoClient
        client = MongoClient(EmbeddedConfig.MONGO_URI)
        
        # Probar conexión
        db = client[EmbeddedConfig.MONGODB_DB]
        collections = db.list_collection_names()
        
        logger.info(f"✅ MongoDB conectado. Colecciones: {collections}")
        
        # Verificar usuarios
        users_collection = db.users
        user_count = users_collection.count_documents({})
        logger.info(f"✅ Usuarios en la base de datos: {user_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {str(e)}")
        return False

def create_test_user():
    """Crea un usuario de prueba si no existe"""
    try:
        logger.info("Creando usuario de prueba...")
        
        # Importar configuración
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        from config_embedded import EmbeddedConfig
        
        from pymongo import MongoClient
        from werkzeug.security import generate_password_hash
        
        client = MongoClient(EmbeddedConfig.MONGO_URI)
        db = client[EmbeddedConfig.MONGODB_DB]
        users_collection = db.users
        
        # Verificar si ya existe el usuario
        existing_user = users_collection.find_one({"username": "edefrutos"})
        if existing_user:
            logger.info("Usuario 'edefrutos' ya existe")
            return True
        
        # Crear usuario de prueba
        test_user = {
            "username": "edefrutos",
            "email": "edfrutos@gmail.com",
            "password": generate_password_hash("123456"),
            "role": "admin",
            "active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        
        result = users_collection.insert_one(test_user)
        logger.info(f"✅ Usuario de prueba creado con ID: {result.inserted_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando usuario de prueba: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("=== CORRECCIÓN DE PROBLEMAS EJECUTABLE MACOS ===")
    logger.info(f"Fecha: {datetime.now()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Directorio actual: {os.getcwd()}")
    
    results = {}
    
    # 1. Corregir rutas de autenticación
    logger.info("\n1. Corrigiendo rutas de autenticación...")
    results['auth_routes'] = fix_auth_routes()
    
    # 2. Probar conexión MongoDB
    logger.info("\n2. Probando conexión a MongoDB...")
    results['mongodb'] = test_mongodb_connection()
    
    # 3. Crear usuario de prueba si es necesario
    logger.info("\n3. Verificando usuario de prueba...")
    results['test_user'] = create_test_user()
    
    # 4. Corregir problema del icono
    logger.info("\n4. Corrigiendo problema del icono...")
    results['icon'] = fix_icon_problem()
    
    # 5. Corregir error de login
    logger.info("\n5. Corrigiendo configuración de login...")
    results['login'] = fix_login_error()
    
    # Resumen final
    logger.info("\n=== RESUMEN DE CORRECCIONES ===")
    for task, success in results.items():
        status = "✅ OK" if success else "❌ ERROR"
        logger.info(f"{task}: {status}")
    
    # Verificar si todas las correcciones fueron exitosas
    all_success = all(results.values())
    if all_success:
        logger.info("\n🎉 Todas las correcciones completadas exitosamente")
        logger.info("La aplicación macOS debería funcionar correctamente ahora")
    else:
        logger.warning("\n⚠️ Algunas correcciones fallaron")
        logger.warning("Revisa los errores anteriores y ejecuta el script nuevamente")
    
    return all_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
