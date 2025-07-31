# ✅ Checklist de Mantenimiento, Seguridad y Backups

## 1. **Actualización del sistema y servicios**

```bash
# Actualiza el sistema (Debian/Ubuntu)
sudo apt update && sudo apt upgrade -y

# Actualiza paquetes específicos (ejemplo: nginx, apache2, php)
sudo apt install --only-upgrade nginx apache2 php

# Actualiza pip y dependencias Python (en tu entorno virtual)
source /.venv/bin/activate
pip install --upgrade pip
pip list --outdated
pip install --upgrade <paquete>
```

---

## 2. **Firewall**

```bash
# Ver reglas activas (UFW)
sudo ufw status

# Permitir puertos web y SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activar firewall
sudo ufw enable
```

---

## 3. **Servicios**

```bash
# Ver estado de servicios
sudo systemctl status apache2
sudo systemctl status nginx
sudo systemctl status edefrutos2025
sudo systemctl status plesk-php83-fpm

# Reiniciar servicios
sudo systemctl restart apache2
sudo systemctl restart nginx
sudo systemctl restart edefrutos2025
sudo systemctl restart plesk-php83-fpm
```

---

## 4. **Backups**

### **Backup de todo el servidor (recomendado)**

- Desde Plesk:  
   **Plesk > Herramientas y configuración > Administrador de backups > Crear backup completo**

### **Backup manual de un dominio WordPress**

```bash
# Archivos
tar czvf /root/backup-edefrutos.me-$(date +%F).tar.gz /var/www/vhosts/edefrutos.me/

# Base de datos (ajusta usuario y base de datos)
mysqldump -u USUARIO -p NOMBRE_BD > /root/edefrutos.me-$(date +%F).sql
```

### **Backup manual de la app Flask**

```bash
# Archivos
tar czvf /root/backup-edefrutos2025-$(date +%F).tar.gz /

# MongoDB Atlas: desde el panel web o usando mongodump si tienes acceso
```

---

## 5. **Seguridad WordPress**

- Instala y configura **Wordfence** o **iThemes Security** desde el panel de plugins.

- Cambia la URL de login con un plugin como **WPS Hide Login**.

- Añade en `wp-config.php`:

```php
define('DISALLOW_FILE_EDIT', true);
```

- Revisa permisos:

```bash
find /var/www/vhosts/DOMINIO/ -type d -exec chmod 755 {} \;
find /var/www/vhosts/DOMINIO/ -type f -exec chmod 644 {} \;
```

---

## 6. **Comprobación de puertos y procesos**

```bash
sudo netstat -tulnp | grep LISTEN
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000
```

---

## 7. **Logs de errores**

```bash
# Apache
tail -f /var/log/apache2/error.log

# Nginx
tail -f /var/log/nginx/error.log

# Gunicorn (Flask)
journalctl -u edefrutos2025 -f

# Plesk
tail -f /var/log/plesk/panel.log
```

---

# 📄 Documento Resumen para Administrar tu Servidor

---

## 1. **Actualización y Mantenimiento**

- Actualiza el sistema y los servicios web regularmente.
- Mantén actualizados los plugins y temas de WordPress.
- Actualiza dependencias Python en tu entorno virtual.

## 2. **Seguridad**

- Usa firewall y permite solo los puertos necesarios.
- Usa contraseñas fuertes y 2FA en WordPress y Plesk.
- Instala plugins de seguridad en WordPress.
- Desactiva la edición de archivos desde el panel de WordPress.
- Revisa y corrige los permisos de archivos y carpetas.

## 3. **Backups**

- Programa backups automáticos desde Plesk (servidor completo o por dominio).
- Haz backups manuales antes de cambios importantes.
- Guarda los backups en una ubicación externa si es posible.

## 4. **Monitorización**

- Revisa el estado de los servicios con `systemctl status`.
- Consulta los logs de errores tras cualquier problema.
- Usa herramientas como `htop` o `top` para monitorizar recursos.

## 5. **WordPress**

- Mantén todo actualizado.
- Elimina plugins y temas que no uses.
- Limita los intentos de login.
- Usa plugins de caché para mejorar el rendimiento.

## 6. **Flask/Python**

- Usa entornos virtuales.
- No ejecutes la app como root.
- Mantén el código y dependencias actualizados.
- Haz backup de la base de datos y del código.

## 7. **Plesk**

- No edites manualmente los archivos de configuración generados por Plesk.

- Usa el panel para cambios siempre que sea posible.

- Si hay problemas, reconfigura dominios con:

```bash
sudo /usr/local/psa/admin/sbin/httpdmng --reconfigure-domain NOMBRE_DOMINIO
```

---

¿Quieres que te prepare este documento en PDF o en un archivo de texto para descargar? ¿O lo prefieres en ambos formatos?  
¡Dímelo y te lo preparo!
