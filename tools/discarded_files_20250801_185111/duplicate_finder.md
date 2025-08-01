# 📁 Detector de Archivos Duplicados

Esta aplicación te permite detectar archivos duplicados en cualquier directorio y todos sus subdirectorios, con opciones para eliminar o mover los archivos duplicados.

## ✨ Características

- **🔍 Detección completa**: Escanea directorios y todos sus subdirectorios de cualquier nivel
- **🔐 Detección por contenido**: Utiliza hash MD5 para detectar duplicados basándose en el contenido real del archivo
- **🖥️ Interfaz gráfica**: Aplicación con interfaz visual fácil de usar
- **⌨️ Línea de comandos**: Script CLI para uso avanzado y automatización
- **🗂️ Gestión de duplicados**: Opciones para eliminar, mover o abrir ubicación de archivos
- **🎯 Selección inteligente**: Opción para seleccionar automáticamente todos los duplicados excepto el más reciente
- **📊 Estadísticas**: Muestra información sobre espacio desperdiciado y cantidad de duplicados
- **📄 Exportación**: Posibilidad de exportar resultados a JSON

```python
# Ejemplo de uso rápido del detector de duplicados
import os
import subprocess
import sys

def test_duplicate_finder():
    """Función para probar el detector de duplicados"""
    
    # Verificar que los archivos existen
    scripts = [
        'duplicate_finder.py',
        'duplicate_finder_cli.py', 
        'run_duplicate_finder.py'
    ]
    
    print("🔍 Verificando archivos del detector de duplicados...")
    for script in scripts:
        if os.path.exists(script):
            print(f"✅ {script} - Encontrado")
        else:
            print(f"❌ {script} - No encontrado")
    
    print("\n🚀 Para ejecutar la aplicación:")
    print("   python duplicate_finder.py (Interfaz gráfica)")
    print("   python run_duplicate_finder.py (Script interactivo)")
    
# Ejecutar la verificación
test_duplicate_finder()
```

## 📦 Archivos incluidos

1. __`duplicate_finder.py`__ - Aplicación con interfaz gráfica (Tkinter)
2. __`duplicate_finder_cli.py`__ - Versión de línea de comandos
3. __`run_duplicate_finder.py`__ - Script de ejemplo para ejecutar fácilmente

## 🛠️ Instalación

### Requisitos

- Python 3.6 o superior
- tkinter (incluido en la mayoría de instalaciones de Python)

### Configuración

```bash
# Navegar al directorio donde están los scripts
cd tools/

# Hacer ejecutables (Linux/macOS)  
chmod +x duplicate_finder.py
chmod +x duplicate_finder_cli.py
```

```python
# Comando para verificar que Python y tkinter están disponibles
try:
    import tkinter as tk
    import hashlib
    import os
    print("✅ Todos los módulos necesarios están disponibles")
    print(f"✅ Python: {sys.version}")
    print("✅ tkinter: OK")
    print("✅ hashlib: OK") 
    print("✅ os: OK")
    print("\n🎉 ¡Listo para usar el detector de duplicados!")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("💡 Instala los módulos faltantes")
```

## 🚀 Uso

### 🖥️ Interfaz Gráfica (Recomendado para principiantes)

```bash
python duplicate_finder.py
```

**Pasos:**

1. Ejecuta la aplicación
2. Haz clic en "Examinar" para seleccionar el directorio a escanear
3. Presiona "Escanear" para iniciar la búsqueda
4. Revisa los resultados organizados por grupos de duplicados
5. Selecciona los archivos que quieres eliminar o mover
6. Usa los botones de acción para gestionar los duplicados

### ⌨️ Línea de Comandos (Para usuarios avanzados)

```bash
# Uso básico
python duplicate_finder_cli.py /ruta/al/directorio

# Con información detallada  
python duplicate_finder_cli.py /ruta/al/directorio -v

# Exportar a JSON
python duplicate_finder_cli.py /ruta/al/directorio -j duplicados.json

# Modo interactivo para eliminar
python duplicate_finder_cli.py /ruta/al/directorio -i
```

```python
# Ejemplo para ejecutar el script de ejemplo desde el notebook
import subprocess
import os

def run_duplicate_finder_example():
    """Ejecuta el script de ejemplo de forma interactiva"""
    
    if os.path.exists('run_duplicate_finder.py'):
        print("🎯 Ejecutando el script de ejemplo...")
        print("📝 Esto abrirá un menú interactivo")
        
        # Nota: En un notebook real, esto ejecutaría el script
        # subprocess.run(['python', 'run_duplicate_finder.py'])
        
        print("💡 Para ejecutar manualmente, usa:")
        print("   python run_duplicate_finder.py")
    else:
        print("❌ Script no encontrado en el directorio actual")
        print("💡 Asegúrate de estar en el directorio tools/")

# Llamar a la función
run_duplicate_finder_example()
```

## 🏃‍♂️ Inicio Rápido

### Para empezar inmediatamente:

1. **Descarga los archivos** en una carpeta

2. **Ejecuta el script de ejemplo**:

```bash
python run_duplicate_finder.py
```

3. **Selecciona la opción 1** (Interfaz Gráfica) para empezar

4. **Examina** un directorio de prueba

5. **Revisa los resultados** antes de eliminar nada

## 🎯 Casos de Uso Comunes

1. **📥 Limpieza de Descargas**: Eliminar archivos descargados múltiples veces
2. **📸 Organización de Fotos**: Encontrar fotos duplicadas en diferentes carpetas
3. **💾 Liberación de espacio**: Identificar archivos que ocupan espacio innecesario
4. **🔄 Mantenimiento de backups**: Verificar duplicados en copias de seguridad
5. **📄 Organización de documentos**: Limpiar versiones duplicadas de archivos

## 🔒 Características de Seguridad

- **✋ Confirmación antes de eliminar**: Siempre pide confirmación antes de eliminar archivos
- **🔍 Detección por contenido**: No se basa solo en nombres, sino en el contenido real
- **⚠️ Manejo de errores**: Continúa el proceso aunque algunos archivos no se puedan leer
- **💾 Respaldo recomendado**: Se recomienda hacer un respaldo antes de eliminar archivos

---

**¡Disfruta manteniendo tus archivos organizados! 🎉**