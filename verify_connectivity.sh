#!/bin/bash

# Script para verificar conectividad y problemas de red
# Útil para diagnosticar problemas de GitHub Actions

echo "🌐 VERIFICACIÓN DE CONECTIVIDAD"
echo "==============================="

# Función para verificar conectividad
check_connectivity() {
    local host=$1
    local name=$2
    echo "🔍 Verificando $name ($host)..."
    
    if ping -c 3 "$host" > /dev/null 2>&1; then
        echo "✅ $name - CONECTIVIDAD OK"
        return 0
    else
        echo "❌ $name - SIN CONECTIVIDAD"
        return 1
    fi
}

# Función para verificar DNS
check_dns() {
    local host=$1
    local name=$2
    echo "🔍 Verificando DNS para $name ($host)..."
    
    if nslookup "$host" > /dev/null 2>&1; then
        echo "✅ DNS para $name - OK"
        return 0
    else
        echo "❌ DNS para $name - FALLO"
        return 1
    fi
}

# Función para verificar HTTP
check_http() {
    local url=$1
    local name=$2
    echo "🔍 Verificando HTTP para $name ($url)..."
    
    if curl -s --connect-timeout 10 --max-time 30 "$url" > /dev/null 2>&1; then
        echo "✅ HTTP para $name - OK"
        return 0
    else
        echo "❌ HTTP para $name - FALLO"
        return 1
    fi
}

echo ""
echo "📡 Verificando conectividad básica..."

# Verificar conectividad básica
check_connectivity "8.8.8.8" "Google DNS"
check_connectivity "1.1.1.1" "Cloudflare DNS"

echo ""
echo "🌍 Verificando servicios críticos..."

# Verificar servicios críticos para el workflow
check_connectivity "pypi.org" "PyPI"
check_connectivity "github.com" "GitHub"
check_connectivity "actions.githubusercontent.com" "GitHub Actions"

echo ""
echo "🔍 Verificando resolución DNS..."

# Verificar DNS
check_dns "pypi.org" "PyPI"
check_dns "github.com" "GitHub"
check_dns "actions.githubusercontent.com" "GitHub Actions"

echo ""
echo "🌐 Verificando HTTP/HTTPS..."

# Verificar HTTP/HTTPS
check_http "https://pypi.org" "PyPI HTTPS"
check_http "https://github.com" "GitHub HTTPS"
check_http "https://api.github.com" "GitHub API"

echo ""
echo "🔧 Verificando configuración de red..."

# Verificar configuración de red
echo "📋 Configuración de red:"
echo "   - Interfaz principal: $(route -n get default | grep interface | awk '{print $2}' 2>/dev/null || echo 'No disponible')"
echo "   - Gateway: $(route -n get default | grep gateway | awk '{print $2}' 2>/dev/null || echo 'No disponible')"
echo "   - DNS: $(cat /etc/resolv.conf | grep nameserver | head -1 | awk '{print $2}' 2>/dev/null || echo 'No disponible')"

echo ""
echo "📊 Verificando velocidad de red..."

# Verificar velocidad de red (descarga de un archivo pequeño)
echo "🚀 Probando velocidad de descarga..."
if curl -s --connect-timeout 10 --max-time 30 -o /dev/null -w "Tiempo de conexión: %{time_connect}s\nTiempo total: %{time_total}s\n" "https://httpbin.org/bytes/1024" 2>/dev/null; then
    echo "✅ Descarga de prueba exitosa"
else
    echo "❌ Descarga de prueba falló"
fi

echo ""
echo "🔍 Verificando puertos comunes..."

# Verificar puertos comunes
check_port() {
    local host=$1
    local port=$2
    local name=$3
    
    if nc -z -w5 "$host" "$port" 2>/dev/null; then
        echo "✅ $name ($host:$port) - ACCESIBLE"
    else
        echo "❌ $name ($host:$port) - NO ACCESIBLE"
    fi
}

check_port "pypi.org" 443 "PyPI HTTPS"
check_port "github.com" 443 "GitHub HTTPS"
check_port "github.com" 22 "GitHub SSH"

echo ""
echo "📋 RESUMEN DE VERIFICACIÓN"
echo "=========================="

# Contar errores
errors=0
if ! ping -c 1 pypi.org > /dev/null 2>&1; then
    errors=$((errors + 1))
fi
if ! ping -c 1 github.com > /dev/null 2>&1; then
    errors=$((errors + 1))
fi

if [ $errors -eq 0 ]; then
    echo "🎉 CONECTIVIDAD PERFECTA"
    echo "✅ Todos los servicios críticos están accesibles"
    echo "✅ Puedes hacer push con confianza"
    exit 0
else
    echo "⚠️  PROBLEMAS DE CONECTIVIDAD DETECTADOS"
    echo "❌ $errors servicio(s) no accesible(s)"
    echo "💡 Posibles soluciones:"
    echo "   - Verificar conexión a internet"
    echo "   - Verificar firewall/proxy"
    echo "   - Verificar DNS"
    echo "   - Esperar unos minutos y reintentar"
    exit 1
fi
