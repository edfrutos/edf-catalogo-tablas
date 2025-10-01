#!/bin/bash

# =====================================
# VERIFICADOR SIMPLE DE ARCHIVO .env
# =====================================

echo "🔍 VERIFICADOR SIMPLE DE ARCHIVO .env"
echo "====================================="

# Verificar existencia
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

echo "✅ Archivo .env encontrado"
echo ""

# Variables críticas a verificar
echo "📋 VERIFICANDO VARIABLES CRÍTICAS:"
echo "-----------------------------------"

# Función para verificar variable
check_var() {
    local var_name="$1"
    local var_desc="$2"
    local show_value="$3"
    
    if grep -q "^${var_name}=" .env; then
        if [ "$show_value" = "show" ]; then
            local value=$(grep "^${var_name}=" .env | cut -d'=' -f2-)
            echo "✅ $var_name: $value"
        else
            local value=$(grep "^${var_name}=" .env | cut -d'=' -f2- | cut -c1-10)
            echo "✅ $var_name: ${value}...***"
        fi
    else
        echo "❌ $var_name: NO DEFINIDA"
    fi
}

# Verificar variables
check_var "SECRET_KEY" "Clave secreta Flask" "hide"
check_var "MONGO_URI" "URI MongoDB" "show"
check_var "BREVO_SMTP_USERNAME" "Usuario SMTP" "show"
check_var "BREVO_SMTP_PASSWORD" "Password SMTP" "hide"
check_var "NOTIFICATION_EMAIL_1" "Email notificación 1" "show"
check_var "NOTIFICATION_EMAIL_2" "Email notificación 2" "show"

echo ""
echo "🚨 VERIFICACIÓN DE SEGURIDAD:"
echo "-----------------------------"

# Verificar SECRET_KEY por defecto
if grep -q "clave-secreta-super-segura" .env; then
    echo "⚠️  SECRET_KEY usando valor por defecto"
else
    echo "✅ SECRET_KEY personalizada"
fi

# Verificar password comprometida
if grep -q "Rmp3UXwsIkvA0c1d" .env; then
    echo "🚨 BREVO_SMTP_PASSWORD usando credencial comprometida"
else
    echo "✅ BREVO_SMTP_PASSWORD actualizada"
fi

# Verificar API key placeholder
if grep -q "tu-nueva-brevo-api-key" .env; then
    echo "⚠️  BREVO_API_KEY necesita configuración"
else
    echo "✅ BREVO_API_KEY configurada"
fi

echo ""
echo "🔐 VERIFICACIÓN DE .gitignore:"
echo "------------------------------"

if grep -q "^\.env$" .gitignore; then
    echo "✅ .env está en .gitignore"
else
    echo "⚠️  .env NO está en .gitignore"
fi

if git status --porcelain | grep -q "\.env"; then
    echo "⚠️  .env aparece en git status (no debería)"
else
    echo "✅ .env no aparece en git status"
fi

echo ""
echo "📊 RESUMEN DEL ARCHIVO .env:"
echo "============================="
echo "📝 Total de líneas: $(wc -l < .env)"
echo "🔧 Variables definidas: $(grep -c "^[A-Z].*=" .env)"
echo "💬 Líneas de comentario: $(grep -c "^#" .env)"
echo "📅 Fecha de modificación: $(stat -c %y .env | cut -d' ' -f1)"

echo ""
echo "✅ Verificación completada"