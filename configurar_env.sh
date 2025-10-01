#!/bin/bash

# =====================================
# SCRIPT DE CONFIGURACIÓN .env
# EDF Catálogo de Tablas
# =====================================

set -e

echo "🔧 CONFIGURADOR DE ARCHIVO .env"
echo "==============================="

ENV_FILE=".env"
ENV_TEMPLATE=".env.TEMPLATE"

# Función para generar SECRET_KEY segura
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Función para verificar MongoDB
check_mongodb() {
    echo "🔍 Verificando conexión MongoDB..."
    if command -v mongosh &> /dev/null; then
        mongosh --eval "db.runCommand('ping')" --quiet 2>/dev/null && echo "✅ MongoDB conectado" || echo "❌ MongoDB no disponible"
    elif command -v mongo &> /dev/null; then
        mongo --eval "db.runCommand('ping')" --quiet 2>/dev/null && echo "✅ MongoDB conectado" || echo "❌ MongoDB no disponible"
    else
        echo "⚠️  MongoDB client no encontrado"
    fi
}

# Verificar si existe .env
if [ -f "$ENV_FILE" ]; then
    echo "✅ Archivo .env encontrado"
    
    # Verificar variables críticas
    echo "🔍 Verificando variables críticas..."
    
    if grep -q "clave-secreta-super-segura-cambiar-en-produccion" "$ENV_FILE"; then
        echo "⚠️  SECRET_KEY usando valor por defecto - DEBE cambiarse"
        echo "💡 Nueva SECRET_KEY sugerida: $(generate_secret_key)"
    else
        echo "✅ SECRET_KEY personalizada"
    fi
    
    if grep -q "Rmp3UXwsIkvA0c1dRmp3UXwsIkvA0c1d" "$ENV_FILE"; then
        echo "🚨 BREVO_SMTP_PASSWORD usando credencial comprometida - CAMBIAR INMEDIATAMENTE"
    else
        echo "✅ BREVO_SMTP_PASSWORD actualizada"
    fi
    
    if grep -q "tu-nueva-brevo-api-key-aqui" "$ENV_FILE"; then
        echo "⚠️  BREVO_API_KEY necesita configuración"
    else
        echo "✅ BREVO_API_KEY configurada"
    fi
    
else
    echo "❌ Archivo .env no encontrado"
    
    if [ -f "$ENV_TEMPLATE" ]; then
        echo "📋 Copiando desde template..."
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        echo "✅ Archivo .env creado desde template"
    else
        echo "❌ Template .env.TEMPLATE tampoco encontrado"
        exit 1
    fi
fi

# Verificar MongoDB
check_mongodb

# Verificar configuración de archivos sensibles
echo ""
echo "🔍 VERIFICANDO ARCHIVOS SENSIBLES:"

# Verificar .gitignore
if grep -q "^\.env$" .gitignore; then
    echo "✅ .env excluido en .gitignore"
else
    echo "⚠️  .env NO está en .gitignore - AGREGAR"
fi

# Verificar archivos de credenciales
if [ -f "tools/db_utils/credentials.json" ]; then
    echo "⚠️  credentials.json presente - verificar que está en .gitignore"
else
    echo "✅ credentials.json no presente (seguro)"
fi

if [ -f "app_data/edefrutos2025_notifications_config.json" ]; then
    echo "⚠️  notifications_config.json presente - verificar contenido"
else
    echo "✅ notifications_config.json no presente"
fi

# Mostrar variables críticas actual
echo ""
echo "📋 VARIABLES CRÍTICAS ACTUALES:"
echo "==============================="

if [ -f "$ENV_FILE" ]; then
    echo "🔐 SECRET_KEY: $(grep "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2 | cut -c1-20)..."
    echo "📧 BREVO_SMTP_USERNAME: $(grep "^BREVO_SMTP_USERNAME=" "$ENV_FILE" | cut -d'=' -f2)"
    echo "🔑 BREVO_SMTP_PASSWORD: $(grep "^BREVO_SMTP_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2 | cut -c1-10)..."
    echo "🌐 MONGO_URI: $(grep "^MONGO_URI=" "$ENV_FILE" | cut -d'=' -f2)"
    echo "📮 NOTIFICATION_EMAIL_1: $(grep "^NOTIFICATION_EMAIL_1=" "$ENV_FILE" | cut -d'=' -f2)"
fi

echo ""
echo "🚨 ACCIONES REQUERIDAS:"
echo "======================"
echo "1. Cambiar BREVO_SMTP_PASSWORD (comprometida)"
echo "2. Generar nueva SECRET_KEY si es necesaria"
echo "3. Configurar BREVO_API_KEY"
echo "4. Verificar MONGO_URI para tu entorno"
echo "5. NO commitear este archivo a Git"

echo ""
echo "💡 COMANDOS ÚTILES:"
echo "=================="
echo "# Generar nueva SECRET_KEY:"
echo "python3 -c \"import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))\""
echo ""
echo "# Verificar variables cargadas:"
echo "python3 -c \"from dotenv import load_dotenv; load_dotenv(); import os; print('MONGO_URI:', os.getenv('MONGO_URI'))\""
echo ""
echo "# Verificar .gitignore:"
echo "git status --ignored | grep .env"

echo ""
echo "✅ Configuración de .env completada"