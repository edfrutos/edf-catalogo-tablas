#!/usr/bin/env python3
"""
Script: aplicar_cabecera_todos.py
Descripción: Aplica la cabecera estándar a todos los scripts Python del proyecto, excepto los de venv, .git y site-packages.
Uso: python3 tools/aplicar_cabecera_todos.py
Autor: EDF EDF EDF EDF EDF Equipo de desarrollo - 2024-05-28
"""
import os
import subprocess

EXCLUIR = ['venv', '.git', 'site-packages']

scripts_py = []
for root, dirs, files in os.walk('.'):
    # Excluir carpetas no deseadas
    dirs[:] = [d for d in dirs if d not in EXCLUIR]
    for file in files:
        if file.endswith('.py'):
            ruta = os.path.join(root, file)
            # Excluir paths que contengan carpetas excluidas en cualquier parte
            if any(ex in ruta for ex in EXCLUIR):
                continue
            scripts_py.append(ruta)

if not scripts_py:
    print("No se encontraron scripts Python para procesar.")
else:
    print(f"Procesando {len(scripts_py)} scripts Python...")
    cmd = ['python3', 'tools/insertar_cabecera.py'] + scripts_py
    subprocess.run(cmd)
    print("Cabeceras aplicadas a todos los scripts Python del proyecto.") 