#!/bin/bash

# =====================================
# SCRIPT DE RESTAURACIÓN COMPLETA
# Información Sensible Recuperada
# =====================================

set -e

echo "🔄 INICIANDO RESTAURACIÓN DE INFORMACIÓN SENSIBLE"
echo "================================================="

# Crear directorios necesarios
mkdir -p .github/workflows
mkdir -p tools/db_utils
mkdir -p tools/production/db_utils
mkdir -p app_data

echo "📁 Directorios creados exitosamente"

# =====================================
# 1. RESTAURAR SCRIPT setup-credentials.sh
# =====================================

echo "🔧 Restaurando setup-credentials.sh..."

cat > .github/workflows/setup-credentials.sh << 'EOF'
#!/bin/bash

# Script para configurar credenciales en GitHub Actions
# Este script se ejecuta en el workflow de construcción

set -e

echo "🔐 Configurando credenciales para GitHub Actions..."

# Crear directorios necesarios
mkdir -p tools/db_utils
mkdir -p tools/production/db_utils

# Verificar si las credenciales están disponibles como secrets
if [ -n "$GOOGLE_CREDENTIALS" ]; then
    echo "📝 Configurando credenciales de Google Drive..."
    echo "$GOOGLE_CREDENTIALS" > tools/db_utils/credentials.json
    echo "$GOOGLE_CREDENTIALS" > tools/production/db_utils/credentials.json
    echo "✅ Credenciales de Google Drive configuradas"
else
    echo "⚠️  No se encontraron credenciales de Google Drive"
    # Crear archivo de ejemplo
    cat > tools/db_utils/credentials.json.example << 'EOF2'
{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost:8080/"]
  }
}
EOF2
    echo "📝 Archivo de ejemplo creado: tools/db_utils/credentials.json.example"
fi

# Verificar si el token está disponible
if [ -n "$GOOGLE_TOKEN" ]; then
    echo "🔑 Configurando token de Google Drive..."
    echo "$GOOGLE_TOKEN" > tools/db_utils/token.json
    echo "$GOOGLE_TOKEN" > tools/production/db_utils/token.json
    echo "✅ Token de Google Drive configurado"
else
    echo "⚠️  No se encontró token de Google Drive"
    # Crear archivo de ejemplo
    cat > tools/db_utils/token.json.example << 'EOF2'
{
  "token": "your-access-token",
  "refresh_token": "your-refresh-token",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "scopes": ["https://www.googleapis.com/auth/drive"]
}
EOF2
    echo "📝 Archivo de ejemplo creado: tools/db_utils/token.json.example"
fi

# Verificar estructura final
echo "📋 Verificando estructura de credenciales..."
ls -la tools/db_utils/
ls -la tools/production/db_utils/

echo "✅ Configuración de credenciales completada"
EOF

chmod +x .github/workflows/setup-credentials.sh
echo "✅ Script setup-credentials.sh restaurado y ejecutable"

# =====================================
# 2. RESTAURAR CONFIGURACIÓN SMTP/BREVO
# =====================================

echo "📧 Restaurando configuración SMTP/Brevo..."

cat > app_data/edefrutos2025_notifications_config.json.RECOVERED << 'EOF'
{
  "enabled": false,
  "smtp": {
    "server": "smtp-relay.brevo.com",
    "port": 587,
    "username": "admin@edefrutos.me",
    "password": "Rmp3UXwsIkvA0c1dRmp3UXwsIkvA0c1d",
    "use_tls": true
  },
  "recipients": [
    "admin@edefrutos2025.xyz",
    "edfrutos@gmail.com"
  ],
  "thresholds": {
    "cpu": 85,
    "memory": 85,
    "disk": 85,
    "error_rate": 10
  },
  "cooldown_minutes": 60,
  "last_alerts": {}
}
EOF

echo "✅ Configuración SMTP restaurada como .RECOVERED"

# =====================================
# 3. CREAR ARCHIVOS DE CREDENCIALES GOOGLE DRIVE
# =====================================

echo "🗂️ Creando plantillas de credenciales Google Drive..."

cat > tools/db_utils/credentials.json.TEMPLATE << 'EOF'
{
  "installed": {
    "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "tu-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "TU_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:8080/"]
  }
}
EOF

cat > tools/db_utils/token.json.TEMPLATE << 'EOF'
{
  "token": "tu-access-token",
  "refresh_token": "tu-refresh-token",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "TU_CLIENT_SECRET",
  "scopes": ["https://www.googleapis.com/auth/drive"]
}
EOF

# Copiar a production también
cp tools/db_utils/credentials.json.TEMPLATE tools/production/db_utils/
cp tools/db_utils/token.json.TEMPLATE tools/production/db_utils/

echo "✅ Plantillas de Google Drive creadas"

# =====================================
# 4. CREAR ARCHIVO .env TEMPLATE
# =====================================

echo "🌐 Creando template de variables de entorno..."

cat > .env.TEMPLATE << 'EOF'
# =====================================
# VARIABLES DE ENTORNO - TEMPLATE
# =====================================

# Base de datos MongoDB
MONGO_URI=mongodb://localhost:27017/edefrutos2025

# Configuración de aplicación
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-secret-key-super-seguro

# Configuración SMTP/Brevo
BREVO_SMTP_USERNAME=admin@edefrutos.me
BREVO_SMTP_PASSWORD=Rmp3UXwsIkvA0c1dRmp3UXwsIkvA0c1d
BREVO_API_KEY=tu-brevo-api-key

# Emails de notificación
NOTIFICATION_EMAIL_1=admin@edefrutos2025.xyz
NOTIFICATION_EMAIL_2=edfrutos@gmail.com

# Google Drive API (opcional)
GOOGLE_CREDENTIALS_FILE=tools/db_utils/credentials.json
GOOGLE_TOKEN_FILE=tools/db_utils/token.json

# Configuración adicional
APP_NAME=EDF Catálogo de Tablas
APP_VERSION=1.0.0
BUILD_DATE=$(date +%Y%m%d)
EOF

echo "✅ Template .env creado"

# =====================================
# 5. RESUMEN Y SIGUIENTES PASOS
# =====================================

echo ""
echo "🎉 RESTAURACIÓN COMPLETADA"
echo "=========================="
echo ""
echo "📋 ARCHIVOS RESTAURADOS:"
echo "  ✅ .github/workflows/setup-credentials.sh"
echo "  ✅ app_data/edefrutos2025_notifications_config.json.RECOVERED"
echo "  ✅ tools/db_utils/credentials.json.TEMPLATE"
echo "  ✅ tools/db_utils/token.json.TEMPLATE"
echo "  ✅ tools/production/db_utils/ (plantillas)"
echo "  ✅ .env.TEMPLATE"
echo ""
echo "⚠️  IMPORTANTE - SIGUIENTES PASOS:"
echo "  1. Renombrar .RECOVERED y .TEMPLATE a nombres reales"
echo "  2. Actualizar credenciales con valores reales"
echo "  3. Verificar que .gitignore excluye estos archivos"
echo "  4. NO commitear archivos con credenciales reales"
echo ""
echo "🔐 CREDENCIALES ENCONTRADAS:"
echo "  📧 SMTP Username: admin@edefrutos.me"
echo "  🔑 SMTP Password: Rmp3UXwsIkvA0c1dRmp3UXwsIkvA0c1d"
echo "  📮 Email 1: admin@edefrutos2025.xyz"
echo "  📮 Email 2: edfrutos@gmail.com"
echo ""
echo "🚨 RECORDATORIO DE SEGURIDAD:"
echo "  - Cambiar passwords si fueron comprometidos"
echo "  - Usar GitHub Secrets para CI/CD"
echo "  - Verificar .gitignore antes de commit"
echo ""
echo "✅ Restauración completa finalizada"