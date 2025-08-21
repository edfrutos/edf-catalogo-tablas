#!/bin/bash

# Script para unificar archivos txt de forma simple
# Autor: EDF Developer - 2025

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}📝 Script para unificar archivos txt${NC}"
    echo ""
    echo "Uso: $0 <archivo1> <archivo2> [opción]"
    echo ""
    echo "Opciones:"
    echo "  append    - Añade el contenido del archivo2 al final del archivo1"
    echo "  merge     - Combina ambos archivos eliminando duplicados (por defecto)"
    echo "  sync      - Sincroniza ambos archivos con el mismo contenido"
    echo "  compare   - Compara los archivos y muestra diferencias"
    echo "  help      - Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 archivo1.txt archivo2.txt"
    echo "  $0 archivo1.txt archivo2.txt merge"
    echo "  $0 archivo1.txt archivo2.txt sync"
    echo "  $0 archivo1.txt archivo2.txt compare"
}

# Función para verificar que los archivos existen
check_files() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ Error: El archivo $1 no existe${NC}"
        exit 1
    fi
    if [ ! -f "$2" ]; then
        echo -e "${RED}❌ Error: El archivo $2 no existe${NC}"
        exit 1
    fi
}

# Función para unificar (append)
unify_append() {
    local file1="$1"
    local file2="$2"
    local output="${file1}_unified_$(date +%Y%m%d_%H%M%S).txt"
    
    echo -e "${BLUE}📝 Unificando $file1 + $file2${NC}"
    
    cat "$file1" "$file2" > "$output"
    
    lines1=$(wc -l < "$file1")
    lines2=$(wc -l < "$file2")
    total=$(wc -l < "$output")
    
    echo -e "${GREEN}✅ Archivo unificado guardado como: $output${NC}"
    echo -e "${YELLOW}📊 Líneas del archivo 1: $lines1${NC}"
    echo -e "${YELLOW}📊 Líneas del archivo 2: $lines2${NC}"
    echo -e "${YELLOW}📊 Total de líneas: $total${NC}"
}

# Función para fusionar (merge sin duplicados)
unify_merge() {
    local file1="$1"
    local file2="$2"
    local output="${file1}_merged_$(date +%Y%m%d_%H%M%S).txt"
    
    echo -e "${BLUE}🔄 Fusionando $file1 + $file2 (sin duplicados)${NC}"
    
    # Combinar y eliminar duplicados
    cat "$file1" "$file2" | sort | uniq > "$output"
    
    lines1=$(wc -l < "$file1")
    lines2=$(wc -l < "$file2")
    unique=$(wc -l < "$output")
    duplicates=$((lines1 + lines2 - unique))
    
    echo -e "${GREEN}✅ Archivo fusionado guardado como: $output${NC}"
    echo -e "${YELLOW}📊 Líneas del archivo 1: $lines1${NC}"
    echo -e "${YELLOW}📊 Líneas del archivo 2: $lines2${NC}"
    echo -e "${YELLOW}📊 Total de líneas únicas: $unique${NC}"
    echo -e "${YELLOW}📊 Duplicados eliminados: $duplicates${NC}"
}

# Función para sincronizar
unify_sync() {
    local file1="$1"
    local file2="$2"
    
    echo -e "${BLUE}🔄 Sincronizando $file1 ↔ $file2${NC}"
    
    # Crear backups
    timestamp=$(date +%Y%m%d_%H%M%S)
    cp "$file1" "${file1}.backup_${timestamp}"
    cp "$file2" "${file2}.backup_${timestamp}"
    
    echo -e "${YELLOW}💾 Backups creados${NC}"
    
    # Crear contenido unificado
    temp_file=$(mktemp)
    cat "$file1" "$file2" | sort | uniq > "$temp_file"
    
    # Sincronizar ambos archivos
    cp "$temp_file" "$file1"
    cp "$temp_file" "$file2"
    
    rm "$temp_file"
    
    unique=$(wc -l < "$file1")
    echo -e "${GREEN}✅ Archivos sincronizados exitosamente${NC}"
    echo -e "${YELLOW}📊 Contenido único en ambos archivos: $unique líneas${NC}"
}

# Función para comparar
unify_compare() {
    local file1="$1"
    local file2="$2"
    
    echo -e "${BLUE}🔍 Comparando $file1 vs $file2${NC}"
    
    # Encontrar diferencias
    only_in_1=$(comm -23 <(sort "$file1") <(sort "$file2"))
    only_in_2=$(comm -13 <(sort "$file1") <(sort "$file2"))
    common=$(comm -12 <(sort "$file1") <(sort "$file2"))
    
    lines1=$(wc -l < "$file1")
    lines2=$(wc -l < "$file2")
    unique1=$(echo "$only_in_1" | wc -l)
    unique2=$(echo "$only_in_2" | wc -l)
    common_count=$(echo "$common" | wc -l)
    
    echo -e "${YELLOW}📊 Líneas únicas en $file1: $unique1${NC}"
    echo -e "${YELLOW}📊 Líneas únicas en $file2: $unique2${NC}"
    echo -e "${YELLOW}📊 Líneas comunes: $common_count${NC}"
    
    if [ -n "$only_in_1" ]; then
        echo -e "\n${BLUE}📄 Solo en $file1:${NC}"
        echo "$only_in_1" | sed 's/^/  + /'
    fi
    
    if [ -n "$only_in_2" ]; then
        echo -e "\n${BLUE}📄 Solo en $file2:${NC}"
        echo "$only_in_2" | sed 's/^/  + /'
    fi
    
    if [ $unique1 -eq 0 ] && [ $unique2 -eq 0 ]; then
        echo -e "${GREEN}✅ Los archivos son idénticos${NC}"
    else
        echo -e "${YELLOW}⚠️  Los archivos tienen diferencias${NC}"
    fi
}

# Verificar argumentos
if [ $# -lt 2 ]; then
    show_help
    exit 1
fi

# Verificar si se solicita ayuda
if [ "$1" = "help" ] || [ "$2" = "help" ]; then
    show_help
    exit 0
fi

file1="$1"
file2="$2"
mode="${3:-merge}"  # Por defecto: merge

# Verificar que los archivos existen
check_files "$file1" "$file2"

# Ejecutar operación según el modo
case "$mode" in
    "append")
        unify_append "$file1" "$file2"
        ;;
    "merge")
        unify_merge "$file1" "$file2"
        ;;
    "sync")
        unify_sync "$file1" "$file2"
        ;;
    "compare")
        unify_compare "$file1" "$file2"
        ;;
    *)
        echo -e "${RED}❌ Error: Modo '$mode' no válido${NC}"
        show_help
        exit 1
        ;;
esac
