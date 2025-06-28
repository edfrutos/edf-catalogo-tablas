#!/usr/bin/env python3
"""
Script: cleanup_users.py
Descripción: Limpia usuarios según criterios introducidos por el usuario.
"""

import sys

print("=== Limpieza de usuarios ===")
criterio = input("Introduce el criterio de limpieza (por ejemplo, email, nombre, etc.): ")
valor = input(f"Introduce el valor para el criterio '{criterio}': ")

print(f"Se limpiarán usuarios donde {criterio} = {valor}")
# Aquí iría la lógica real de limpieza, por ejemplo:
# limpiar_usuarios(criterio, valor)
print("(Simulación) Limpieza completada.") 