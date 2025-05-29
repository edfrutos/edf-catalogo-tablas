# Configuración de Tareas Programadas para clean_images_scheduled.py

Este documento proporciona instrucciones detalladas para configurar el script `clean_images_scheduled.py` como una tarea programada (cron job) tanto en entornos de desarrollo (macOS) como en producción (servidor Ubuntu con Plesk).

## Índice

1. [Descripción General](#descripción-general)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración en macOS](#configuración-en-macos)
4. [Configuración en Ubuntu con Plesk](#configuración-en-ubuntu-con-plesk)
5. [Variables de Entorno](#variables-de-entorno)
6. [Prueba de la Tarea Programada](#prueba-de-la-tarea-programada)
7. [Recomendaciones de Seguridad](#recomendaciones-de-seguridad)
8. [Solución de Problemas](#solución-de-problemas)

## Descripción General

El script `clean_images_scheduled.py` realiza una limpieza automática de imágenes no utilizadas en su aplicación. El script:

1. Se conecta a MongoDB para identificar imágenes referenciadas
2. Compara con los archivos en el directorio de imágenes
3. Elimina o mueve las imágenes que ya no están siendo utilizadas
4. Genera registros (logs) de todas las acciones realizadas

Al configurarlo como una tarea programada, este proceso se ejecutará automáticamente según la frecuencia que usted defina.

## Requisitos Previos

Antes de configurar la tarea programada, asegúrese de que:

1. El script `clean_images_scheduled.py` está ubicado en el directorio raíz de su proyecto
2. Las dependencias de Python están instaladas (`pymongo`, `python-dotenv`, `certifi`)
3. El archivo `.env` está configurado correctamente con sus credenciales de MongoDB
4. El script se puede ejecutar manualmente sin errores: `python3 clean_images_scheduled.py`

## Configuración en macOS

### Paso 1: Verificar Permisos

Asegúrese de que el script tiene permisos de ejecución:

```bash
chmod +x /ruta/completa/a/clean_images_scheduled.py
```

### Paso 2: Crear Archivo de Logs

```bash
mkdir -p ~/logs
touch ~/logs/clean_images_cron.log
```

### Paso 3: Editar el Crontab

Abra el editor de crontab:

```bash
crontab -e
```

Añada la siguiente línea para ejecutar el script semanalmente (cada domingo a las 2:00 AM):

```
0 2 * * 0 cd /ruta/completa/a/su/proyecto && /usr/bin/python3 clean_images_scheduled.py >> ~/logs/clean_images_cron.log 2>&1
```

Para personalizar la frecuencia:
- `0 2 * * 0` - Cada domingo a las 2:00 AM
- `0 0 * * *` - Todos los días a medianoche
- `0 0 1 * *` - El primer día de cada mes

Guarde y cierre el editor (normalmente con `:wq` en vim).

### Paso 4: Verificar la Configuración

Verifique que el cron job se ha creado correctamente:

```bash
crontab -l
```

## Configuración en Ubuntu con Plesk

### Método 1: Usando la Interfaz de Plesk

1. Inicie sesión en el Panel de Control de Plesk.
2. Navegue a "Dominios" y seleccione su dominio.
3. Vaya a "Programador de Tareas" o "Scheduled Tasks".
4. Haga clic en "Añadir Tarea".
5. Configure la tarea:
   - **Ejecutar**: `/usr/bin/python3`
   - **Argumentos**: `/ruta/completa/a/clean_images_scheduled.py`
   - **Directorio de trabajo**: `/ruta/completa/a/su/proyecto`
   - **Ejecutar como**: El usuario del sitio web (normalmente no root)
   - **Calendario**: Configure la frecuencia deseada (ej. semanal)

6. Guarde la tarea.

### Método 2: Usando SSH y Crontab

Si tiene acceso SSH al servidor:

1. Conéctese a su servidor mediante SSH.
2. Abra el editor de crontab:

```bash
crontab -e
```

3. Añada la siguiente línea:

```
0 2 * * 0 cd /ruta/completa/a/su/proyecto && /usr/bin/python3 clean_images_scheduled.py >> /var/log/clean_images_cron.log 2>&1
```

4. Guarde y cierre el editor.

### Método 3: Usando el Archivo de Crontab de Plesk

Si prefiere editar directamente los archivos de configuración:

1. Ubique el archivo de crontab para su usuario:

```bash
/var/spool/cron/crontabs/[nombre_usuario]
```

2. Edite este archivo (necesita permisos de root):

```bash
sudo nano /var/spool/cron/crontabs/[nombre_usuario]
```

3. Añada la línea del cron job (igual que en el Método 2).
4. Guarde y cierre el archivo.
5. Reinicie el servicio cron:

```bash
sudo systemctl restart cron
```

## Variables de Entorno

El script utiliza variables de entorno para su configuración. Asegúrese de que estas variables están disponibles para el cron job.

### Opción 1: Archivo .env

Asegúrese de que su archivo `.env` contiene:

```
MONGO_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=app_catalogojoyero_nueva
UPLOAD_FOLDER=imagenes_subidas
UNUSED_IMAGES_FOLDER=unused_images
# Para activar la eliminación directa en lugar de mover a unused_images
# DELETE_UNUSED=true
# Para configurar una edad mínima (en días) para eliminar archivos
# MIN_AGE_DAYS=30
# Para configurar un correo de notificaciones
# NOTIFICATION_EMAIL=su@email.com
```

### Opción 2: Configurar en el Crontab

Puede definir las variables en la misma línea del crontab:

```
0 2 * * 0 cd /ruta/completa && MONGO_URI="mongodb+srv://usuario:contraseña@cluster.mongodb.net" MONGO_DB="app_catalogojoyero_nueva" /usr/bin/python3 clean_images_scheduled.py >> ~/logs/clean_images_cron.log 2>&1
```

## Prueba de la Tarea Programada

Para verificar que la tarea se ejecutará correctamente:

### En macOS y Ubuntu:

1. Pruebe el script manualmente:

```bash
cd /ruta/completa/a/su/proyecto
python3 clean_images_scheduled.py
```

2. Simule la ejecución del cron con el mismo entorno:

```bash
cd /ruta/completa/a/su/proyecto && python3 clean_images_scheduled.py
```

3. Verifique que los logs se generan correctamente:

```bash
tail -f ~/logs/clean_images_cron.log   # macOS
tail -f /var/log/clean_images_cron.log # Ubuntu
```

### Prueba de tiempo de ejecución

Para una ejecución inmediata como prueba (útil durante la configuración):

```bash
# Ejecutar cada minuto para pruebas
* * * * * cd /ruta/completa/a/su/proyecto && /usr/bin/python3 clean_images_scheduled.py >> ~/logs/clean_images_cron.log 2>&1
```

Recuerde volver a la configuración original después de la prueba.

## Recomendaciones de Seguridad

1. **No use el usuario root**: Configure el cron job para ejecutarse con el usuario del sitio web.

2. **Proteja su archivo .env**:
   ```bash
   chmod 600 /ruta/completa/a/.env
   ```

3. **Limite los permisos del script**:
   ```bash
   chmod 700 /ruta/completa/a/clean_images_scheduled.py
   ```

4. **Use rutas absolutas** en lugar de relativas dentro del script y en la configuración del cron.

5. **Monitoree los logs** regularmente para detectar errores o comportamientos inesperados.

6. **Limite las acciones del script** para evitar eliminar archivos críticos:
   - Use `MIN_AGE_DAYS` para evitar eliminar archivos recientes
   - Configure primero con `DELETE_UNUSED=false` (modo seguro) antes de activar la eliminación definitiva

7. **Configure notificaciones** para recibir alertas sobre el resultado de la ejecución:
   ```
   NOTIFICATION_EMAIL=admin@sudominio.com
   ```

## Solución de Problemas

### Cron no se ejecuta

1. Verifique los permisos:
   ```bash
   ls -la /ruta/completa/a/clean_images_scheduled.py
   ```

2. Verifique las rutas absolutas en la configuración de cron.

3. Verifique el registro de cron:
   ```bash
   grep CRON /var/log/syslog  # Ubuntu
   ```

### Errores en conexión MongoDB

1. Asegúrese de que el paquete `certifi` está instalado:
   ```bash
   pip3 install certifi
   ```

2. Verifique las credenciales en el archivo `.env`

3. Si usa una IP fija en MongoDB Atlas, asegúrese de que la IP del servidor está en la lista blanca.

### Otros errores

Consulte los logs generados para identificar la causa específica:

```bash
tail -n 50 ~/logs/clean_images_cron.log
```

En caso de problemas persistentes, ejecute el script manualmente con un nivel de log más detallado:

```bash
DEBUG=True python3 clean_images_scheduled.py
```

# Configuración de Tareas Programadas para clean_images_scheduled.py

Este documento proporciona instrucciones detalladas para configurar el script `clean_images_scheduled.py` como una tarea programada tanto en entornos de desarrollo (macOS) como en producción (Ubuntu con Plesk).

## Contenido
1. [Preparación del Script](#preparación-del-script)
2. [Configuración en macOS (Desarrollo)](#configuración-en-macos-desarrollo)
3. [Configuración en Ubuntu con Plesk (Producción)](#configuración-en-ubuntu-con-plesk-producción)
4. [Variables de Entorno](#variables-de-entorno)
5. [Permisos Necesarios](#permisos-necesarios)
6. [Verificación y Monitoreo](#verificación-y-monitoreo)
7. [Solución de Problemas](#solución-de-problemas)

## Preparación del Script

Antes de configurar la tarea programada, asegúrate de que el script sea ejecutable:

```bash
# Para ambos entornos (macOS y Ubuntu)
chmod +x clean_images_scheduled.py
```

Realiza una ejecución de prueba para verificar que funciona correctamente:

```bash
python3 clean_images_scheduled.py --dry-run
```

## Configuración en macOS (Desarrollo)

En macOS, usaremos `crontab` para programar la tarea:

### 1. Abrir el Editor de Crontab

```bash
crontab -e
```

### 2. Añadir la Tarea Programada

Agrega la siguiente línea para ejecutar el script semanalmente (por ejemplo, cada domingo a las 2 AM):

```
0 2 * * 0 cd /Users/edefrutos/_Repositorios/edf_catalogo_tablas && /usr/bin/python3 clean_images_scheduled.py >> /Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs/clean_images.log 2>&1
```

Asegúrate de:
- Modificar la ruta según la ubicación de tu repositorio
- Crear el directorio `logs` si no existe:

```bash
mkdir -p /Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs
```

### 3. Verificar la Configuración

Comprueba que el cron job se ha configurado correctamente:

```bash
crontab -l
```

### 4. Configurar launchd (Alternativa a cron en macOS)

macOS también permite usar `launchd` para tareas programadas más robustas:

1. Crea un archivo plist en `~/Library/LaunchAgents/com.catalogo.clean_images.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.catalogo.clean_images</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/edefrutos/_Repositorios/edf_catalogo_tablas/clean_images_scheduled.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/edefrutos/_Repositorios/edf_catalogo_tablas</string>
    <key>StandardOutPath</key>
    <string>/Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs/clean_images.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs/clean_images_error.log</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>MONGODB_URI</key>
        <string>mongodb://localhost:27017/catalogo</string>
    </dict>
</dict>
</plist>
```

2. Carga el job:

```bash
launchctl load ~/Library/LaunchAgents/com.catalogo.clean_images.plist
```

## Configuración en Ubuntu con Plesk (Producción)

### 1. Usando Plesk Panel

La forma más sencilla es usar el panel de control Plesk:

1. Inicia sesión en el panel de Plesk
2. Ve a "Hosting Web" > [Tu dominio] > "Tareas programadas"
3. Haz clic en "Añadir tarea"
4. Configura:
   - **Ejecutar**: Selecciona "Comando PHP" o "Comando"
   - **Comando**: `/usr/bin/python3 /var/www/vhosts/[tu-dominio]/httpdocs/clean_images_scheduled.py`
   - **Planificación**: Selecciona "Personalizada" y configura para ejecutar semanalmente
   - **Enviar resultado por email**: Configura tu dirección de correo si deseas recibir notificaciones

### 2. Configuración Manual vía SSH

Si prefieres configurar manualmente a través de SSH:

1. Conéctate a tu servidor vía SSH
2. Edita el crontab:

```bash
crontab -e
```

3. Añade la siguiente línea:

```
0 2 * * 0 cd /var/www/vhosts/[tu-dominio]/httpdocs && /usr/bin/python3 clean_images_scheduled.py >> /var/www/vhosts/[tu-dominio]/logs/clean_images.log 2>&1
```

### 3. Usando Configuración de Plesk (Expertos)

Para una configuración más avanzada y específica:

1. Crea un archivo de configuración de tarea en `/etc/cron.d/clean_images_[tu-dominio]`:

```
# Limpieza de imágenes para [tu-dominio]
0 2 * * 0 [usuario-plesk] cd /var/www/vhosts/[tu-dominio]/httpdocs && /usr/bin/python3 clean_images_scheduled.py >> /var/www/vhosts/[tu-dominio]/logs/clean_images.log 2>&1
```

2. Establece los permisos correctos:

```bash
chmod 644 /etc/cron.d/clean_images_[tu-dominio]
```

## Variables de Entorno

El script puede configurarse mediante variables de entorno. Hay varias formas de establecerlas:

### 1. Directamente en el Crontab

```
0 2 * * 0 MONGODB_URI=mongodb://localhost:27017/catalogo DELETE_UNUSED=true cd /ruta/proyecto && python3 clean_images_scheduled.py
```

### 2. Archivo .env

Crea un archivo `.env` en el directorio del proyecto:

```
MONGODB_URI=mongodb://localhost:27017/catalogo
S3_BUCKET_NAME=tu-bucket-s3
DELETE_UNUSED=true
SEND_EMAIL_REPORT=true
EMAIL_RECIPIENT=tu@email.com
```

### 3. Variables de Entorno para Producción en Plesk

En producción, es recomendable configurar las variables de entorno a nivel de sistema o de aplicación:

```bash
# Ejecutar como root o usuario con privilegios
echo 'MONGODB_URI=mongodb://usuario:password@localhost:27017/catalogo' >> /etc/environment
echo 'S3_BUCKET_NAME=mi-bucket-produccion' >> /etc/environment
```

O específicamente para el usuario que ejecuta la tarea:

```bash
echo 'export MONGODB_URI=mongodb://usuario:password@localhost:27017/catalogo' >> /home/[usuario-plesk]/.bashrc
echo 'export S3_BUCKET_NAME=mi-bucket-produccion' >> /home/[usuario-plesk]/.bashrc
```

## Permisos Necesarios

### macOS (Desarrollo)

1. Asegúrate de que el usuario tenga permisos de lectura/escritura en:
   - Directorio del proyecto
   - Directorio de logs
   - Directorio `imagenes_subidas`
   - Directorio `unused_images`

```bash
chmod -R 755 /Users/edefrutos/_Repositorios/edf_catalogo_tablas/imagenes_subidas
chmod -R 755 /Users/edefrutos/_Repositorios/edf_catalogo_tablas/unused_images
chmod -R 755 /Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs
```

### Ubuntu con Plesk (Producción)

1. Asegúrate de que el usuario web (típicamente `www-data` o el usuario específico de Plesk) tenga los permisos necesarios:

```bash
# Ajusta [usuario-plesk] según la configuración de tu servidor
chown -R [usuario-plesk]:psaserv /var/www/vhosts/[tu-dominio]/httpdocs/imagenes_subidas
chown -R [usuario-plesk]:psaserv /var/www/vhosts/[tu-dominio]/httpdocs/unused_images
chown -R [usuario-plesk]:psaserv /var/www/vhosts/[tu-dominio]/logs

chmod -R 755 /var/www/vhosts/[tu-dominio]/httpdocs/imagenes_subidas
chmod -R 755 /var/www/vhosts/[tu-dominio]/httpdocs/unused_images
chmod -R 755 /var/www/vhosts/[tu-dominio]/logs
```

2. Permisos para Python y dependencias:

```bash
# Instalar dependencias necesarias
pip3 install pymongo boto3 python-dotenv requests --user [usuario-plesk]
```

## Verificación y Monitoreo

### Ejecución Manual para Prueba

Verifica que todo funcione correctamente con una ejecución manual:

```bash
# Modo prueba (no elimina archivos)
python3 clean_images_scheduled.py --dry-run

# Ejecución normal
python3 clean_images_scheduled.py
```

### Verificar Logs

Después de la primera ejecución programada, revisa los logs:

```bash
# macOS
cat /Users/edefrutos/_Repositorios/edf_catalogo_tablas/logs/clean_images.log

# Ubuntu
cat /var/www/vhosts/[tu-dominio]/logs/clean_images.log
```

### Verificar Estado del Cron

```bash
# macOS
crontab -l

# Ubuntu
grep clean_images /var/log/syslog
```

## Solución de Problemas

### Problemas Comunes en macOS

1. **El cron no se ejecuta**: macOS puede requerir permisos especiales para cron:
   - Ve a Preferencias del Sistema > Seguridad y Privacidad > Privacidad > Acceso Completo al Disco
   - Agrega Terminal o el editor que usaste para configurar crontab

2. **Problemas con PATH**: Usa rutas absolutas para todos los ejecutables y directorios.

### Problemas Comunes en Ubuntu/Plesk

1. **Permisos insuficientes**: Verifica los permisos del script y directorios.

2. **Dependencias faltantes**: Asegúrate de que todas las bibliotecas Python necesarias estén instaladas.

3. **Configuración de MongoDB**: Verifica la cadena de conexión y credenciales.

4. **Logs de Plesk**: Revisa `/var/log/plesk/panel.log` para errores relacionados con tareas programadas.

### Comando para Depuración

Si encuentras problemas, ejecuta el script con el flag de depuración:

```bash
python3 clean_images_scheduled.py --debug
```

---

Este documento cubre la configuración básica y avanzada para ejecutar el script `clean_images_scheduled.py` como una tarea programada. Para necesidades específicas o configuraciones avanzadas, consulta la documentación de cron para tu sistema operativo específico o la documentación de Plesk.

