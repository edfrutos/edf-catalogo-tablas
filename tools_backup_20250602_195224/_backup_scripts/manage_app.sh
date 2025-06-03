#!/bin/bash
# Script de mantenimiento para la aplicación Flask

case "$1" in
    start)
        echo "Iniciando servicio Gunicorn..."
        systemctl start gunicorn_edefrutos.service
        ;;
    stop)
        echo "Deteniendo servicio Gunicorn..."
        systemctl stop gunicorn_edefrutos.service
        ;;
    restart)
        echo "Reiniciando servicio Gunicorn..."
        systemctl restart gunicorn_edefrutos.service
        ;;
    status)
        echo "Estado del servicio Gunicorn:"
        systemctl status gunicorn_edefrutos.service
        echo ""
        echo "Procesos de Gunicorn:"
        ps aux | grep gunicorn | grep -v grep
        echo ""
        echo "Puerto 8000:"
        ss -tulpn | grep 8000
        ;;
    logs)
        echo "Últimas 20 líneas de los logs:"
        echo "=== Flask logs ==="
        tail -n 20 /flask_app.log
        echo ""
        echo "=== Systemd logs ==="
        journalctl -u gunicorn_edefrutos.service -n 20
        ;;
    apache)
        echo "Estado de Apache:"
        systemctl status apache2
        echo ""
        echo "Configuración de los sitios:"
        apache2ctl -S
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|apache}"
        exit 1
        ;;
esac

exit 0
