#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurador de Tamaño de Ventana para EDF CatálogoDeTablas (PyWebView)
========================================================================

Este archivo te permite configurar fácilmente el tamaño de la ventana
de la aplicación y aplicar los cambios automáticamente al launcher.py

INSTRUCCIONES DE USO:
1. Modifica los valores ANCHO y ALTO según tus preferencias
2. Ejecuta este archivo para aplicar los cambios
3. Los valores se ajustarán automáticamente para PyWebView

"""

# ===== CONFIGURACIÓN DE TAMAÑO =====
# Modifica estos valores para cambiar el tamaño de la ventana

# Tamaño personalizado (ancho x alto en píxeles reales deseados)
ANCHO_DESEADO = 1680  # Tamaño real que quieres obtener
ALTO_DESEADO = 1050   # Tamaño real que quieres obtener

# ===== TAMAÑOS PREDEFINIDOS =====
# Descomenta el tamaño que prefieras y comenta los demás

# Pequeño - ideal para pantallas pequeñas
# ANCHO_DESEADO, ALTO_DESEADO = 800, 600

# Mediano - tamaño estándar
# ANCHO_DESEADO, ALTO_DESEADO = 1024, 768

# Grande - para pantallas medianas
# ANCHO_DESEADO, ALTO_DESEADO = 1280, 800

# Extra Grande - para pantallas grandes
# ANCHO_DESEADO, ALTO_DESEADO = 1440, 900

# Pantalla completa HD
# ANCHO_DESEADO, ALTO_DESEADO = 1920, 1080

# Formato 16:10 Profesional (actual)
# ANCHO_DESEADO, ALTO_DESEADO = 1680, 1050

def calcular_tamaño_pywebview(ancho_real, alto_real):
    """
    Calcula el tamaño que hay que configurar en PyWebView
    para obtener el tamaño real deseado.
    
    PyWebView reduce automáticamente el tamaño aproximadamente un 10%
    """
    factor_compensacion = 1.1  # Compensar la reducción del 10%
    ancho_config = int(ancho_real * factor_compensacion)
    alto_config = int(alto_real * factor_compensacion)
    return ancho_config, alto_config

def mostrar_configuracion():
    """Muestra la configuración actual."""
    ancho_config, alto_config = calcular_tamaño_pywebview(ANCHO_DESEADO, ALTO_DESEADO)
    
    print("=" * 60)
    print("CONFIGURACIÓN DE TAMAÑO DE VENTANA")
    print("=" * 60)
    print(f"Tamaño real deseado:    {ANCHO_DESEADO} x {ALTO_DESEADO} píxeles")
    print(f"Tamaño a configurar:    {ancho_config} x {alto_config} píxeles")
    print(f"Relación de aspecto:    {ANCHO_DESEADO/ALTO_DESEADO:.2f}:1")
    
    # Determinar el tipo de formato
    ratio = ANCHO_DESEADO / ALTO_DESEADO
    if abs(ratio - 16/9) < 0.1:
        formato = "16:9 (Widescreen)"
    elif abs(ratio - 4/3) < 0.1:
        formato = "4:3 (Clásico)"
    elif abs(ratio - 16/10) < 0.1:
        formato = "16:10 (Profesional)"
    else:
        formato = "Personalizado"
    
    print(f"Formato detectado:      {formato}")
    print("=" * 60)
    
    return ancho_config, alto_config

def aplicar_configuracion():
    """
    Aplica la configuración al launcher.py
    """
    import re
    
    ancho_config, alto_config = calcular_tamaño_pywebview(ANCHO_DESEADO, ALTO_DESEADO)
    
    try:
        # Leer el contenido actual de launcher.py
        with open('launcher.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Preparar las nuevas líneas de configuración
        nueva_config = f'''        # Configuración de tamaño de ventana
        # Formato configurado para obtener {ANCHO_DESEADO}x{ALTO_DESEADO} píxeles reales
        WINDOW_WIDTH = {ancho_config}   # Resultará en ~{ANCHO_DESEADO} píxeles
        WINDOW_HEIGHT = {alto_config}  # Resultará en ~{ALTO_DESEADO} píxeles
        
        # Factor de escala aproximado de PyWebView:
        # El tamaño real será aproximadamente un 90% del especificado
        # {ancho_config} x {alto_config} -> resultará en aprox. {ANCHO_DESEADO} x {ALTO_DESEADO}
'''
        
        # Buscar y reemplazar la sección de configuración
        patron = r'        # Configuración de tamaño de ventana.*?(?=        window = )'
        nuevo_contenido = re.sub(
            patron, 
            nueva_config,
            contenido,
            flags=re.DOTALL
        )
        
        # Verificar que se hizo el cambio
        if nuevo_contenido == contenido:
            print("❌ No se pudo encontrar la sección de configuración en launcher.py")
            return False
        
        # Guardar los cambios
        with open('launcher.py', 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        
        print("\n✅ Configuración aplicada exitosamente a launcher.py")
        print(f"   La ventana se abrirá con un tamaño de {ANCHO_DESEADO}x{ALTO_DESEADO} píxeles")
        return True
        
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo launcher.py")
        return False
    except Exception as e:
        print(f"❌ Error: No se pudo aplicar la configuración")
        print(f"   Error técnico: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 Configurador de Tamaño de Ventana - EDF CatálogoDeTablas")
    print()
    
    # Mostrar la configuración actual
    mostrar_configuracion()
    
    # Preguntar si aplicar los cambios
    respuesta = input("\n¿Aplicar esta configuración al launcher.py? (s/n): ").lower().strip()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        if aplicar_configuracion():
            print("\n🚀 Para ver los cambios:")
            print("1. Cierra la aplicación si está abierta")
            print("2. Ejecuta la aplicación normalmente")
            print("3. La ventana debería abrirse con el nuevo tamaño")
        else:
            print("\n❌ No se pudieron aplicar los cambios")
    else:
        print("\n⏹️  Configuración cancelada. No se realizaron cambios.")

if __name__ == "__main__":
    main()
