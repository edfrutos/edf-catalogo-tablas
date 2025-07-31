#!/bin/bash

# Script de mantenimiento para edefrutos2025.xyz
# Este script:
# 1. Corrige permisos de directorios y archivos
# 2. Realiza copias de seguridad de los archivos importantes

# Configuración
APP_DIR="/var/www/vhosts/edefrutos2025.xyz/httpdocs"
BACKUP_DIR="${APP_DIR}/backups"
DATE=$(date +%Y-%m-%d)

# Crear directorio de copias de seguridad si no existe
mkdir -p "${BACKUP_DIR}"

# 1. Asegurar permisos correctos
echo "Corrigiendo permisos..."
# Directorios
find "${APP_DIR}/spreadsheets" "${APP_DIR}/imagenes_subidas" -type d -exec chmod 775 {} \;
find "${APP_DIR}/spreadsheets" "${APP_DIR}/imagenes_subidas" -exec chown edefrutos2025:www-data {} \;

# Archivos Excel
find "${APP_DIR}/spreadsheets" -name "*.xlsx" -type f -exec chmod 664 {} \;

# 2. Realizar copias de seguridad
echo "Realizando copias de seguridad..."
tar -czf "${BACKUP_DIR}/spreadsheets_${DATE}.tar.gz" -C "${APP_DIR}" spreadsheets
tar -czf "${BACKUP_DIR}/imagenes_${DATE}.tar.gz" -C "${APP_DIR}" imagenes_subidas

# Mantenimiento de copias: mantener solo las últimas 7
find "${BACKUP_DIR}" -name "spreadsheets_*.tar.gz" -type f -mtime +7 -delete
find "${BACKUP_DIR}" -name "imagenes_*.tar.gz" -type f -mtime +7 -delete

# Corregir permisos de las copias de seguridad
chmod 640 "${BACKUP_DIR}"/*.tar.gz
chown edefrutos2025:www-data "${BACKUP_DIR}"/*.tar.gz

echo "Mantenimiento completado: $(date)"
