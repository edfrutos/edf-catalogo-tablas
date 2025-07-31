# 📦 Catálogo de Tablas - Aplicación Flask

Aplicación web desarrollada en **Python + Flask** para la **gestión de catálogos**, con soporte de:
- 🔒 Autenticación de usuarios
- 📄 Gestión de archivos Excel
- 🖼️ Subida y gestión de imágenes (integración con AWS S3)
- 📧 Recuperación de contraseñas por correo electrónico
- 📈 Administración de usuarios (con 2FA opcional)
- 🛡️ Seguridad mejorada y control de errores

---

## 🚀 Requisitos Previos

- Python 3.8 o superior
- MongoDB Atlas configurado (URI en `.env`)
- AWS S3 Bucket (para almacenamiento de imágenes)
- Servidor web (Ubuntu + Apache + Gunicorn, como en producción)

---

## ⚙️ Configuración Rápida

### 1. Clona el proyecto y crea un entorno virtual

```bash
git clone https://tu-repo.git
cd httpdocs
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Variables de entorno

Copia el archivo `.env` de ejemplo o crea uno:

```env
# Flask
FLASK_SECRET_KEY=tu_clave_secreta
FLASK_ENV=production
FLASK_DEBUG=False

# MongoDB
MONGO_URI=tu_mongo_uri

# Correo
MAIL_SERVER=smtp.tuservidor.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_email
MAIL_PASSWORD=tu_contraseña
MAIL_DEFAULT_SENDER_NAME=Administrador
MAIL_DEFAULT_SENDER_EMAIL=tu_email

# AWS S3
AWS_ACCESS_KEY_ID=tu_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=eu-central-1
S3_BUCKET_NAME=nombre_bucket
```

---

### 3. Inicializar carpetas necesarias

```bash
mkdir -p app/static/css app/static/img app/static/js app/static/uploads spreadsheets imagenes_subidas instance
touch app/static/css/.gitkeep app/static/img/.gitkeep app/static/js/.gitkeep app/static/uploads/.gitkeep spreadsheets/.gitkeep imagenes_subidas/.gitkeep instance/.gitkeep
```

---

### 4. Ejecutar en modo desarrollo

```bash
flask --app run.py run --host=0.0.0.0 --port=8000
```

---

### 5. Configurar Gunicorn + Systemd (producción)

Archivo `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for edefrutos2025.xyz
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/edefrutos2025.xyz/httpdocs
Environment="PATH=/.venv/bin"
ExecStart=/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 run:app

[Install]
WantedBy=multi-user.target
```

Comandos:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn
```

---

## 📂 Estructura del Proyecto

```plaintext
app/
├── __init__.py
├── config.py
├── utils.py
├── models.py
├── auth_routes.py
├── main_routes.py
├── tables_routes.py
├── catalog_routes.py
├── static/
│   ├── css/
│   ├── img/
│   ├── js/
│   └── uploads/
├── templates/
│   └── (plantillas html)
spreadsheets/
imagenes_subidas/
instance/
run.py
.env
requirements.txt
README.md
```

---

## 🛡️ Seguridad y buenas prácticas

- Variables críticas validadas automáticamente al inicio.
- Manejo de errores y logs detallados.
- URLs firmadas para acceso seguro a imágenes de S3.
- Acceso a MongoDB con certificados TLS verificados (`certifi`).
- Sesiones Flask protegidas por claves secretas.
- Separación completa de configuración, rutas y lógica de negocio.

---

> ✨ Proyecto diseñado para ser **escalable, seguro y mantenible**.

---
