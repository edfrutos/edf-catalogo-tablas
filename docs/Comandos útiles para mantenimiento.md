$ bash

# Ver uso de recursos
htop
free -h
df -h

# Ver servicios activos
sudo systemctl status apache2
sudo systemctl status plesk-php83-fpm
sudo systemctl status edefrutos2025
sudo systemctl status nginx

# Ver logs recientes
sudo tail -n 40 /var/log/apache2/error.log
sudo tail -n 40 /var/log/nginx/error.log
sudo journalctl -u edefrutos2025 -n 40

# Reiniciar servicios
sudo systemctl reload apache2
sudo systemctl reload nginx
sudo systemctl restart plesk-php83-fpm
sudo systemctl restart edefrutos2025

# Actualizar sistema
sudo apt update && sudo apt upgrade

# Ver procesos que más consumen
ps aux --sort=-%mem | head -n 20