#!/usr/bin/env python3
"""
Script para corregir la foto de perfil del usuario
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_profile_image():
    """Corrige la foto de perfil del usuario"""
    
    print("🔧 CORRIGIENDO FOTO DE PERFIL")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    try:
        # Importar la aplicación Flask
        from main_app import create_app
        
        # Crear la aplicación
        app = create_app()
        
        with app.app_context():
            # Importar funciones necesarias
            from app.models import get_users_collection
            
            # Buscar el usuario edefrutos
            users_collection = get_users_collection()
            user = users_collection.find_one({"email": "edfrutos@gmail.com"})
            
            if user:
                print(f"\n👤 USUARIO ENCONTRADO:")
                print(f"   📧 Email: {user.get('email')}")
                print(f"   👤 Usuario: {user.get('username')}")
                print(f"   📸 Foto actual: {user.get('foto_perfil', 'No configurada')}")
                
                # Buscar la imagen correcta
                imagenes_path = "app/static/imagenes_subidas"
                if os.path.exists(imagenes_path):
                    miguel_images = [f for f in os.listdir(imagenes_path) if "Miguel" in f]
                    if miguel_images:
                        correct_image = miguel_images[0]
                        print(f"   ✅ Imagen encontrada: {correct_image}")
                        
                        # Actualizar la base de datos
                        result = users_collection.update_one(
                            {"_id": user["_id"]},
                            {"$set": {"foto_perfil": correct_image}}
                        )
                        
                        if result.modified_count > 0:
                            print(f"   ✅ Foto de perfil actualizada correctamente")
                            print(f"   📸 Nueva foto: {correct_image}")
                            
                            # Verificar que se actualizó
                            updated_user = users_collection.find_one({"_id": user["_id"]})
                            print(f"   🔍 Verificación: {updated_user.get('foto_perfil')}")
                            
                            return True
                        else:
                            print(f"   ❌ Error al actualizar la foto de perfil")
                            return False
                    else:
                        print(f"   ❌ No se encontraron imágenes de Miguel")
                        return False
                else:
                    print(f"   ❌ Directorio {imagenes_path} no existe")
                    return False
            else:
                print(f"   ❌ Usuario no encontrado")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    
    print("🚀 CORRIGIENDO FOTO DE PERFIL")
    print("=" * 50)
    
    # Ejecutar corrección
    success = fix_profile_image()
    
    if success:
        print(f"\n🎉 Corrección completada")
        print(f"\n💡 Ahora la foto de perfil debería mostrarse correctamente")
        return True
    else:
        print(f"\n❌ Error en la corrección")
        return False

if __name__ == "__main__":
    main()
