#!/bin/bash

# ==============================================
# 🔍 SCRIPT: Verificar y Liberar Puerto 5002
# ==============================================

PORT=5002
APP_NAME="EDF_CatalogoDeTablas"

echo "🔍 Verificando puerto $PORT..."

# Función para verificar si el puerto está en uso
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Puerto $PORT está ocupado"
        return 0  # Puerto ocupado
    else
        echo "✅ Puerto $PORT está libre"
        return 1  # Puerto libre
    fi
}

# Función para liberar el puerto
free_port() {
    echo "🔧 Intentando liberar puerto $PORT..."
    
    # Buscar procesos que usen el puerto
    PIDS=$(lsof -ti :$PORT 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "📋 Procesos encontrados en puerto $PORT:"
        lsof -i :$PORT
        
        echo "🔄 Terminando procesos..."
        for PID in $PIDS; do
            echo "   - Terminando proceso $PID"
            kill -TERM $PID 2>/dev/null
            
            # Esperar un poco y verificar si se terminó
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                echo "   - Forzando terminación del proceso $PID"
                kill -KILL $PID 2>/dev/null
            fi
        done
        
        # Verificar si se liberó el puerto
        sleep 3
        if check_port; then
            echo "❌ No se pudo liberar el puerto $PORT"
            return 1
        else
            echo "✅ Puerto $PORT liberado exitosamente"
            return 0
        fi
    else
        echo "✅ No se encontraron procesos en puerto $PORT"
        return 0
    fi
}

# Función para verificar si hay instancias de la app ejecutándose
check_app_instances() {
    echo "🔍 Verificando instancias de $APP_NAME..."
    
    # Buscar procesos de Python que ejecuten la app
    PYTHON_PIDS=$(ps aux | grep -E "(flask|python.*main_app|python.*wsgi)" | grep -v grep | awk '{print $2}')
    
    if [ -n "$PYTHON_PIDS" ]; then
        echo "⚠️  Instancias de Flask/Python encontradas:"
        ps aux | grep -E "(flask|python.*main_app|python.*wsgi)" | grep -v grep
        
        echo "🔄 Terminando instancias de Flask/Python..."
        for PID in $PYTHON_PIDS; do
            echo "   - Terminando proceso $PID"
            kill -TERM $PID 2>/dev/null
        done
        
        sleep 3
        echo "✅ Instancias de Flask/Python terminadas"
    else
        echo "✅ No se encontraron instancias de Flask/Python ejecutándose"
    fi
}

# Función principal
main() {
    echo "🚀 Iniciando verificación de puerto $PORT para $APP_NAME"
    echo "=================================================="
    
    # Verificar instancias de la app
    check_app_instances
    
    # Verificar si el puerto está ocupado
    if check_port; then
        echo "🔄 Puerto ocupado, intentando liberar..."
        if free_port; then
            echo "✅ Puerto $PORT listo para usar"
        else
            echo "❌ Error: No se pudo liberar el puerto $PORT"
            echo "💡 Sugerencias:"
            echo "   - Reinicia tu terminal"
            echo "   - Usa 'sudo lsof -i :$PORT' para ver qué usa el puerto"
            echo "   - Usa 'sudo kill -9 <PID>' para forzar la terminación"
            exit 1
        fi
    else
        echo "✅ Puerto $PORT está libre y listo"
    fi
    
    echo "=================================================="
    echo "🎯 Puerto $PORT verificado y listo para $APP_NAME"
    echo "💡 Ahora puedes ejecutar: flask run --debug --port=$PORT"
}

# Ejecutar función principal
main "$@"
