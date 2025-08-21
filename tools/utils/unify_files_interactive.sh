#!/bin/bash

# Script interactivo para unificar archivos txt
# Autor: EDF Developer - 2025

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para mostrar el menú principal
show_main_menu() {
    clear
    echo -e "${BLUE}🎯 Unificador Interactivo de Archivos TXT${NC}"
    echo -e "${BLUE}==================================================${NC}"
    echo ""
    echo -e "${CYAN}📋 Modos disponibles:${NC}"
    echo -e "  1. ${YELLOW}Modo Interactivo${NC} (archivos individuales)"
    echo -e "  2. ${YELLOW}Modo Batch${NC} (múltiples archivos)"
    echo -e "  3. ${YELLOW}Modo Comando${NC} (argumentos)"
    echo -e "  0. ${RED}Salir${NC}"
    echo ""
}

# Función para obtener lista de archivos txt
get_txt_files() {
    find . -maxdepth 1 -name "*.txt" -type f | sed 's|^\./||' | sort
}

# Función para mostrar archivos disponibles
show_file_list() {
    local files=($(get_txt_files))
    local count=${#files[@]}
    
    if [ $count -eq 0 ]; then
        echo -e "${RED}❌ No hay archivos .txt en el directorio actual${NC}"
        return 1
    fi
    
    echo -e "${CYAN}📁 Archivos disponibles:${NC}"
    for i in "${!files[@]}"; do
        echo -e "  ${YELLOW}$((i+1)).${NC} ${files[i]}"
    done
    echo -e "  ${RED}0.${NC} Cancelar"
    echo ""
}

# Función para seleccionar archivo
select_file() {
    local prompt="$1"
    local files=($(get_txt_files))
    local count=${#files[@]}
    
    if [ $count -eq 0 ]; then
        echo -e "${RED}❌ No hay archivos .txt disponibles${NC}"
        return 1
    fi
    
    echo -e "${BLUE}$prompt${NC}"
    show_file_list
    
    while true; do
        read -p "🔢 Selecciona un número: " choice
        
        if [[ "$choice" == "0" ]]; then
            return 1
        fi
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
            echo "${files[$((choice-1))]}"
            return 0
        else
            echo -e "${RED}❌ Número inválido. Intenta de nuevo.${NC}"
        fi
    done
}

# Función para ingresar ruta manualmente
input_file_path() {
    local prompt="$1"
    
    while true; do
        read -p "$prompt (o 'cancel' para cancelar): " file_path
        
        if [[ "$file_path" =~ ^(cancel|c|salir|s)$ ]]; then
            return 1
        fi
        
        if [[ -z "$file_path" ]]; then
            echo -e "${RED}❌ Por favor ingresa una ruta válida.${NC}"
            continue
        fi
        
        # Expandir ~ si está presente
        file_path="${file_path/#\~/$HOME}"
        
        if [[ -f "$file_path" ]]; then
            echo "$file_path"
            return 0
        else
            echo -e "${RED}❌ El archivo '$file_path' no existe.${NC}"
            read -p "¿Quieres crear este archivo? (s/n): " create
            if [[ "$create" =~ ^(s|si|sí|y|yes)$ ]]; then
                touch "$file_path"
                echo -e "${GREEN}✅ Archivo '$file_path' creado.${NC}"
                echo "$file_path"
                return 0
            else
                echo -e "${YELLOW}❌ Operación cancelada.${NC}"
            fi
        fi
    done
}

# Función para seleccionar operación
select_operation() {
    echo -e "${CYAN}🛠️  Operaciones disponibles:${NC}"
    echo -e "  1. ${YELLOW}Append${NC} - Añadir contenido del archivo2 al final del archivo1"
    echo -e "  2. ${YELLOW}Merge${NC} - Combinar archivos eliminando duplicados"
    echo -e "  3. ${YELLOW}Sync${NC} - Sincronizar ambos archivos con el mismo contenido"
    echo -e "  4. ${YELLOW}Compare${NC} - Comparar archivos y mostrar diferencias"
    echo -e "  0. ${RED}Salir${NC}"
    echo ""
    
    while true; do
        read -p "🔢 Selecciona una operación: " choice
        
        case "$choice" in
            "1") echo "append"; return 0 ;;
            "2") echo "merge"; return 0 ;;
            "3") echo "sync"; return 0 ;;
            "4") echo "compare"; return 0 ;;
            "0") return 1 ;;
            *) echo -e "${RED}❌ Opción inválida. Intenta de nuevo.${NC}" ;;
        esac
    done
}

# Función para modo interactivo
interactive_mode() {
    echo -e "${BLUE}🎯 Modo Interactivo - Unificador de Archivos TXT${NC}"
    echo -e "${BLUE}==================================================${NC}"
    
    # Verificar archivos disponibles
    local files=($(get_txt_files))
    local count=${#files[@]}
    
    echo -e "\n📂 Directorio actual: $(pwd)"
    
    # Seleccionar primer archivo
    local file1=""
    if [ $count -gt 0 ]; then
        echo -e "\n¿Cómo quieres seleccionar el primer archivo?"
        echo -e "  1. Seleccionar de la lista"
        echo -e "  2. Ingresar ruta manualmente"
        
        read -p "🔢 Opción: " choice
        
        case "$choice" in
            "1")
                file1=$(select_file "Selecciona el primer archivo:")
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ Operación cancelada.${NC}"
                    return
                fi
                ;;
            "2")
                file1=$(input_file_path "Ingresa la ruta del primer archivo:")
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ Operación cancelada.${NC}"
                    return
                fi
                ;;
            *)
                echo -e "${RED}❌ Opción inválida.${NC}"
                return
                ;;
        esac
    else
        file1=$(input_file_path "Ingresa la ruta del primer archivo:")
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Operación cancelada.${NC}"
            return
        fi
    fi
    
    # Seleccionar segundo archivo
    local file2=""
    if [ $count -gt 0 ]; then
        echo -e "\n¿Cómo quieres seleccionar el segundo archivo?"
        echo -e "  1. Seleccionar de la lista"
        echo -e "  2. Ingresar ruta manualmente"
        
        read -p "🔢 Opción: " choice
        
        case "$choice" in
            "1")
                file2=$(select_file "Selecciona el segundo archivo:")
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ Operación cancelada.${NC}"
                    return
                fi
                ;;
            "2")
                file2=$(input_file_path "Ingresa la ruta del segundo archivo:")
                if [ $? -ne 0 ]; then
                    echo -e "${RED}❌ Operación cancelada.${NC}"
                    return
                fi
                ;;
            *)
                echo -e "${RED}❌ Opción inválida.${NC}"
                return
                ;;
        esac
    else
        file2=$(input_file_path "Ingresa la ruta del segundo archivo:")
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Operación cancelada.${NC}"
            return
        fi
    fi
    
    # Seleccionar operación
    local operation=$(select_operation)
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Operación cancelada.${NC}"
        return
    fi
    
    # Ejecutar operación
    echo -e "\n🚀 Ejecutando operación: $operation"
    echo -e "📄 Archivo 1: $file1"
    echo -e "📄 Archivo 2: $file2"
    
    # Llamar al script original
    if ./unify_files.sh "$file1" "$file2" "$operation"; then
        echo -e "\n${GREEN}✅ Operación completada exitosamente!${NC}"
    else
        echo -e "\n${RED}❌ Error en la operación.${NC}"
    fi
    
    read -p "Presiona Enter para continuar..."
}

# Función para modo batch
batch_mode() {
    echo -e "${BLUE}📦 Modo Batch - Procesamiento de Múltiples Archivos${NC}"
    echo -e "${BLUE}==================================================${NC}"
    
    local files=($(get_txt_files))
    local count=${#files[@]}
    
    if [ $count -lt 2 ]; then
        echo -e "${RED}❌ Se necesitan al menos 2 archivos .txt para el modo batch.${NC}"
        read -p "Presiona Enter para continuar..."
        return
    fi
    
    echo -e "\n📁 Archivos disponibles: ${files[*]}"
    
    # Seleccionar archivos a procesar
    echo -e "\n¿Qué archivos quieres procesar?"
    echo -e "  1. Todos los archivos .txt"
    echo -e "  2. Seleccionar archivos específicos"
    
    read -p "🔢 Opción: " choice
    
    local files_to_process=()
    case "$choice" in
        "1")
            files_to_process=("${files[@]}")
            ;;
        "2")
            echo -e "\nSelecciona los archivos (números separados por comas):"
            for i in "${!files[@]}"; do
                echo -e "  ${YELLOW}$((i+1)).${NC} ${files[i]}"
            done
            
            read -p "🔢 Números: " selections
            IFS=',' read -ra nums <<< "$selections"
            for num in "${nums[@]}"; do
                num=$(echo "$num" | tr -d ' ')
                if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "$count" ]; then
                    files_to_process+=("${files[$((num-1))]}")
                fi
            done
            ;;
        *)
            echo -e "${RED}❌ Opción inválida.${NC}"
            read -p "Presiona Enter para continuar..."
            return
            ;;
    esac
    
    if [ ${#files_to_process[@]} -lt 2 ]; then
        echo -e "${RED}❌ Se necesitan al menos 2 archivos para procesar.${NC}"
        read -p "Presiona Enter para continuar..."
        return
    fi
    
    # Seleccionar operación
    local operation=$(select_operation)
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Operación cancelada.${NC}"
        return
    fi
    
    # Procesar archivos
    echo -e "\n🚀 Procesando ${#files_to_process[@]} archivos con operación: $operation"
    
    for ((i=0; i<${#files_to_process[@]}-1; i++)); do
        local file1="${files_to_process[i]}"
        local file2="${files_to_process[i+1]}"
        
        echo -e "\n📄 Procesando: $file1 + $file2"
        
        if ./unify_files.sh "$file1" "$file2" "$operation"; then
            echo -e "${GREEN}✅ $file1 + $file2 procesados exitosamente!${NC}"
        else
            echo -e "${RED}❌ Error procesando $file1 + $file2${NC}"
        fi
    done
    
    read -p "Presiona Enter para continuar..."
}

# Función principal
main() {
    while true; do
        show_main_menu
        
        read -p "🔢 Selecciona un modo: " choice
        
        case "$choice" in
            "0")
                echo -e "${GREEN}👋 ¡Hasta luego!${NC}"
                exit 0
                ;;
            "1")
                interactive_mode
                ;;
            "2")
                batch_mode
                ;;
            "3")
                echo -e "\n💡 Para usar el modo comando, ejecuta:"
                echo -e "   ${YELLOW}python3 tools/utils/unify_files.py archivo1.txt archivo2.txt --mode merge${NC}"
                echo -e "   ${YELLOW}./tools/utils/unify_files.sh archivo1.txt archivo2.txt merge${NC}"
                read -p "Presiona Enter para continuar..."
                ;;
            *)
                echo -e "${RED}❌ Opción inválida. Intenta de nuevo.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Ejecutar función principal
main
