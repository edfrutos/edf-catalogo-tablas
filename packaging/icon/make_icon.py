"""Genera el icono de TablaTeca (PNG 1024 + iconset + icns) desde packaging/icon/TablaTeca_source.jpg.

Uso: python packaging/icon/make_icon.py packaging/icon/TablaTeca_source.jpg <carpeta_salida>
Requiere Pillow, numpy y scipy. Después copiar TablaTeca.icns como edf_developer.icns.
"""
import sys, struct, io, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(int)
dark = 765 - a.sum(axis=2)

# 1) Silueta: lo que no es fondo blanco ni sombra suave
m = dark > 300
m = ndi.binary_closing(m, iterations=3)
m = ndi.binary_fill_holes(m)
lab, n = ndi.label(m)
sizes = ndi.sum(m, lab, range(1, n + 1))
m = lab == (1 + int(np.argmax(sizes)))
m = ndi.binary_erosion(m, iterations=1)

ys, xs = np.where(m)
x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
print("silueta", x0, x1, y0, y1, "->", x1 - x0, "x", y1 - y0)

# 2) Recorte con la máscara como alfa (borde suavizado)
alpha = Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.0))
rgba = im.copy().convert("RGBA")
rgba.putalpha(alpha)
art = rgba.crop((x0, y0, x1, y1))

# 3) A cuadrado (la silueta mide ~605x624: estiramiento del 3 %, imperceptible)
ART = 824
art = art.resize((ART, ART), Image.LANCZOS)

# 4) Lienzo 1024 con margen y sombra suave, como la plantilla de macOS
canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
shadow = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
sh_alpha = Image.new("L", (1024, 1024), 0)
sh_alpha.paste(art.split()[3], (100, 100 + 12))
sh_alpha = sh_alpha.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.35))
shadow.putalpha(sh_alpha)
canvas = Image.alpha_composite(canvas, shadow)
canvas.alpha_composite(art, (100, 100))
canvas.save(os.path.join(OUT, "TablaTeca_1024.png"))

# 5) iconset (nombres de iconutil) y .icns escrito a mano (chunks PNG)
iconset = os.path.join(OUT, "TablaTeca.iconset")
os.makedirs(iconset, exist_ok=True)
sizes_px = {
    "icon_16x16.png": 16, "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32, "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128, "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256, "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512, "icon_512x512@2x.png": 1024,
}
def png_bytes(px):
    b = io.BytesIO()
    canvas.resize((px, px), Image.LANCZOS).save(b, "PNG", optimize=True)
    return b.getvalue()
for name, px in sizes_px.items():
    open(os.path.join(iconset, name), "wb").write(png_bytes(px))

chunks = [  # tipo, píxeles
    (b"icp4", 16), (b"icp5", 32), (b"icp6", 64),
    (b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024),
    (b"ic11", 32), (b"ic12", 64), (b"ic13", 256), (b"ic14", 512),
]
body = b""
for t, px in chunks:
    data = png_bytes(px)
    body += t + struct.pack(">I", 8 + len(data)) + data
open(os.path.join(OUT, "TablaTeca.icns"), "wb").write(b"icns" + struct.pack(">I", 8 + len(body)) + body)
print("icns", 8 + len(body), "bytes")
