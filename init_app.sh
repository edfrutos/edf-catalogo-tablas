#!/bin/bash
# Script de inicialización para cargar variables de entorno
# Generado automáticamente por fix_mongodb_env_macos.py

# Cargar variables de entorno desde .env
if [ -f "/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/.env" ]; then
    # Cargar variables de entorno de forma más robusta
    while IFS= read -r line; do
        # Ignorar líneas vacías, comentarios y líneas que no contienen '='
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# && "$line" == *"="* ]]; then
            # Extraer nombre y valor de la variable
            var_name="${line%%=*}"
            var_value="${line#*=}"
            # Eliminar espacios en blanco
            var_name=$(echo "$var_name" | xargs)
            var_value=$(echo "$var_value" | xargs)
            # Exportar la variable solo si tiene un nombre válido
            if [[ -n "$var_name" && "$var_name" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
                export "$var_name=$var_value"
            fi
        fi
    done < "/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/.env"
    
    echo "✅ Variables de entorno cargadas desde /Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/.env"
else
    echo "❌ Archivo .env no encontrado en /Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/.env"
    exit 1
fi

# Verificar que MONGO_URI esté disponible
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    exit 1
else
    echo "✅ MONGO_URI configurada correctamente"
fi

# Ejecutar la aplicación
echo "🚀 Iniciando aplicación..."
exec "$@"
