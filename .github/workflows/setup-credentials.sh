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
    cat > tools/db_utils/credentials.json.example << 'EOF'
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
EOF
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
    cat > tools/db_utils/token.json.example << 'EOF'
{
  "token": "your-access-token",
  "refresh_token": "your-refresh-token",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "scopes": ["https://www.googleapis.com/auth/drive"]
}
EOF
    echo "📝 Archivo de ejemplo creado: tools/db_utils/token.json.example"
fi

# Verificar estructura final
echo "📋 Verificando estructura de credenciales..."
ls -la tools/db_utils/
ls -la tools/production/db_utils/

echo "✅ Configuración de credenciales completada"
