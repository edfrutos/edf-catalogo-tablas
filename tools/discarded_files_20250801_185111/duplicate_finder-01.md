---
runme:
  document:
    relativePath: README_duplicate_finder.md
  session:
    id: 01K0H73XXRVJCWPWVB7663W0EW
    updated: 2025-07-19 18:36:41+02:00
---

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

## 📦 Archivos incluidos

1. **`duplicate_finder.py`** - Aplicación con interfaz gráfica (Tkinter)
2. **`duplicate_finder_cli.py`** - Versión de línea de comandos
3. **`run_duplicate_finder.py`** - Script de ejemplo para ejecutar fácilmente

## 🛠️ Instalación

### Requisitos
- Python 3.6 o superior
- tkinter (incluido en la mayoría de instalaciones de Python)

### Configuración
```bash
# Clonar o descargar los archivos
# Navegar al directorio donde están los scripts
cd /ruta/a/los/scripts

# Hacer ejecutables (Linux/macOS)
chmod +x duplicate_finder.py
chmod +x duplicate_finder_cli.py
```

## 🚀 Uso

### 🖥️ Interfaz Gráfica

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

**Botones disponibles:**
- **🗑️ Eliminar Seleccionados**: Elimina permanentemente los archivos seleccionados
- **📦 Mover Seleccionados**: Mueve los archivos a otro directorio
- **📂 Abrir Ubicación**: Abre el explorador en la ubicación del archivo
- **✅ Seleccionar Todos Excepto Primero**: Selecciona automáticamente todos los duplicados excepto el más reciente de cada grupo
- **❌ Limpiar Selección**: Deselecciona todos los archivos

### ⌨️ Línea de Comandos

```bash
# Uso básico
python duplicate_finder_cli.py /ruta/al/directorio

# Con información detallada
python duplicate_finder_cli.py /ruta/al/directorio -v

# Exportar a JSON
python duplicate_finder_cli.py /ruta/al/directorio -j duplicados.json

# Modo interactivo para eliminar
python duplicate_finder_cli.py /ruta/al/directorio -i

# Combinando opciones
python duplicate_finder_cli.py /ruta/al/directorio -v -j duplicados.json -i
```

**Opciones CLI:**
- `-v, --verbose`: Muestra información detallada durante el proceso
- `-j, --json ARCHIVO`: Exporta los resultados a un archivo JSON
- `-i, --interactive`: Modo interactivo para eliminar duplicados
- `--no-paths`: No muestra las rutas completas en la salida

### 🎮 Modo Interactivo (CLI)

En el modo interactivo puedes:
- `s`: Saltar el grupo actual
- `1`: Mantener solo el archivo más reciente (eliminar los demás)
- `2-N`: Mantener solo el archivo especificado por número
- `m`: Modo manual (preguntar por cada archivo individualmente)

## 📋 Ejemplos de Uso

### Ejemplo 1: Escaneo básico con interfaz gráfica
```bash
python duplicate_finder.py
```

### Ejemplo 2: Escaneo rápido de directorio
```bash
python duplicate_finder_cli.py ~/Documentos
```

### Ejemplo 3: Análisis completo con exportación
```bash
python duplicate_finder_cli.py ~/Descargas -v -j reporte_duplicados.json
```

### Ejemplo 4: Limpieza interactiva
```bash
python duplicate_finder_cli.py ~/Fotos -i
```

### Ejemplo 5: Usar el script de ejemplo (RECOMENDADO)
```bash
python run_duplicate_finder.py
```

## 🔒 Características de Seguridad

- **✋ Confirmación antes de eliminar**: Siempre pide confirmación antes de eliminar archivos
- **🔍 Detección por contenido**: No se basa solo en nombres, sino en el contenido real
- **⚠️ Manejo de errores**: Continúa el proceso aunque algunos archivos no se puedan leer
- **💾 Respaldo recomendado**: Se recomienda hacer un respaldo antes de eliminar archivos

## 💡 Consejos de Uso

1. **🔰 Empezar con directorios pequeños**: Prueba primero con directorios pequeños para familiarizarte
2. **👀 Revisar antes de eliminar**: Siempre revisa la lista antes de eliminar archivos
3. **📅 Mantener archivos recientes**: Por defecto, mantén los archivos más recientes
4. **📄 Usar exportación JSON**: Para análisis posterior o respaldo de decisiones
5. **🎛️ Modo interactivo para control fino**: Usa el modo interactivo cuando necesites control preciso

## 🎯 Casos de Uso Comunes

1. **📥 Limpieza de Descargas**: Eliminar archivos descargados múltiples veces
2. **📸 Organización de Fotos**: Encontrar fotos duplicadas en diferentes carpetas
3. **💾 Liberación de espacio**: Identificar archivos que ocupan espacio innecesario
4. **🔄 Mantenimiento de backups**: Verificar duplicados en copias de seguridad
5. **📄 Organización de documentos**: Limpiar versiones duplicadas de archivos

## 🏃‍♂️ Inicio Rápido

1. **Descarga los archivos** en una carpeta
2. **Ejecuta el script de ejemplo**:
   ```bash
   python run_duplicate_finder.py
   ```
3. **Selecciona la opción 1** (Interfaz Gráfica) para empezar
4. **Examina** un directorio de prueba
5. **Revisa los resultados** antes de eliminar nada

## ⚙️ Notas Técnicas

- **🔐 Algoritmo de hash**: Utiliza MD5 para calcular hashes de archivos
- **⚖️ Comparación**: Solo archivos con el mismo hash se consideran duplicados
- **⚡ Rendimiento**: Procesa archivos en chunks para manejar archivos grandes eficientemente
- **🧵 Multihilo**: La versión GUI utiliza hilos separados para no bloquear la interfaz

## 📄 Licencia

Este proyecto es de uso libre. Puedes modificarlo y distribuirlo según tus necesidades.

---

**¡Disfruta manteniendo tus archivos organizados! 🎉**