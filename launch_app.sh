#!/bin/bash
# Launcher para la aplicación con variables de entorno
# Generado automáticamente por fix_mongodb_env_macos.py

# Cambiar al directorio de la aplicación
cd "/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas"

# Cargar variables de entorno de forma robusta
if [ -f ".env" ]; then
    echo "📁 Cargando variables de entorno desde .env..."
    
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
    done < ".env"
    
    echo "✅ Variables de entorno cargadas"
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Verificar MONGO_URI
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    exit 1
fi

echo "🚀 Iniciando aplicación..."
echo "📡 MongoDB URI: ${MONGO_URI:0:30}... (ocultando credenciales)"

# Ejecutar la aplicación web
python3 launcher_web.py
