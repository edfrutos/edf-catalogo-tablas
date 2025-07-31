#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración de Tamaño de Ventana para EDF CatálogoDeTablas
============================================================

Este archivo te permite configurar fácilmente el tamaño de la ventana
de la aplicación sin modificar el código principal.

INSTRUCCIONES DE USO:
1. Modifica los valores ANCHO y ALTO según tus preferencias
2. Ejecuta este archivo para lanzar la aplicación con el tamaño personalizado
3. O importa la configuración en tu aplicación principal

"""

# ===== CONFIGURACIÓN DE TAMAÑO =====
# Modifica estos valores para cambiar el tamaño de la ventana

# Tamaño personalizado (ancho x alto en píxeles)
ANCHO = 1680
ALTO = 1050

# ===== TAMAÑOS PREDEFINIDOS =====
# Descomenta el tamaño que prefieras y comenta los demás

# Pequeño - ideal para pantallas pequeñas
# ANCHO, ALTO = 800, 600

# Mediano - tamaño estándar (predeterminado)
# ANCHO, ALTO = 1024, 768

# Grande - para pantallas medianas
# ANCHO, ALTO = 1280, 800

# Extra Grande - para pantallas grandes
# ANCHO, ALTO = 1440, 900

# Pantalla completa HD - para monitores Full HD
# ANCHO, ALTO = 1920, 1080

# Pantalla completa 4K - para monitores 4K (ajustado)
# ANCHO, ALTO = 1600, 1200

# ===== CONFIGURACIONES ESPECIALES =====

# Formato 16:9 (widescreen)
# ANCHO, ALTO = 1366, 768  # HD Ready
# ANCHO, ALTO = 1600, 900  # HD+
# ANCHO, ALTO = 1920, 1080 # Full HD

# Formato 4:3 (clásico)
# ANCHO, ALTO = 1024, 768  # XGA
# ANCHO, ALTO = 1280, 960  # SXGA-
# ANCHO, ALTO = 1400, 1050 # SXGA+

# Formato 16:10 (pantallas profesionales)
# ANCHO, ALTO = 1280, 800  # WXGA
# ANCHO, ALTO = 1440, 900  # WXGA+
# ANCHO, ALTO = 1680, 1050 # WSXGA+

def obtener_configuracion():
    """
    Retorna la configuración actual de tamaño de ventana.
    
    Returns:
        tuple: (ancho, alto) en píxeles
    """
    return ANCHO, ALTO

def validar_tamaño(ancho, alto):
    """
    Valida que el tamaño esté dentro de los límites permitidos.
    
    Args:
        ancho (int): Ancho en píxeles
        alto (int): Alto en píxeles
        
    Returns:
        tuple: (ancho, alto) validados y ajustados si es necesario
    """
    # Límites mínimos y máximos
    MIN_ANCHO, MIN_ALTO = 800, 600
    MAX_ANCHO, MAX_ALTO = 2560, 1600
    
    # Ajustar si está fuera de los límites
    ancho_ajustado = max(MIN_ANCHO, min(ancho, MAX_ANCHO))
    alto_ajustado = max(MIN_ALTO, min(alto, MAX_ALTO))
    
    if ancho != ancho_ajustado or alto != alto_ajustado:
        print(f"⚠️  Tamaño ajustado de {ancho}x{alto} a {ancho_ajustado}x{alto_ajustado}")
        print(f"   Límites: {MIN_ANCHO}x{MIN_ALTO} - {MAX_ANCHO}x{MAX_ALTO}")
    
    return ancho_ajustado, alto_ajustado

def mostrar_configuracion():
    """Muestra la configuración actual de tamaño."""
    ancho, alto = obtener_configuracion()
    ancho_val, alto_val = validar_tamaño(ancho, alto)
    
    print("=" * 50)
    print("CONFIGURACIÓN DE TAMAÑO DE VENTANA")
    print("=" * 50)
    print(f"Tamaño configurado: {ancho} x {alto} píxeles")
    print(f"Tamaño validado:    {ancho_val} x {alto_val} píxeles")
    print(f"Relación de aspecto: {ancho_val/alto_val:.2f}:1")
    
    # Determinar el tipo de formato
    ratio = ancho_val / alto_val
    if abs(ratio - 16/9) < 0.1:
        formato = "16:9 (Widescreen)"
    elif abs(ratio - 4/3) < 0.1:
        formato = "4:3 (Clásico)"
    elif abs(ratio - 16/10) < 0.1:
        formato = "16:10 (Profesional)"
    else:
        formato = "Personalizado"
    
    print(f"Formato detectado:  {formato}")
    print("=" * 50)

if __name__ == "__main__":
    # Mostrar la configuración actual
    mostrar_configuracion()
    
    # Intentar lanzar la aplicación con la configuración
    try:
        from ventana_edf_catalogodetablas import CatalogoTablasWindow
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # Obtener y validar el tamaño
        ancho, alto = obtener_configuracion()
        ancho_val, alto_val = validar_tamaño(ancho, alto)
        
        # Crear la aplicación
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Crear la ventana con el tamaño personalizado
        print(f"\n🚀 Iniciando aplicación con tamaño {ancho_val}x{alto_val}...")
        window = CatalogoTablasWindow(ancho_val, alto_val)
        window.show()
        
        # Ejecutar la aplicación
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"\n❌ Error: No se pudo importar la aplicación principal.")
        print(f"   Asegúrate de que 'ventana_edf_catalogodetablas.py' esté en el mismo directorio.")
        print(f"   Error técnico: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
