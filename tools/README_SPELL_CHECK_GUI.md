# 🎨 Interfaz Gráfica de Spell Check

## 📋 Descripción

La interfaz gráfica de Spell Check es una aplicación de escritorio que integra todos los scripts de gestión de ortografía en una interfaz fácil de usar. Permite ejecutar todas las funciones de spell check con un solo clic.

## 🚀 Cómo Usar

### Lanzamiento Rápido
```bash
# Desde el directorio raíz del proyecto
./tools/launch_spell_check_gui.sh
```

### Lanzamiento Manual
```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar directamente
python tools/spell_check_gui.py
```

## 🎯 Funciones Disponibles

### 🔍 Verificación Rápida
- **Descripción**: Escanea archivos del proyecto para encontrar palabras desconocidas
- **Uso**: Para revisar cambios recientes o verificar archivos específicos
- **Script**: `tools/quick_spell_check.py`

### ⚙️ Configuración Rápida
- **Descripción**: Configura VS Code, cSpell y PyCharm sin escaneo completo
- **Uso**: Para configuración inicial o cuando solo necesitas configurar herramientas
- **Script**: `tools/quick_setup_spell_check.py`

### 🔄 Workflow Completo
- **Descripción**: Ejecuta el flujo completo de gestión de ortografía
- **Uso**: Para configuración inicial completa del proyecto
- **Script**: `tools/complete_spell_check_workflow.py`

### 📝 Agregar Palabras Comunes
- **Descripción**: Agrega automáticamente palabras técnicas y del proyecto
- **Uso**: Para expandir el diccionario con términos comunes
- **Script**: `tools/add_common_words.py`

### 📊 Agregar Palabras Categorizadas
- **Descripción**: Agrega palabras basadas en resultados de escaneos previos
- **Uso**: Para gestionar palabras desconocidas de forma inteligente
- **Script**: `tools/add_categorized_words.py`

### 🔧 Corregir Problemas
- **Descripción**: Resuelve problemas comunes de configuración
- **Uso**: Cuando hay errores o dependencias faltantes
- **Script**: `tools/fix_spell_check.py`

### 📋 Ver Configuración Actual
- **Descripción**: Muestra el estado actual de todas las configuraciones
- **Uso**: Para revisar qué está configurado y qué no

### 🧹 Limpiar Logs
- **Descripción**: Limpia el área de logs de la interfaz
- **Uso**: Para mantener la interfaz organizada

### ❓ Ayuda
- **Descripción**: Muestra información detallada sobre todas las funciones
- **Uso**: Para aprender cómo usar cada función

## 🖥️ Características de la Interfaz

### Estado en Tiempo Real
- **Indicador de estado**: Muestra si está listo, ejecutando o con error
- **Barra de progreso**: Indica el progreso de las operaciones
- **Configuración actual**: Muestra el estado de los archivos de configuración

### Logs Detallados
- **Área de logs**: Muestra toda la salida de los scripts
- **Timestamps**: Cada mensaje incluye la hora exacta
- **Scroll automático**: Los logs se desplazan automáticamente

### Ejecución Asíncrona
- **Hilos separados**: Los scripts se ejecutan en segundo plano
- **Interfaz responsiva**: La interfaz no se bloquea durante la ejecución
- **Notificaciones**: Mensajes de éxito o error al completar

## 📊 Información de Configuración

La interfaz muestra automáticamente:
- **Palabras en cSpell**: Número de palabras en `pyproject.toml`
- **VS Code**: Estado de `.vscode/settings.json`
- **cSpell**: Estado de `cspell.json`

## 🔧 Requisitos

### Dependencias
- **Python 3.8+**: Para ejecutar los scripts
- **tkinter**: Para la interfaz gráfica (incluido en Python)
- **toml**: Para leer archivos de configuración

### Instalación de Dependencias
```bash
# En macOS
brew install python-tk

# Instalar toml si no está disponible
pip install toml
```

## 🎨 Personalización

### Colores y Estilos
La interfaz usa un tema moderno con:
- **Colores**: Paleta de grises y azules profesionales
- **Fuentes**: Arial para texto general, Consolas para logs
- **Iconos**: Emojis para mejor identificación visual

### Tamaño de Ventana
- **Tamaño por defecto**: 900x700 píxeles
- **Redimensionable**: Se adapta al contenido
- **Centrada**: Se centra automáticamente en la pantalla

## 🚨 Solución de Problemas

### Error: "tkinter no está disponible"
```bash
# En macOS
brew install python-tk

# En Ubuntu/Debian
sudo apt-get install python3-tk

# En CentOS/RHEL
sudo yum install tkinter
```

### Error: "toml no está disponible"
```bash
pip install toml
```

### La interfaz no responde
- Los scripts se ejecutan en hilos separados
- La interfaz debería permanecer responsiva
- Si se bloquea, cierra y vuelve a abrir

### Scripts no se ejecutan
- Verifica que estés en el directorio raíz del proyecto
- Asegúrate de que los scripts existan en `tools/`
- Revisa los logs para ver errores específicos

## 📈 Flujo de Trabajo Recomendado

### Configuración Inicial
1. **Workflow Completo**: Para configuración inicial
2. **Ver Configuración**: Para verificar que todo esté correcto
3. **Agregar Palabras Comunes**: Para expandir el diccionario

### Uso Diario
1. **Verificación Rápida**: Para revisar cambios
2. **Agregar Palabras Categorizadas**: Si hay nuevas palabras desconocidas
3. **Corregir Problemas**: Si hay errores

### Mantenimiento
1. **Ver Configuración**: Para revisar el estado
2. **Limpiar Logs**: Para mantener la interfaz organizada
3. **Ayuda**: Para recordar cómo usar las funciones

## 🎉 Beneficios

- ✅ **Interfaz intuitiva**: No necesitas recordar comandos
- ✅ **Ejecución visual**: Puedes ver el progreso en tiempo real
- ✅ **Gestión centralizada**: Todos los scripts en un solo lugar
- ✅ **Logs detallados**: Información completa de cada operación
- ✅ **Configuración automática**: Se actualiza automáticamente
- ✅ **Manejo de errores**: Mensajes claros cuando algo falla

---

**Desarrollado para EDF Catalogotablas - 2025**
