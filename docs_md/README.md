# EDF Catálogo de Tablas

Sistema de gestión de catálogos y tablas con interfaz web y aplicación nativa para macOS.

## 🚀 Características

- Interfaz web responsive
- Aplicación nativa para macOS
- Sistema de notificaciones por email
- Gestión de usuarios y permisos
- Backup automático a Google Drive
- Integración con MongoDB

## 🔐 Configuración de Secrets

Los secrets están configurados en GitHub para CI/CD seguro.

## 📦 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/edfrutos/edf_catalogotablas.git
cd edf_catalogotablas

# Instalar dependencias
pip install -r requirements_python310.txt

# Configurar variables de entorno
cp app_data/edefrutos2025_notifications_config.example.json app_data/edefrutos2025_notifications_config.json
# Editar el archivo con tus credenciales

# Ejecutar la aplicación
python run_server.py
```

## 🏗️ Build de Aplicación macOS

```bash
# Build automático via GitHub Actions
# O build local:
./build_native_websockets.sh
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.
