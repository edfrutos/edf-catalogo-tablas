from PIL import Image, ImageDraw

def crear_imagen_perfil_default(path="static/default_profile.png"):
    # Crea una imagen simple de perfil por defecto
    img = Image.new('RGB', (128, 128), color=(200, 200, 200))
    d = ImageDraw.Draw(img)
    d.ellipse((32, 32, 96, 96), fill=(150, 150, 150))
    img.save(path) 