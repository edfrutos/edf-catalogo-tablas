# Configuración para modo de desarrollo local

Este documento describe los pasos necesarios para ejecutar la aplicación en modo local para desarrollo.

## 1. Modificar configuración de entorno

Edita el archivo `.env` para cambiar a modo desarrollo:

```
# Cambiar estas líneas
FLASK_ENV=development
FLASK_DEBUG=True
```

## 2. Variables de entorno críticas

Asegúrate de tener todas las variables críticas configuradas en tu archivo `.env`:

- `FLASK_SECRET_KEY` - Clave secreta para Flask (¡Añádela si falta!)
- `MONGO_URI` - URI de conexión a MongoDB
- `MAIL_SERVER` - Servidor de correo SMTP
- `MAIL_PORT` - Puerto del servidor de correo
- `MAIL_USERNAME` - Nombre de usuario del correo
- `MAIL_PASSWORD` - Contraseña del correo
- `MAIL_DEFAULT_SENDER_NAME` - Nombre del remitente por defecto
- `MAIL_DEFAULT_SENDER_EMAIL` - Correo del remitente por defecto

## 3. Instalación de dependencias

Instala las dependencias necesarias en tu entorno local:

```bash
pip install -r requirements.txt
```

## 4. Ejecución de la aplicación

Para iniciar la aplicación en modo desarrollo:

```bash
flask run --host=0.0.0.0 --port=5000
```

O alternativamente:

```bash
python app.py
```

## 5. Consideraciones adicionales

- **MongoDB**: Verifica el acceso a la base de datos MongoDB
- **AWS S3**: Si usas S3, asegúrate de tener las credenciales adecuadas
- **Correo electrónico**: Para pruebas de envío de correos, considera usar una configuración local o servicios como Mailtrap

## 6. Solución de problemas comunes

- Si encuentras errores de importación de módulos, verifica la configuración de `PYTHONPATH`
- Para problemas de permisos con archivos subidos, asegúrate de que las carpetas tengan los permisos adecuados
- Verifica los registros de errores para diagnóstico adicional
