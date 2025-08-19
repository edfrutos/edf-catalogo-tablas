# EDF Catálogo de Tablas - Aplicaciones macOS

Este proyecto incluye **dos versiones** de la aplicación EDF Catálogo de Tablas para macOS:

## 🌐 Versión Web (Navegador)
**Archivo:** `launcher_web.py`

### Características:
- ✅ Se ejecuta como aplicación nativa de macOS
- ✅ Abre automáticamente el navegador web
- ✅ Interfaz web completa (misma que producción)
- ✅ Funciona offline (solo necesita conexión para S3 y MongoDB)
- ✅ Fácil de usar para usuarios familiarizados con navegadores

### Uso:
```bash
# Construir
./build_web_app.sh

# Ejecutar
./dist/EDF_CatalogoDeTablas_Web/EDF_CatalogoDeTablas_Web
```

### Ventajas:
- Interfaz familiar (navegador web)
- Acceso completo a todas las funcionalidades
- Fácil de distribuir y usar
- No requiere conocimientos técnicos

---

## 🖥️ Versión Nativa (Ventana de Escritorio)
**Archivo:** `launcher_native.py`

### Características:
- ✅ Ventana nativa de macOS (como una app tradicional)
- ✅ Sin necesidad de navegador
- ✅ Interfaz integrada en el escritorio
- ✅ Comportamiento nativo (minimizar, maximizar, etc.)
- ✅ Más profesional para entornos corporativos

### Uso:
```bash
# Construir
./build_native_app.sh

# Ejecutar
./dist/EDF_CatalogoDeTablas_Native/EDF_CatalogoDeTablas_Native
```

### Ventajas:
- Aspecto más profesional
- Integración nativa con macOS
- No depende del navegador del usuario
- Mejor experiencia para usuarios finales

---

## 🚀 Constructor Universal

Para construir ambas versiones fácilmente:

```bash
./build_all_versions.sh
```

Este script te permite elegir:
1. **Versión Web** (navegador)
2. **Versión Nativa** (ventana de escritorio)
3. **Ambas versiones**
4. **Salir**

---

## 📋 Comparación de Versiones

| Característica | Versión Web | Versión Nativa |
|----------------|-------------|----------------|
| **Interfaz** | Navegador web | Ventana nativa |
| **Distribución** | Fácil | Fácil |
| **Experiencia** | Familiar | Profesional |
| **Dependencias** | Navegador | Ninguna |
| **Tamaño** | ~200MB | ~250MB |
| **Rendimiento** | Excelente | Excelente |
| **Compatibilidad** | macOS 10.14+ | macOS 10.14+ |

---

## 🎯 Casos de Uso Recomendados

### Versión Web:
- **Usuarios domésticos** que prefieren navegadores
- **Entornos educativos** donde se usan navegadores
- **Pruebas y desarrollo** (más fácil de debuggear)
- **Usuarios que ya conocen la versión web**

### Versión Nativa:
- **Entornos corporativos** que requieren apps nativas
- **Usuarios que prefieren apps tradicionales**
- **Distribución profesional** (se ve más "serio")
- **Usuarios que no quieren usar navegadores**

---

## 🔧 Requisitos Técnicos

### Para ambas versiones:
- macOS 10.14 (Mojave) o superior
- 4GB RAM mínimo (8GB recomendado)
- 500MB espacio en disco
- Conexión a internet (para S3 y MongoDB Atlas)

### Dependencias incluidas:
- Python 3.10 y todas las librerías
- Flask y extensiones
- MongoDB driver
- AWS S3 client
- Todas las utilidades necesarias

---

## 📦 Distribución

### Para usuarios finales:
1. **Versión Web**: Enviar carpeta `EDF_CatalogoDeTablas_Web/`
2. **Versión Nativa**: Enviar carpeta `EDF_CatalogoDeTablas_Native/`

### Instalación:
- Simplemente copiar la carpeta al Mac del usuario
- Ejecutar el archivo principal
- No requiere instalación adicional

---

## 🛠️ Desarrollo

### Modificar la aplicación:
1. Editar archivos en `app/`
2. Reconstruir con el script correspondiente
3. Probar la nueva versión

### Agregar funcionalidades:
- Los cambios se aplican a ambas versiones
- Solo necesitas reconstruir después de cambios

---

## 🆘 Solución de Problemas

### Versión Web no abre navegador:
- Abrir manualmente: `http://localhost:5001`
- Verificar que el puerto 5001 esté libre

### Versión Nativa no inicia:
- Verificar que PyWebView esté instalado
- Ejecutar desde terminal para ver errores

### Problemas de conexión:
- Verificar archivo `.env` con credenciales
- Comprobar conexión a internet
- Verificar acceso a MongoDB Atlas y S3

---

## 📞 Soporte

Para problemas técnicos:
1. Revisar logs en la terminal
2. Verificar requisitos del sistema
3. Comprobar configuración de `.env`
4. Contactar al equipo de desarrollo

---

**¡Ambas versiones ofrecen la misma funcionalidad completa de EDF Catálogo de Tablas!**
