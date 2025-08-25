# Scripts de Build y Launcher - EDF Catálogo de Tablas

## 📁 Archivos Mantenidos

### 🚀 **Launchers (Ejecutores)**

#### `launcher_web.py`
- **Propósito**: Lanza la aplicación web en el navegador
- **Uso**: `python3 launcher_web.py`
- **Funcionalidad**: 
  - Inicia el servidor Flask en puerto 5001
  - Abre automáticamente el navegador
  - Ideal para desarrollo y uso web

#### `launcher_native_websockets.py`
- **Propósito**: Lanza la aplicación nativa de macOS (ventana independiente)
- **Uso**: `python3 launcher_native_websockets.py`
- **Funcionalidad**:
  - Inicia el servidor Flask en puerto 5003
  - Crea una ventana nativa con pywebview
  - **NO abre navegador externo** - ventana independiente
  - Incluye icono personalizado
  - Soporte para WebSockets

### 🔨 **Scripts de Build**

#### `build_all_versions.sh`
- **Propósito**: Menú principal para construir ambas versiones
- **Uso**: `./build_all_versions.sh`
- **Opciones**:
  1. Versión Web (navegador)
  2. Versión Nativa (ventana de escritorio)
  3. Ambas versiones
  4. Salir

#### `build_web_app.sh`
- **Propósito**: Construye la aplicación web empaquetada
- **Uso**: `./build_web_app.sh`
- **Resultado**: `dist/EDF_CatalogoDeTablas_Web/`
- **Características**:
  - Aplicación ejecutable que abre el navegador
  - Incluye todos los archivos necesarios
  - Configuración optimizada para web

#### `build_native_websockets.sh`
- **Propósito**: Construye la aplicación nativa de macOS
- **Uso**: `./build_native_websockets.sh`
- **Resultado**: `dist/EDF_CatalogoDeTablas_Web_Native.app`
- **Características**:
  - Aplicación `.app` nativa de macOS
  - Ventana independiente (sin navegador)
  - Icono personalizado incluido
  - Soporte para WebSockets

### 📦 **Scripts de Distribución**

#### `create_dmg_websockets.sh`
- **Propósito**: Crea el instalador DMG para macOS
- **Uso**: `./create_dmg_websockets.sh`
- **Requisito**: Ejecutar primero `./build_native_websockets.sh`
- **Resultado**: `EDF_CatalogoDeTablas_Web_Native.dmg`

### ⚙️ **Archivos de Configuración**

#### `EDF_CatalogoDeTablas_Native_WebSockets.spec`
- **Propósito**: Configuración de PyInstaller para la aplicación nativa
- **Incluye**: 
  - Icono personalizado
  - Configuración de macOS
  - Dependencias optimizadas

## 🎯 **Flujo de Trabajo Recomendado**

### Para Desarrollo:
```bash
# Aplicación web (navegador)
python3 launcher_web.py

# Aplicación nativa (ventana independiente)
python3 launcher_native_websockets.py
```

### Para Construcción:
```bash
# Construir ambas versiones
./build_all_versions.sh

# O construir individualmente:
./build_web_app.sh          # Solo web
./build_native_websockets.sh # Solo nativa
```

### Para Distribución:
```bash
# 1. Construir la aplicación nativa
./build_native_websockets.sh

# 2. Crear el instalador DMG
./create_dmg_websockets.sh
```

## 🔧 **Diferencias Clave**

### Aplicación Web vs Nativa:

| Característica | Web | Nativa |
|---|---|---|
| **Interfaz** | Navegador | Ventana independiente |
| **Puerto** | 5001 | 5003 |
| **Icono** | No aplica | Personalizado |
| **WebSockets** | Sí | Sí |
| **Distribución** | Ejecutable | .app + DMG |

## ✅ **Archivos Eliminados**

Se eliminaron los siguientes archivos obsoletos o duplicados:
- `launcher_native_improved.py`
- `launcher_native.py`
- `launcher_native_web.py`
- `app_nativa_websockets.py`
- `app_nativa_real.py`
- `EDF_CatalogoDeTablas_Native_Web.spec`
- `EDF_CatalogoDeTablas_Native_Real.spec`
- `EDF_CatalogoDeTablas.spec`
- `build_native_app.sh`
- `build_macos_app.sh`
- `create_dmg.sh`
- `create_dmg_improved.sh`

## 🎉 **Estado Actual**

- ✅ **Aplicación web funcionando** - Navegador automático
- ✅ **Aplicación nativa funcionando** - Ventana independiente
- ✅ **Icono personalizado incluido** - En aplicación nativa
- ✅ **Scripts optimizados** - Sin duplicados
- ✅ **Documentación completa** - Este README
