# EDF Catálogo de Tablas

Sistema de gestión de catálogos y tablas con interfaz web y aplicación nativa para macOS.

## Características

- Interfaz web responsive
- Aplicación nativa para macOS
- Gestión de usuarios y permisos
- Integración con MongoDB y AWS S3
- Backup a Google Drive

## Documentación

- **[NOTEBOOK.md](./NOTEBOOK.md)** — Características, funcionalidades y mejoras del proyecto
- **[docs/](./docs/)** — Documentación completa (guías, despliegue, seguridad, etc.)

## Inicio rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env  # si existe

# Ejecutar
python run_server.py
```

## Licencia

Este proyecto está bajo la Licencia MIT.
