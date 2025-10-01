#!/bin/bash

# =========================================
# ACTUALIZADOR DE ARCHIVO .env
# EDF Catálogo de Tablas
# =========================================

set -e

echo "🔧 ACTUALIZADOR DEL ARCHIVO .env"
echo "================================="

ENV_FILE=".env"

# Verificar que existe .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

echo "✅ Archivo .env encontrado, procediendo con la actualización..."
echo ""

# Función para actualizar variable
update_env_var() {
    local var_name="$1"
    local var_description="$2"
    local current_value="$3"
    local is_secret="$4"
    
    echo "🔧 Configurando: $var_description"
    
    if [ -n "$current_value" ]; then
        if [ "$is_secret" = "true" ]; then
            local display_value="${current_value:0:8}...***"
        else
            local display_value="$current_value"
        fi
        echo "   Valor actual: $display_value"
    else
        echo "   Valor actual: NO DEFINIDO"
    fi
    
    read -p "   Nuevo valor (Enter para mantener actual): " new_value
    
    if [ -n "$new_value" ]; then
        # Escapar caracteres especiales para sed
        escaped_old=$(printf '%s\n' "$current_value" | sed 's/[[\.*^$()+?{|]/\\&/g')
        escaped_new=$(printf '%s\n' "$new_value" | sed 's/[[\.*^$(){}+?{|]/\\&/g')
        
        # Reemplazar en el archivo
        sed -i "s|^${var_name}=${escaped_old}|${var_name}=${escaped_new}|g" "$ENV_FILE"
        echo "   ✅ Actualizado: $var_name"
    else
        echo "   ⏭️  Mantenido: $var_name"
    fi
    echo ""
}

# Obtener valores actuales
get_current_value() {
    local var_name="$1"
    grep "^${var_name}=" "$ENV_FILE" | cut -d'=' -f2- || echo ""
}

echo "📋 CONFIGURACIÓN DE VARIABLES CRÍTICAS"
echo "======================================"
echo ""

# 1. MongoDB URI
current_mongo=$(get_current_value "MONGO_URI")
echo "💾 MONGODB - Base de datos principal"
echo "   Ejemplos:"
echo "   - Local: mongodb://localhost:27017/edefrutos2025"
echo "   - Atlas: mongodb+srv://usuario:password@cluster.mongodb.net/database"
echo "   - Remoto: mongodb://usuario:password@host:27017/database"
update_env_var "MONGO_URI" "URI de MongoDB" "$current_mongo" "false"

# 2. Secret Key
current_secret=$(get_current_value "SECRET_KEY")
echo "🔑 SECRET_KEY - Clave secreta de Flask"
echo "   Esta clave debe ser única y secreta para producción"
update_env_var "SECRET_KEY" "Clave secreta de Flask" "$current_secret" "true"

# 3. BREVO API Key
current_brevo_api=$(get_current_value "BREVO_API_KEY")
echo "📧 BREVO API KEY - Para envío de emails"
echo "   Obtener en: https://app.brevo.com/settings/keys/api"
update_env_var "BREVO_API_KEY" "API Key de Brevo" "$current_brevo_api" "true"

# 4. BREVO SMTP Password
current_brevo_password=$(get_current_value "BREVO_SMTP_PASSWORD")
echo "🔐 BREVO SMTP PASSWORD - Contraseña SMTP"
echo "   ⚠️  IMPORTANTE: La contraseña actual está comprometida"
if [[ "$current_brevo_password" == *"Rmp3UXwsIkvA0c1d"* ]]; then
    echo "   🚨 CREDENCIAL COMPROMETIDA - DEBE CAMBIARSE"
fi
update_env_var "BREVO_SMTP_PASSWORD" "Password SMTP de Brevo" "$current_brevo_password" "true"

# 5. URLs y configuración del servidor
echo "🌐 CONFIGURACIÓN DEL SERVIDOR"
echo "============================"

current_base_url=$(get_current_value "BASE_URL")
echo "🔗 URL BASE - URL pública de la aplicación"
echo "   Ejemplo: https://edefrutos2025.xyz"
update_env_var "BASE_URL" "URL base de la aplicación" "$current_base_url" "false"

# 6. Configuración de AWS (si se usa)
echo "☁️  CONFIGURACIÓN AWS (Opcional)"
echo "==============================="

current_aws_key=$(get_current_value "AWS_ACCESS_KEY_ID")
if [ -n "$current_aws_key" ] && [ "$current_aws_key" != "tu-aws-access-key-id" ]; then
    echo "🔧 AWS ya configurado"
    read -p "¿Actualizar configuración AWS? (y/N): " update_aws
    if [[ $update_aws =~ ^[Yy]$ ]]; then
        update_env_var "AWS_ACCESS_KEY_ID" "AWS Access Key ID" "$current_aws_key" "true"
        
        current_aws_secret=$(get_current_value "AWS_SECRET_ACCESS_KEY")
        update_env_var "AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key" "$current_aws_secret" "true"
        
        current_aws_region=$(get_current_value "AWS_REGION")
        update_env_var "AWS_REGION" "AWS Region" "$current_aws_region" "false"
    fi
else
    read -p "¿Configurar AWS S3? (y/N): " configure_aws
    if [[ $configure_aws =~ ^[Yy]$ ]]; then
        update_env_var "AWS_ACCESS_KEY_ID" "AWS Access Key ID" "" "true"
        update_env_var "AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key" "" "true"
        update_env_var "AWS_REGION" "AWS Region (ej: eu-west-1)" "" "false"
    fi
fi

echo ""
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "==========================="

# Ejecutar verificador
if [ -f "verificar_env_simple.sh" ]; then
    echo "🔍 Ejecutando verificación..."
    ./verificar_env_simple.sh
else
    echo "📋 RESUMEN DE LA CONFIGURACIÓN:"
    echo "   MONGO_URI: $(get_current_value "MONGO_URI" | cut -c1-50)..."
    echo "   SECRET_KEY: $(get_current_value "SECRET_KEY" | cut -c1-10)...***"
    echo "   BREVO_API_KEY: $(get_current_value "BREVO_API_KEY" | cut -c1-10)...***"
    echo "   BASE_URL: $(get_current_value "BASE_URL")"
fi

echo ""
echo "🚨 RECORDATORIOS IMPORTANTES:"
echo "   1. NO commitear el archivo .env a Git"
echo "   2. Usar GitHub Secrets para CI/CD"
echo "   3. Cambiar passwords comprometidas"
echo "   4. Hacer backup de la configuración en lugar seguro"

echo ""
echo "✅ Configuración del archivo .env completada"