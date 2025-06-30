#!/usr/bin/env python3
# Script: insert_admin_and_minimum_data.py
# Descripción: Este script genera contraseñas aleatorias y permite al usuario guardarlas en un archivo CSV.
# Uso: python3 insert_admin_and_minimum_data.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-30

import random
import string
import csv

def generar_contraseña(longitud=12):
    """Genera una contraseña aleatoria de la longitud especificada."""
    caracteres = string.ascii_letters + string.digits + string.punctuation
    contraseña = ''.join(random.choice(caracteres) for i in range(longitud))
    return contraseña

def guardar_contraseñas_csv(contraseñas, nombre_archivo="contraseñas.csv"):
    """Guarda las contraseñas en un archivo CSV."""
    try:
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Nombre de la contraseña", "Contraseña"])  #Encabezado
            for nombre, contraseña in contraseñas:
                writer.writerow([nombre, contraseña])
        print(f"Contraseñas guardadas en {nombre_archivo}")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")


def generar_y_guardar_contraseñas():
    """Genera contraseñas y permite guardarlas en un archivo CSV."""
    contraseñas = []
    while True:
        nombre_contraseña = input("Ingrese el nombre para la contraseña (o 'salir' para terminar): ")
        if nombre_contraseña.lower() == 'salir':
            break

        if not nombre_contraseña: #Maneja entrada vacía
            print("Por favor ingrese un nombre para la contraseña.")
            continue

        contraseña = generar_contraseña()
        contraseñas.append((nombre_contraseña, contraseña))
        print(f"Contraseña generada para {nombre_contraseña}: {contraseña}")


    if contraseñas:
        guardar_o_no = input("¿Desea guardar las contraseñas en un archivo CSV? (s/n): ")
        if guardar_o_no.lower() == 's':
            nombre_archivo = input("Ingrese el nombre del archivo (o presione Enter para usar 'contraseñas.csv'): ")
            nombre_archivo = nombre_archivo or "contraseñas.csv"  #Usar nombre por defecto si está vacío
            guardar_contraseñas_csv(contraseñas, nombre_archivo)

if __name__ == "__main__":
    generar_y_guardar_contraseñas()
# This script generates random passwords and allows the user to save them in a CSV file.
