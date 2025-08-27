#!/bin/bash
# Launcher para la aplicación nativa macOS
# Generado automáticamente por fix_native_app_macos.py

# Cambiar al directorio de la aplicación
cd "$(dirname "$0")"

# Verificar que la aplicación existe
if [ ! -d "dist/EDF_CatalogoDeTablas_Web_Native.app" ]; then
    echo "❌ Aplicación nativa no encontrada: dist/EDF_CatalogoDeTablas_Web_Native.app"
    exit 1
fi

# Cargar variables de entorno desde .env si existe
if [ -f ".env" ]; then
    echo "📁 Cargando variables de entorno desde .env..."
    
    # Cargar variables de entorno de forma robusta
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
    echo "⚠️  Archivo .env no encontrado, usando variables del sistema"
fi

# Verificar MONGO_URI
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    echo "💡 Asegúrate de que el archivo .env esté presente"
    exit 1
fi

echo "🚀 Iniciando aplicación nativa..."
echo "📡 MongoDB URI: ${MONGO_URI:0:30}... (ocultando credenciales)"

# Ejecutar la aplicación nativa
open "dist/EDF_CatalogoDeTablas_Web_Native.app"
