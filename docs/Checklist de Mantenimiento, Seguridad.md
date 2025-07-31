# Checklist de Mantenimiento, Seguridad y Backups

## 1. Actualización del sistema y servicios
sudo apt update && sudo apt upgrade -y
sudo apt install --only-upgrade nginx apache2 php
source /.venv/bin/activate
pip install --upgrade pip
pip list --outdated
pip install --upgrade <paquete>

## 2. Firewall
sudo ufw status
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

## 3. Servicios
sudo systemctl status apache2
sudo systemctl status nginx
sudo systemctl status edefrutos2025
sudo systemctl status plesk-php83-fpm
sudo systemctl restart apache2
sudo systemctl restart nginx
sudo systemctl restart edefrutos2025
sudo systemctl restart plesk-php83-fpm

## 4. Backups
# Backup de todo el servidor (Plesk)
# Plesk > Herramientas y configuración > Administrador de backups > Crear backup completo
# Backup manual de un dominio WordPress
sudo tar czvf /root/backup-edefrutos.me-$(date +%F).tar.gz /var/www/vhosts/edefrutos.me/
mysqldump -u USUARIO -p NOMBRE_BD > /root/edefrutos.me-$(date +%F).sql
# Backup manual de la app Flask
sudo tar czvf /root/backup-edefrutos2025-$(date +%F).tar.gz /
# MongoDB Atlas: desde el panel web o usando mongodump si tienes acceso

## 5. Seguridad WordPress
# Instala y configura Wordfence o iThemes Security
# Cambia la URL de login con WPS Hide Login
# Añade en wp-config.php:
define('DISALLOW_FILE_EDIT', true);
# Revisa permisos:
find /var/www/vhosts/DOMINIO/ -type d -exec chmod 755 {} \;
find /var/www/vhosts/DOMINIO/ -type f -exec chmod 644 {} \;

## 6. Comprobación de puertos y procesos
sudo netstat -tulnp | grep LISTEN
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

## 7. Logs de errores
# Apache
tail -f /var/log/apache2/error.log
# Nginx
tail -f /var/log/nginx/error.log
# Gunicorn (Flask)
journalctl -u edefrutos2025 -f
# Plesk
tail -f /var/log/plesk/panel.log

---

# Documento Resumen para Administrar tu Servidor

## 1. Actualización y Mantenimiento
- Actualiza el sistema y los servicios web regularmente.
- Mantén actualizados los plugins y temas de WordPress.
- Actualiza dependencias Python en tu entorno virtual.

## 2. Seguridad
- Usa firewall y permite solo los puertos necesarios.
- Usa contraseñas fuertes y 2FA en WordPress y Plesk.
- Instala plugins de seguridad en WordPress.
- Desactiva la edición de archivos desde el panel de WordPress.
- Revisa y corrige los permisos de archivos y carpetas.

## 3. Backups
- Programa backups automáticos desde Plesk (servidor completo o por dominio).
- Haz backups manuales antes de cambios importantes.
- Guarda los backups en una ubicación externa si es posible.

## 4. Monitorización
- Revisa el estado de los servicios con systemctl status.
- Consulta los logs de errores tras cualquier problema.
- Usa herramientas como htop o top para monitorizar recursos.

## 5. WordPress
- Mantén todo actualizado.
- Elimina plugins y temas que no uses.
- Limita los intentos de login.
- Usa plugins de caché para mejorar el rendimiento.

## 6. Flask/Python
- Usa entornos virtuales.
- No ejecutes la app como root.
- Mantén el código y dependencias actualizados.
- Haz backup de la base de datos y del código.

## 7. Plesk
- No edites manualmente los archivos de configuración generados por Plesk.
- Usa el panel para cambios siempre que sea posible.
- Si hay problemas, reconfigura dominios con:
sudo /usr/local/psa/admin/sbin/httpdmng --reconfigure-domain NOMBRE_DOMINIO 