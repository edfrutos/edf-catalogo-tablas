# Guía de Configuración y Despliegue

## Tabla de Contenidos
1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Configuración de la Base de Datos](#configuración-de-la-base-de-datos)
5. [Variables de Entorno](#variables-de-entorno)
6. [Despliegue en Producción](#despliegue-en-producción)
7. [Mantenimiento](#mantenimiento)
8. [Solución de Problemas](#solución-de-problemas)

## Requisitos del Sistema

- Python 3.8 o superior
- MongoDB 4.4 o superior
- pip (gestor de paquetes de Python)
- Git (para clonar el repositorio)
- Nginx o Apache (opcional, para producción)
- Gunicorn o uWSGI (para producción)

## Configuración del Entorno

1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd edf_catalogotablas
   ```

2. **Crear y activar un entorno virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

## Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Configuración de la Base de Datos

1. **Instalar MongoDB**
   - Sigue las instrucciones oficiales para tu sistema operativo: [MongoDB Installation Guide](https://docs.mongodb.com/manual/installation/)

2. **Crear un usuario administrador**
   ```bash
   mongo
   use admin
   db.createUser({
     user: "adminUser",
     pwd: "contraseñaSegura123",
     roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
   })
   exit
   ```

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Configuración de la aplicación
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_muy_larga_y_compleja

# Configuración de MongoDB
MONGO_URI=mongodb://usuario:contraseña@localhost:27017/nombre_bd?authSource=admin

# Configuración de correo electrónico
MAIL_SERVER=smtp.tudominio.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_correo@tudominio.com
MAIL_PASSWORD=tu_contraseña
MAIL_DEFAULT_SENDER=('Tu Nombre', 'tu_correo@tudominio.com')

# Configuración de AWS S3 (opcional)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-bucket

# Configuración de logs
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## Despliegue en Producción

### Opción 1: Gunicorn + Nginx (Recomendado)

1. **Instalar Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Crear archivo de configuración de Gunicorn** (`gunicorn_config.py`):
   ```python
   bind = '0.0.0.0:5000'
   workers = 4
   worker_class = 'sync'
   timeout = 120
   keepalive = 5
   errorlog = 'gunicorn_error.log'
   accesslog = 'gunicorn_access.log'
   ```

3. **Configurar Nginx**
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com www.tu-dominio.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }

       location /static {
           alias /ruta/a/tu/app/static;
           expires 30d;
       }
   }
   ```

4. **Iniciar la aplicación con Gunicorn**
   ```bash
   gunicorn -c gunicorn_config.py wsgi:app
   ```

### Opción 2: Usando uWSGI + Nginx

1. **Instalar uWSGI**
   ```bash
   pip install uwsgi
   ```

2. **Crear archivo de configuración** (`uwsgi.ini`):
   ```ini
   [uwsgi]
   module = wsgi:app
   master = true
   processes = 5
   socket = tu-app.sock
   chmod-socket = 660
   vacuum = true
   die-on-term = true
   ```

3. **Configurar Nginx**
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com www.tu-dominio.com;

       location / {
           include uwsgi_params;
           uwsgi_pass unix:/ruta/a/tu/app/tu-app.sock;
       }
   }
   ```

## Mantenimiento

### Actualización de la aplicación

1. **Obtener los últimos cambios**
   ```bash
   git pull origin master
   ```

2. **Actualizar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Reiniciar el servidor**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl restart gunicorn  # o uwsgi
   ```

### Copias de seguridad

1. **Base de datos**
   ```bash
   mongodump --uri="mongodb://usuario:contraseña@localhost:27017/nombre_bd" --out=/ruta/de/respaldo
   ```

2. **Archivos de la aplicación**
   ```bash
   tar -czvf app_backup_$(date +%Y%m%d).tar.gz /ruta/de/la/aplicacion
   ```

## Solución de Problemas

### Error: No se puede conectar a MongoDB
- Verifica que el servicio de MongoDB esté en ejecución
- Comprueba que las credenciales en `.env` sean correctas
- Asegúrate de que el firewall permita la conexión al puerto 27017

### Error: No se pueden enviar correos
- Verifica las credenciales SMTP
- Comprueba que el puerto no esté bloqueado por un firewall
- Revisa los logs del servidor de correo

### La aplicación no responde
- Verifica que los procesos de Gunicorn/uWSGI estén en ejecución
- Revisa los logs de error en `gunicorn_error.log` o `uwsgi.log`
- Comprueba el uso de recursos del servidor con `top` o `htop`

### Páginas de error personalizadas
La aplicación incluye páginas de error personalizadas para los códigos 404, 403, 500, etc. Estas se pueden personalizar en el directorio `templates/errors/`.

## Seguridad

- **Nunca** expongas archivos sensibles en el repositorio
- Usa HTTPS en producción
- Mantén las dependencias actualizadas
- Implementa un WAF (Web Application Firewall) para protección adicional
- Configura copias de seguridad automáticas

## Monitoreo

Se recomienda implementar un sistema de monitoreo como:
- Prometheus + Grafana
- New Relic
- Datadog

## Escalabilidad

Para manejar mayor carga, considera:
1. Balanceo de carga con múltiples instancias de Gunicorn
2. Usar un CDN para archivos estáticos
3. Implementar caché con Redis o Memcached
4. Escalar horizontalmente la base de datos MongoDB
