# Catálogo de Tablas

Aplicación Flask para la gestión de catálogos de tablas con autenticación, gestión de usuarios y almacenamiento en MongoDB.

## 🚀 Características Principales

- **Gestión de Usuarios**: Sistema de autenticación con roles (admin/user)
- **CRUD de Catálogos**: Creación, lectura, actualización y eliminación de catálogos
- **Importación/Exportación**: Soporte para Excel y CSV
- **Almacenamiento**: Imágenes en sistema de archivos local o S3
- **Monitoreo**: Sistema integrado de logging y monitoreo

## 🛠️ Estructura del Proyecto

```
.
├── app/                    # Código principal de la aplicación
│   ├── routes/             # Rutas de la aplicación
│   ├── static/             # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/          # Plantillas HTML
│   └── utils/              # Utilidades de la aplicación
├── config/                 # Archivos de configuración
├── docs/                   # Documentación del proyecto
├── models/                 # Modelos de datos
├── scripts/                # Scripts de utilidad
│   ├── db_utils/          # Utilidades de base de datos
│   ├── hooks/             # Hooks para PyInstaller
│   └── maintenance/       # Scripts de mantenimiento
├── tests/                  # Pruebas automatizadas
│   ├── integration/       # Pruebas de integración
│   └── unit/              # Pruebas unitarias
└── tools/                  # Herramientas de desarrollo
```

## 🚀 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone [url-del-repositorio]
   cd edf_catalogotablas
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   Copiar el archivo `.env.example` a `.env` y configurar según sea necesario.

5. **Iniciar la aplicación**
   ```bash
   python run.py
   ```
   O para producción:
   ```bash
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

## 📦 Dependencias Principales

- **Backend**: Flask, Flask-Login, Flask-PyMongo
- **Base de datos**: PyMongo
- **Autenticación**: bcrypt, Flask-Session
- **Procesamiento de datos**: pandas, openpyxl
- **Despliegue**: gunicorn

## 🧪 Ejecución de Pruebas

Para ejecutar las pruebas unitarias:
```bash
pytest tests/unit/
```

Para pruebas de integración:
```bash
pytest tests/integration/
```

## 📝 Guía de Contribución

1. Haz un fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Agradecimientos

- A todos los contribuyentes que han ayudado a mejorar este proyecto.
- A la comunidad de código abierto por las herramientas y bibliotecas utilizadas.

