#!/bin/bash
# Ruta: /daily_report.sh

#!/bin/bash

# Configuración
LOG_FILE="/logs/daily_report.log"
EMAIL="edfutos@gmail.com"
HOSTNAME=$(hostname)
DATE=$(date '+%Y-%m-%d')

# Crear informe
echo "Informe diario del servidor $HOSTNAME - $DATE" > $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE
echo "" >> $LOG_FILE

echo "1. Espacio en disco:" >> $LOG_FILE
df -h / >> $LOG_FILE
echo "" >> $LOG_FILE

echo "2. Uso de memoria:" >> $LOG_FILE
free -h >> $LOG_FILE
echo "" >> $LOG_FILE

echo "3. Carga del sistema:" >> $LOG_FILE
uptime >> $LOG_FILE
echo "" >> $LOG_FILE

echo "4. Procesos de la aplicación:" >> $LOG_FILE
ps aux | grep -E 'wsgi|python|gunicorn' | grep -v grep >> $LOG_FILE
echo "" >> $LOG_FILE

echo "5. Últimos errores de Apache:" >> $LOG_FILE
tail -n 20 /var/log/apache2/error.log >> $LOG_FILE
echo "" >> $LOG_FILE

echo "6. Últimos errores de la aplicación:" >> $LOG_FILE
tail -n 20 /logs/wsgi.log >> $LOG_FILE
echo "" >> $LOG_FILE

echo "7. Resumen de reinicio del servicio:" >> $LOG_FILE
grep "reiniciando servicio" /logs/socket_monitor.log | tail -n 10 >> $LOG_FILE
echo "" >> $LOG_FILE

echo "8. Estado de servicios críticos:" >> $LOG_FILE
systemctl status apache2 --no-pager | head -n 3 >> $LOG_FILE
systemctl status wsgi --no-pager | head -n 3 >> $LOG_FILE
echo "" >> $LOG_FILE

echo "9. Conexiones actuales:" >> $LOG_FILE
netstat -tuln | grep -E '80|443|5000' >> $LOG_FILE
echo "" >> $LOG_FILE

echo "10. Intentos de acceso fallidos:" >> $LOG_FILE
grep "Failed password" /var/log/auth.log | tail -n 10 >> $LOG_FILE
echo "" >> $LOG_FILE

# Enviar informe por correo
mail -s "Informe diario del servidor $HOSTNAME - $DATE" $EMAIL < $LOG_FILE

echo "Informe enviado a $EMAIL"