#!/usr/bin/env python3
"""
Script: final_cleanup.py
Descripción: Limpieza final de datos, pide al usuario qué datos limpiar.
"""

print("=== Limpieza final de datos ===")
print("¿Qué tipo de datos deseas limpiar?")
print("1. Usuarios")
print("2. Catálogos")
print("3. Logs")
print("4. Otro")
opcion = input("Selecciona una opción (1-4): ")

if opcion == '1':
    print("Limpieza de usuarios seleccionada.")
    # Aquí iría la lógica real
elif opcion == '2':
    print("Limpieza de catálogos seleccionada.")
    # Aquí iría la lógica real
elif opcion == '3':
    print("Limpieza de logs seleccionada.")
    # Aquí iría la lógica real
else:
    otro = input("Especifica qué deseas limpiar: ")
    print(f"Limpieza personalizada de: {otro}")
    # Aquí iría la lógica real
print("(Simulación) Limpieza completada.") 