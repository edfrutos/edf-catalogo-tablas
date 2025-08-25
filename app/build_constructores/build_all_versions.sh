#!/bin/bash

echo "🚀 Constructor de EDF Catálogo de Tablas - Todas las Versiones"
echo "============================================================="
echo ""
echo "Elige qué versión quieres construir:"
echo "1) Versión Web (navegador)"
echo "2) Versión Nativa (ventana de escritorio)"
echo "3) Ambas versiones"
echo "4) Salir"
echo ""
read -p "Selecciona una opción (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Construyendo versión Web..."
        ./build_web_app.sh
        ;;
    2)
        echo ""
        echo "🔨 Construyendo versión Nativa..."
        ./build_native_app.sh
        ;;
    3)
        echo ""
        echo "🔨 Construyendo ambas versiones..."
        echo "📱 Primero la versión Web..."
        ./build_web_app.sh
        echo ""
        echo "🖥️  Ahora la versión Nativa..."
        ./build_native_app.sh
        ;;
    4)
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "✅ Proceso completado!"
echo ""
echo "📁 Aplicaciones disponibles:"
if [ -d "dist/EDF_CatalogoDeTablas_Web" ]; then
    echo "   🌐 Web: dist/EDF_CatalogoDeTablas_Web/EDF_CatalogoDeTablas_Web"
fi
if [ -d "dist/EDF_CatalogoDeTablas_Native" ]; then
    echo "   🖥️  Nativa: dist/EDF_CatalogoDeTablas_Native/EDF_CatalogoDeTablas_Native"
fi
echo ""
echo "🚀 Para probar las aplicaciones:"
echo "   🌐 Web: Se abre automáticamente en el navegador"
echo "   🖥️  Nativa: Se ejecuta en una ventana nativa de macOS"
