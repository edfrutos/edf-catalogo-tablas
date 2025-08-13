# 🍎 EDF CatálogoDeTablas - Aplicación macOS

## 📋 Descripción

**EDF CatálogoDeTablas** es una aplicación de escritorio nativa para macOS que proporciona una interfaz completa para la gestión y catalogación de tablas. Esta aplicación está basada en la plataforma web alojada en `edefrutos2025.xyz` y ofrece todas las funcionalidades en un entorno de escritorio optimizado.

## ✨ Características Principales

### 🔐 Gestión de Usuarios
- **Sistema de autenticación completo** con roles de administrador y usuario
- **Gestión de perfiles** con imágenes de perfil personalizables
- **Control de acceso** basado en roles y permisos
- **Sesiones seguras** con Flask-Login

### 📊 Catalogación de Tablas
- **Creación y edición** de catálogos de tablas
- **Gestión de filas y columnas** con interfaz intuitiva
- **Búsqueda y filtrado** avanzado de datos
- **Exportación** a múltiples formatos (CSV, Excel, PDF)
- **Importación** de datos desde archivos externos

### 🛠️ Herramientas de Administración
- **Panel de administración** completo
- **Gestión de usuarios** y permisos
- **Monitoreo del sistema** en tiempo real
- **Herramientas de mantenimiento** y diagnóstico
- **Gestión de logs** y auditoría

### ☁️ Integración en la Nube
- **Backup automático** a Google Drive
- **Sincronización** con Amazon S3 para imágenes
- **Almacenamiento seguro** de credenciales
- **Respaldo incremental** de datos

### 🔧 Funcionalidades Avanzadas
- **Sistema de logging** unificado y configurable
- **Diagnósticos automáticos** del sistema
- **Herramientas de limpieza** y optimización
- **Monitoreo de rendimiento** en tiempo real
- **Gestión de errores** robusta

## 🖥️ Especificaciones Técnicas

### Requisitos del Sistema
- **Sistema Operativo**: macOS 10.13 (High Sierra) o superior
- **Arquitectura**: Intel x64 / Apple Silicon (ARM64)
- **Memoria RAM**: Mínimo 4GB, recomendado 8GB
- **Espacio en Disco**: 500MB para la aplicación + espacio para datos
- **Conexión a Internet**: Requerida para funcionalidades en la nube

### Tecnologías Utilizadas
- **Python**: 3.10.1
- **Flask**: Framework web para la lógica de negocio
- **PyWebView**: Interfaz de escritorio nativa
- **MongoDB**: Base de datos NoSQL
- **PyInstaller**: Empaquetado de la aplicación
- **Google Drive API**: Integración con Google Drive
- **Amazon S3**: Almacenamiento de imágenes
- **Boto3**: SDK de AWS para Python

### Estructura de la Aplicación
```
EDF_CatalogoDeTablas.app/
├── Contents/
│   ├── MacOS/
│   │   └── EDF_CatalogoDeTablas (ejecutable)
│   ├── Resources/
│   │   ├── app/ (aplicación Flask)
│   │   ├── tools/ (herramientas y utilidades)
│   │   ├── backups/ (directorio de respaldos)
│   │   ├── config.py (configuración)
│   │   └── main_app.py (aplicación principal)
│   ├── Frameworks/ (bibliotecas del sistema)
│   └── Info.plist (metadatos de la aplicación)
```

## 🚀 Instalación

### Método 1: Instalación Directa (Recomendado)

1. **Descargar el DMG**
   - Descarga el archivo `EDF_CatalogoDeTablas.dmg`
   - El archivo incluye todo lo necesario para la instalación

2. **Montar el DMG**
   - Haz doble clic en el archivo `.dmg`
   - Se abrirá una ventana con el instalador

3. **Instalar la Aplicación**
   - Arrastra `EDF_CatalogoDeTablas.app` a la carpeta `Aplicaciones`
   - O haz doble clic en el instalador automático

4. **Primera Ejecución**
   - Ve a `Aplicaciones` y haz doble clic en `EDF_CatalogoDeTablas`
   - La primera vez, macOS puede mostrar una advertencia de seguridad
   - Haz clic en "Abrir" para permitir la ejecución

### Método 2: Instalación Manual

1. **Extraer el DMG**
   ```bash
   hdiutil attach EDF_CatalogoDeTablas.dmg
   ```

2. **Copiar la Aplicación**
   ```bash
   cp -R "/Volumes/EDF_CatalogoDeTablas/EDF_CatalogoDeTablas.app" /Applications/
   ```

3. **Desmontar el DMG**
   ```bash
   hdiutil detach "/Volumes/EDF_CatalogoDeTablas"
   ```

### Configuración Inicial

1. **Permisos de Seguridad**
   - Si macOS bloquea la ejecución, ve a:
   - `Preferencias del Sistema` > `Seguridad y Privacidad`
   - Haz clic en "Abrir de todas formas" para `EDF_CatalogoDeTablas`

2. **Configuración de Red**
   - La aplicación requiere conexión a internet para:
     - Conexión a MongoDB Atlas
     - Sincronización con Google Drive
     - Subida de imágenes a Amazon S3

3. **Credenciales Iniciales**
   - **Usuario**: `edefrutos`
   - **Contraseña**: Contacta al administrador del sistema

## 📖 Manual de Uso

### Inicio de Sesión

1. **Abrir la Aplicación**
   - Desde Finder: Doble clic en `EDF_CatalogoDeTablas.app`
   - Desde Terminal: `open /Applications/EDF_CatalogoDeTablas.app`

2. **Pantalla de Login**
   - Ingresa tu nombre de usuario o email
   - Ingresa tu contraseña
   - Haz clic en "Iniciar Sesión"

3. **Panel Principal**
   - Se abrirá la ventana principal de la aplicación
   - Tamaño predeterminado: 1900x1200 píxeles

### Navegación Principal

#### 🏠 Panel de Usuario
- **Dashboard**: Vista general de catálogos y estadísticas
- **Mis Catálogos**: Gestión de catálogos personales
- **Perfil**: Edición de información personal
- **Configuración**: Preferencias del usuario

#### 🔧 Panel de Administración (Solo Administradores)
- **Dashboard Admin**: Estadísticas del sistema
- **Gestión de Usuarios**: Administración de usuarios
- **Mantenimiento**: Herramientas de sistema
- **Backups**: Gestión de respaldos
- **Logs**: Visualización de logs del sistema

### Gestión de Catálogos

#### Crear un Nuevo Catálogo
1. Ve a "Crear Catálogo" en el menú principal
2. Completa la información básica:
   - Nombre del catálogo
   - Descripción
   - Categoría
3. Haz clic en "Crear"

#### Agregar Filas y Columnas
1. Selecciona el catálogo
2. Haz clic en "Agregar Fila" o "Agregar Columna"
3. Completa la información requerida
4. Guarda los cambios

#### Editar Datos
1. Haz doble clic en cualquier celda
2. Modifica el contenido
3. Presiona Enter o haz clic fuera para guardar

### Funciones Avanzadas

#### Exportación de Datos
1. Selecciona el catálogo
2. Haz clic en "Exportar"
3. Elige el formato:
   - **CSV**: Para Excel o análisis de datos
   - **Excel**: Formato nativo de Microsoft Excel
   - **PDF**: Para impresión o archivo

#### Importación de Datos
1. Ve a "Importar" en el menú del catálogo
2. Selecciona el archivo (CSV o Excel)
3. Mapea las columnas
4. Confirma la importación

#### Búsqueda y Filtros
1. Usa la barra de búsqueda en la parte superior
2. Aplica filtros por:
   - Fecha de creación
   - Categoría
   - Usuario creador
   - Estado del catálogo

### Herramientas de Administración

#### Gestión de Usuarios
1. Ve al Panel de Administración
2. Selecciona "Gestión de Usuarios"
3. Funciones disponibles:
   - Crear nuevos usuarios
   - Editar permisos
   - Desactivar usuarios
   - Exportar lista de usuarios

#### Sistema de Backups
1. Ve a "Mantenimiento" > "Backups"
2. Opciones disponibles:
   - **Backup Manual**: Crear respaldo inmediato
   - **Backup Automático**: Programar respaldos
   - **Google Drive**: Sincronizar con la nube
   - **Restaurar**: Recuperar desde respaldo

#### Monitoreo del Sistema
1. Ve a "Mantenimiento" > "Dashboard"
2. Información disponible:
   - Estado de la base de datos
   - Uso de memoria y CPU
   - Espacio en disco
   - Logs del sistema

## 🔧 Solución de Problemas

### La Aplicación No Se Abre

#### Problema: "No se puede abrir porque no es de un desarrollador identificado"
**Solución:**
1. Ve a `Preferencias del Sistema` > `Seguridad y Privacidad`
2. Haz clic en "Abrir de todas formas"
3. Confirma la acción

#### Problema: La aplicación se cierra inmediatamente
**Solución:**
1. Abre Terminal
2. Ejecuta: `/Applications/EDF_CatalogoDeTablas.app/Contents/MacOS/EDF_CatalogoDeTablas`
3. Revisa los mensajes de error

### Problemas de Conexión

#### Error: "No se puede conectar a la base de datos"
**Solución:**
1. Verifica tu conexión a internet
2. Contacta al administrador del sistema
3. Revisa la configuración de red

#### Error: "Error de autenticación con Google Drive"
**Solución:**
1. Verifica que las credenciales estén configuradas
2. Contacta al administrador para renovar credenciales
3. Revisa los permisos de Google Drive

### Problemas de Rendimiento

#### La aplicación está lenta
**Solución:**
1. Cierra otras aplicaciones pesadas
2. Reinicia la aplicación
3. Verifica el espacio disponible en disco

#### Error de memoria
**Solución:**
1. Reinicia la aplicación
2. Cierra otros programas
3. Reinicia el Mac si es necesario

## 📞 Soporte Técnico

### Contacto
- **Email**: soporte@edefrutos2025.xyz
- **Sitio Web**: https://edefrutos2025.xyz
- **Documentación**: Disponible en el panel de administración

### Información de Diagnóstico
Para reportar problemas, incluye:
1. **Versión de macOS**: `Acerca de este Mac`
2. **Versión de la aplicación**: Panel de administración
3. **Logs de error**: Disponibles en el panel de mantenimiento
4. **Descripción del problema**: Pasos para reproducir

## 🔄 Actualizaciones

### Actualización Automática
- La aplicación verifica actualizaciones automáticamente
- Las notificaciones aparecen en el panel de administración
- Las actualizaciones se descargan e instalan automáticamente

### Actualización Manual
1. Descarga la nueva versión desde el sitio web
2. Reemplaza la aplicación existente
3. Reinicia la aplicación

## 📄 Licencia

Esta aplicación es propiedad de EDFrutos y está protegida por derechos de autor.
Para uso comercial, contacta a: licencias@edefrutos2025.xyz

## 🗓️ Historial de Versiones

### v1.0.0 (2025-08-13)
- ✅ Lanzamiento inicial
- ✅ Funcionalidades completas de catalogación
- ✅ Integración con Google Drive y Amazon S3
- ✅ Panel de administración completo
- ✅ Sistema de usuarios y permisos
- ✅ Herramientas de mantenimiento y diagnóstico

---

**© 2025 EDFrutos. Todos los derechos reservados.**
