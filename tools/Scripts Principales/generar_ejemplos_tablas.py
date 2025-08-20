#!/usr/bin/env python3
"""
Script: generar_ejemplos_tablas.py
Descripción: Genera tablas de ejemplo con 15 filas sobre temas de oficina, periféricos y almacenamiento, incluyendo enlaces a imágenes, en formatos .xlsx y .csv.
Uso: python3 tools/generar_ejemplos_tablas.py
Autor: EDF Equipo de desarrollo - 2024-05-28
"""
import csv
import os
from datetime import datetime

from openpyxl import Workbook

EXPORT_DIR = 'exportados'
os.makedirs(EXPORT_DIR, exist_ok=True)
fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')

# Datos de ejemplo
articulos = [
    ["Lápiz", "Para escribir o dibujar", "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=400&q=80"],
    ["Bolígrafo", "Instrumento de escritura de tinta", "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=400&q=80"],
    ["Cuaderno", "Para tomar notas", "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=400&q=80"],
    ["Grapadora", "Para unir hojas", "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=400&q=80"],
    ["Tijeras", "Para cortar papel", "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=400&q=80"],
    ["Regla", "Para medir", "https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80"],
    ["Carpeta", "Para archivar documentos", "https://images.unsplash.com/photo-1515168833906-d2a3b82b1a48?auto=format&fit=crop&w=400&q=80"],
    ["Post-it", "Notas adhesivas", "https://images.unsplash.com/photo-1503676382389-4809596d5290?auto=format&fit=crop&w=400&q=80"],
    ["Corrector", "Para corregir errores de tinta", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Cinta adhesiva", "Para pegar papeles", "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80"],
    ["Archivador", "Para guardar documentos", "https://images.unsplash.com/photo-1515168833906-d2a3b82b1a48?auto=format&fit=crop&w=400&q=80"],
    ["Calculadora", "Para operaciones matemáticas", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Silla de oficina", "Para sentarse cómodamente", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Mesa de escritorio", "Superficie de trabajo", "https://images.unsplash.com/photo-1465101178521-c1a9136a3b99?auto=format&fit=crop&w=400&q=80"],
    ["Lámpara de escritorio", "Iluminación", "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80"]
]

perifericos = [
    ["Teclado", "Entrada de texto", "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80"],
    ["Ratón", "Dispositivo apuntador", "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=400&q=80"],
    ["Monitor", "Visualización de datos", "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80"],
    ["Impresora", "Impresión de documentos", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Escáner", "Digitalización de documentos", "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80"],
    ["Altavoces", "Salida de audio", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Micrófono", "Entrada de audio", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Cámara web", "Captura de video", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Joystick", "Control de juegos", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Tableta gráfica", "Dibujo digital", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Proyector", "Proyección de imagen", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Lector de tarjetas", "Lectura de tarjetas SD", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Disco duro externo", "Almacenamiento adicional", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Memoria USB", "Almacenamiento portátil", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Pantalla táctil", "Interacción directa", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"]
]

almacenamiento = [
    ["Disco duro interno", "Almacenamiento principal", "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80"],
    ["SSD interno", "Almacenamiento rápido", "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=400&q=80"],
    ["Unidad óptica (DVD)", "Lectura de discos", "https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80"],
    ["Disco duro externo", "Almacenamiento adicional", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["SSD externo", "Almacenamiento rápido portátil", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Memoria USB", "Almacenamiento portátil", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80"],
    ["Tarjeta SD", "Almacenamiento en cámaras", "https://images.unsplash.com/photo-1503676382389-4809596d5290?auto=format&fit=crop&w=400&q=80"],
    ["MicroSD", "Almacenamiento en móviles", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Blu-ray", "Almacenamiento óptico", "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80"],
    ["Cinta magnética", "Backup de datos", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["RAID", "Almacenamiento redundante", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["NAS", "Almacenamiento en red", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Cloud Storage", "Almacenamiento en la nube", "https://images.unsplash.com/photo-1465101178521-c1a9136a3b99?auto=format&fit=crop&w=400&q=80"],
    ["Zip Drive", "Almacenamiento portátil antiguo", "https://images.unsplash.com/photo-1515168833906-d2a3b82b1a48?auto=format&fit=crop&w=400&q=80"],
    ["Disquete", "Almacenamiento clásico", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"]
]

motos = [
    ["Honda CB500F", "Naked urbana de media cilindrada", "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?auto=format&fit=crop&w=400&q=80"],
    ["Yamaha MT-07", "Naked deportiva", "https://images.unsplash.com/photo-1518655048521-f130df041f66?auto=format&fit=crop&w=400&q=80"],
    ["Kawasaki Z900", "Naked potente", "https://images.unsplash.com/photo-1465447142348-e9952c393450?auto=format&fit=crop&w=400&q=80"],
    ["BMW R1250GS", "Trail adventure", "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=400&q=80"],
    ["Ducati Panigale V4", "Superdeportiva", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Suzuki V-Strom 650", "Trail versátil", "https://images.unsplash.com/photo-1465101178521-c1a9136a3b99?auto=format&fit=crop&w=400&q=80"],
    ["Harley-Davidson Iron 883", "Custom clásica", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Triumph Bonneville T120", "Clásica británica", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["KTM Duke 390", "Naked ligera y ágil", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Honda Africa Twin", "Trail de aventura", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Yamaha XSR700", "Neo-retro", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["BMW S1000RR", "Superdeportiva", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Ducati Scrambler", "Scrambler moderna", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Suzuki GSX-S750", "Naked deportiva", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Kawasaki Versys 650", "Trail asfáltica", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"]
]

coches = [
    ["Toyota Corolla", "Compacto eficiente", "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?auto=format&fit=crop&w=400&q=80"],
    ["Volkswagen Golf", "Hatchback popular", "https://images.unsplash.com/photo-1518655048521-f130df041f66?auto=format&fit=crop&w=400&q=80"],
    ["Ford Focus", "Compacto versátil", "https://images.unsplash.com/photo-1465447142348-e9952c393450?auto=format&fit=crop&w=400&q=80"],
    ["BMW Serie 3", "Sedán premium", "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=400&q=80"],
    ["Audi A4", "Sedán elegante", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Mercedes-Benz Clase C", "Sedán de lujo", "https://images.unsplash.com/photo-1465101178521-c1a9136a3b99?auto=format&fit=crop&w=400&q=80"],
    ["Seat León", "Hatchback español", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Renault Clio", "Urbano francés", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Peugeot 308", "Compacto francés", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Kia Ceed", "Compacto coreano", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Hyundai i30", "Compacto moderno", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Mazda 3", "Compacto japonés", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Honda Civic", "Compacto deportivo", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Opel Astra", "Compacto alemán", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"],
    ["Citroën C4", "Compacto francés", "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80"]
]

def exportar(nombre, headers, filas):
    # CSV
    csv_path = os.path.join(EXPORT_DIR, f'{nombre}_{fecha_str}.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(filas)
    print(f"Exportado a {csv_path}")
    # Excel
    xlsx_path = os.path.join(EXPORT_DIR, f'{nombre}_{fecha_str}.xlsx')
    wb = Workbook()
    ws = wb.active
    ws.title = nombre
    ws.append(headers)
    for fila in filas:
        ws.append(fila)
    wb.save(xlsx_path)
    print(f"Exportado a {xlsx_path}")

exportar('articulos_oficina', ['Nombre', 'Descripción', 'Imagen'], articulos)
exportar('perifericos_computador', ['Nombre', 'Descripción', 'Imagen'], perifericos)
exportar('unidades_almacenamiento', ['Nombre', 'Descripción', 'Imagen'], almacenamiento)
exportar('motos', ['Modelo', 'Descripción', 'Imagen'], motos)
exportar('coches', ['Modelo', 'Descripción', 'Imagen'], coches)
