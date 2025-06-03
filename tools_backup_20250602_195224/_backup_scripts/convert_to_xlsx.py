#!/usr/bin/env python3
from openpyxl import Workbook
import csv

# Leer el CSV
rows = []
with open('hojas_de_calculo/conectores.csv', 'r', encoding='utf-8') as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        rows.append(row)

# Crear un nuevo libro de Excel
wb = Workbook()
ws = wb.active
ws.title = "Conectores"

# Escribir los datos
for row in rows:
    ws.append(row)

# Ajustar el ancho de las columnas
for column in ws.columns:
    max_length = 0
    column = list(column)
    for cell in column:
        try:
            if len(str(cell.value)) > max_length:
                max_length = len(str(cell.value))
        except:
            pass
    adjusted_width = (max_length + 2)
    ws.column_dimensions[column[0].column_letter].width = adjusted_width

# Guardar el archivo
wb.save('hojas_de_calculo/conectores.xlsx')
