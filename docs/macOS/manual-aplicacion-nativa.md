# 🚀 EDF Catálogo de Tablas - Aplicación Nativa de macOS

## 📱 Descripción de la Aplicación

**EDF Catálogo de Tablas** es una aplicación nativa de macOS que permite gestionar catálogos de productos de manera eficiente y profesional. La aplicación está empaquetada como una aplicación de escritorio independiente, sin necesidad de navegador web.

### ✨ Características Principales

- **Aplicación Nativa**: Interfaz de escritorio nativa de macOS
- **Sin Dependencias**: No requiere navegador web externo
- **Gestión de Catálogos**: Crear, editar y gestionar catálogos de productos
- **Sistema de Usuarios**: Autenticación y gestión de usuarios
- **Almacenamiento en la Nube**: Integración con Amazon S3 para imágenes
- **Base de Datos**: MongoDB para almacenamiento de datos
- **Interfaz Moderna**: Diseño responsive y profesional

## 🎯 Requisitos del Sistema

- **macOS**: 10.15 (Catalina) o superior
- **Arquitectura**: Intel o Apple Silicon (M1/M2/M3)
- **Memoria**: Mínimo 4GB RAM (recomendado 8GB)
- **Espacio**: 1GB de espacio libre en disco

## 📦 Instalación

### Opción 1: Instalación Directa
1. Descargar el archivo DMG
2. Hacer doble clic en el archivo DMG para montarlo
3. Arrastrar `EDF_CatalogoDeTablas.app` a la carpeta Aplicaciones
4. Desmontar el DMG
5. Ejecutar desde Launchpad o Spotlight

### Opción 2: Instalación desde Finder
1. Abrir el archivo DMG
2. Hacer doble clic en `EDF_CatalogoDeTablas.app`
3. Confirmar la instalación si macOS solicita permisos

## 🚀 Primeros Pasos

### 1. Iniciar la Aplicación
- Buscar "EDF Catálogo de Tablas" en Spotlight (⌘ + Espacio)
- O navegar a Aplicaciones y hacer doble clic en el icono

### 2. Iniciar Sesión
- **Usuario**: `edefrutos`
- **Contraseña**: [Contactar al administrador]
- La aplicación se conectará automáticamente a la base de datos

### 3. Panel de Administración
Una vez autenticado, tendrás acceso a:
- **Dashboard**: Vista general del sistema
- **Catálogos**: Gestión de catálogos de productos
- **Usuarios**: Administración de usuarios
- **Herramientas**: Utilidades de mantenimiento

## 📋 Funcionalidades Principales

### Gestión de Catálogos
- **Crear Catálogos**: Nuevos catálogos de productos
- **Editar Catálogos**: Modificar información existente
- **Agregar Productos**: Incluir nuevos productos con imágenes
- **Organizar Datos**: Estructurar información de manera eficiente

### Gestión de Imágenes
- **Subir Imágenes**: Carga automática a Amazon S3
- **Optimización**: Redimensionamiento automático
- **Organización**: Categorización por catálogos
- **Visualización**: Vista previa y galería

### Sistema de Usuarios
- **Autenticación**: Login seguro
- **Roles**: Administrador y usuario
- **Permisos**: Control de acceso por funcionalidad
- **Gestión**: Crear y administrar usuarios

## 🛠️ Herramientas de Mantenimiento

### Backup y Restauración
- **Backup Automático**: Respaldo de datos
- **Restauración**: Recuperación de información
- **Exportación**: Exportar datos en diferentes formatos

### Monitoreo del Sistema
- **Estado del Servidor**: Monitoreo en tiempo real
- **Logs**: Registro de actividades
- **Métricas**: Rendimiento del sistema

## 🔧 Configuración Avanzada

### Variables de Entorno
La aplicación utiliza las siguientes configuraciones:
- **MongoDB**: Conexión a base de datos
- **Amazon S3**: Almacenamiento de imágenes
- **Logs**: Directorio de registros

### Directorios de Datos
- **Logs**: `/var/folders/.../edf_catalogo_logs/`
- **Sesiones**: `/var/folders/.../edf_catalogo_logs/flask_session/`
- **Cache**: Almacenamiento temporal automático

## 🆘 Solución de Problemas

### La aplicación no se inicia
1. Verificar que macOS sea 10.15 o superior
2. Comprobar permisos de seguridad en Preferencias del Sistema
3. Reinstalar la aplicación

### Error de conexión
1. Verificar conexión a internet
2. Comprobar configuración de firewall
3. Contactar al administrador del sistema

### Problemas de rendimiento
1. Cerrar otras aplicaciones
2. Reiniciar la aplicación
3. Verificar espacio disponible en disco

## 📞 Soporte Técnico

### Contacto
- **Email**: [Email de soporte]
- **Teléfono**: [Número de soporte]
- **Horario**: Lunes a Viernes, 9:00 - 18:00

### Información del Sistema
- **Versión**: 1.0.0
- **Fecha de Lanzamiento**: Agosto 2025
- **Desarrollador**: EDF Sistemas

## 🔄 Actualizaciones

La aplicación se actualiza automáticamente cuando hay nuevas versiones disponibles. Las actualizaciones incluyen:
- Mejoras de seguridad
- Nuevas funcionalidades
- Corrección de errores
- Optimizaciones de rendimiento

## 📄 Licencia

Esta aplicación está desarrollada para uso interno de EDF Sistemas. Todos los derechos reservados.

---

**EDF Catálogo de Tablas v1.0.0**  
*Desarrollado con ❤️ para la gestión eficiente de catálogos*
