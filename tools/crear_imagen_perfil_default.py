#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PIL import Image, ImageDraw, ImageFont
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def crear_imagen_perfil_default():
    """
    Crea una imagen de perfil predeterminada simple con las iniciales 'U' (Usuario)
    """
    try:
        # Rutas
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
        uploads_dir = os.path.join(static_dir, 'uploads')
        
        # Crear directorios si no existen
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Ruta de la imagen predeterminada
        default_profile_path = os.path.join(static_dir, 'default_profile.png')
        
        # Crear una imagen cuadrada
        size = 200
        img = Image.new('RGB', (size, size), color=(52, 152, 219))  # Azul
        
        # Dibujar un círculo
        draw = ImageDraw.Draw(img)
        
        # Agregar texto (inicial 'U')
        try:
            # Intentar cargar una fuente
            font = ImageFont.truetype('DejaVuSans.ttf', 100)
        except IOError:
            # Si no está disponible, usar la fuente predeterminada
            font = ImageFont.load_default()
        
        # Dibujar la inicial centrada
        text = "U"
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (80, 80)
        position = ((size - text_width) // 2, (size - text_height) // 2)
        draw.text(position, text, font=font, fill=(255, 255, 255))
        
        # Guardar la imagen
        img.save(default_profile_path)
        logger.info(f"✅ Imagen de perfil predeterminada creada en {default_profile_path}")
        
        # También guardar una copia en uploads
        uploads_profile_path = os.path.join(uploads_dir, 'default_profile.png')
        img.save(uploads_profile_path)
        logger.info(f"✅ Copia guardada en {uploads_profile_path}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error al crear imagen de perfil predeterminada: {str(e)}")
        
        # Plan B: Crear una imagen muy simple sin usar PIL
        try:
            with open(default_profile_path, 'wb') as f:
                # Crear un archivo PNG mínimo válido (1x1 pixel azul)
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x90\xfb\xcf\x00\x00\x02\x10\x01\x05\xd8\xfa\x0f\xdf\x00\x00\x00\x00IEND\xaeB`\x82')
            logger.info(f"✅ Imagen de perfil mínima creada en {default_profile_path}")
            
            # También guardar una copia en uploads
            with open(uploads_profile_path, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x90\xfb\xcf\x00\x00\x02\x10\x01\x05\xd8\xfa\x0f\xdf\x00\x00\x00\x00IEND\xaeB`\x82')
            logger.info(f"✅ Copia mínima guardada en {uploads_profile_path}")
            return True
        except Exception as e2:
            logger.error(f"❌ Error en plan B: {str(e2)}")
            return False

if __name__ == "__main__":
    crear_imagen_perfil_default()
