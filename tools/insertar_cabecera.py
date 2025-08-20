#!/usr/bin/env python3
"""
Script: insertar_cabecera.py
Descripción: Inserta una cabecera estándar de documentación en scripts Python que no la tengan.
Uso: python3 insertar_cabecera.py ruta/al/script.py
Autor: EDF Equipo de desarrollo - 2024-05-28
"""
import os
import sys
from datetime import date

CABECERA = '''# Script: {nombre}
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 {nombre} [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - {fecha}
'''

def tiene_cabecera(path):
    with open(path, encoding='utf-8') as f:
        for _ in range(5):
            linea = f.readline()
            if '#' in linea:
                return True
    return False

def insertar_cabecera(path):
    nombre = os.path.basename(path)
    fecha = date.today().isoformat()
    with open(path, encoding='utf-8') as f:
        contenido = f.read()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(CABECERA.format(nombre=nombre, fecha=fecha))
        f.write('\n')
        f.write(contenido)
    print(f"Cabecera insertada en {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 insertar_cabecera.py ruta/al/script.py")
        sys.exit(1)
    for script in sys.argv[1:]:
        if not os.path.isfile(script):
            print(f"No existe el archivo: {script}")
            continue
        if tiene_cabecera(script):
            print(f"Ya tiene cabecera: {script}")
        else:
            insertar_cabecera(script)
