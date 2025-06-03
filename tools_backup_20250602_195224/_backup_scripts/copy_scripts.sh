#!/bin/bash
# Script para copiar todos los scripts .sh y .py al directorio /tools
# Actualizado: 17/05/2025

# Definir directorio de destino
TOOLS_DIR="/tools"
PROJECT_ROOT="/var/www/vhosts/edefrutos2025.xyz/httpdocs"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "Copiando scripts al directorio $TOOLS_DIR..."

# Limpiar el directorio de herramientas (excepto este script)
find "$TOOLS_DIR" -type f -not -name "copy_scripts.sh" -delete

# Crear subdirectorios para organizar los scripts
mkdir -p "$TOOLS_DIR/maintenance"
mkdir -p "$TOOLS_DIR/admin_utils"
mkdir -p "$TOOLS_DIR/app_runners"
mkdir -p "$TOOLS_DIR/aws_utils"
mkdir -p "$TOOLS_DIR/catalog_utils"
mkdir -p "$TOOLS_DIR/db_utils"
mkdir -p "$TOOLS_DIR/image_utils"
mkdir -p "$TOOLS_DIR/monitoring"
mkdir -p "$TOOLS_DIR/password_utils"
mkdir -p "$TOOLS_DIR/session_utils"
mkdir -p "$TOOLS_DIR/root"

# Copiar scripts de cada categoría
echo "Copiando scripts de mantenimiento..."
cp "$SCRIPTS_DIR/maintenance/"*.{sh,py} "$TOOLS_DIR/maintenance/" 2>/dev/null

echo "Copiando scripts de admin_utils..."
cp "$SCRIPTS_DIR/admin_utils/"*.{sh,py} "$TOOLS_DIR/admin_utils/" 2>/dev/null

echo "Copiando scripts de app_runners..."
cp "$SCRIPTS_DIR/app_runners/"*.{sh,py} "$TOOLS_DIR/app_runners/" 2>/dev/null

echo "Copiando scripts de aws_utils..."
cp "$SCRIPTS_DIR/aws_utils/"*.{sh,py} "$TOOLS_DIR/aws_utils/" 2>/dev/null

echo "Copiando scripts de catalog_utils..."
cp "$SCRIPTS_DIR/catalog_utils/"*.{sh,py} "$TOOLS_DIR/catalog_utils/" 2>/dev/null

echo "Copiando scripts de db_utils..."
cp "$SCRIPTS_DIR/db_utils/"*.{sh,py} "$TOOLS_DIR/db_utils/" 2>/dev/null

echo "Copiando scripts de image_utils..."
cp "$SCRIPTS_DIR/image_utils/"*.{sh,py} "$TOOLS_DIR/image_utils/" 2>/dev/null

echo "Copiando scripts de monitoring..."
cp "$SCRIPTS_DIR/monitoring/"*.{sh,py} "$TOOLS_DIR/monitoring/" 2>/dev/null

echo "Copiando scripts de password_utils..."
cp "$SCRIPTS_DIR/password_utils/"*.{sh,py} "$TOOLS_DIR/password_utils/" 2>/dev/null

echo "Copiando scripts de session_utils..."
cp "$SCRIPTS_DIR/session_utils/"*.{sh,py} "$TOOLS_DIR/session_utils/" 2>/dev/null

echo "Copiando scripts de la raíz..."
find "$SCRIPTS_DIR" -maxdepth 1 -type f -name "*.sh" -o -name "*.py" | xargs -I{} cp {} "$TOOLS_DIR/root/" 2>/dev/null

# Establecer permisos de ejecución para todos los scripts
echo "Estableciendo permisos de ejecución..."
find "$TOOLS_DIR" -type f -name "*.sh" -exec chmod +x {} \;
find "$TOOLS_DIR" -type f -name "*.py" -exec chmod +x {} \;

echo "Proceso completado. Los scripts han sido copiados a $TOOLS_DIR"
