#!/usr/bin/env python3
"""
Solución para el archivo MP4 problemático
==========================================

Limpia referencias cached y proporciona herramientas para resolver
el problema de archivos MP4 que ya no existen pero siguen siendo
referenciados por el navegador.
"""

def create_cache_cleaner_script():
    """Crear script JavaScript para limpiar cache"""
    js_content = """
// SOLUCIONADOR DE ARCHIVOS MP4 PROBLEMÁTICOS
// ==========================================

console.log('🧹 Iniciando limpieza de cache de archivos multimedia problemáticos...');

// Archivo específico problemático
const PROBLEMATIC_FILE = 'cf342a562c104122a5ca9241bf1ef896_oUcGqQXIG8InPCfTAIeSA2gneLBJnRIInz4jwY.MP4';

// Función para limpiar localStorage
function cleanLocalStorage() {
    console.log('🧹 Limpiando localStorage...');
    
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        
        if (value && value.includes(PROBLEMATIC_FILE)) {
            keysToRemove.push(key);
            console.log(`❌ Removiendo clave localStorage: ${key}`);
        }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
    console.log(`✅ localStorage limpiado: ${keysToRemove.length} claves removidas`);
}

// Función para limpiar sessionStorage
function cleanSessionStorage() {
    console.log('🧹 Limpiando sessionStorage...');
    
    const keysToRemove = [];
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const value = sessionStorage.getItem(key);
        
        if (value && value.includes(PROBLEMATIC_FILE)) {
            keysToRemove.push(key);
            console.log(`❌ Removiendo clave sessionStorage: ${key}`);
        }
    }
    
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
    console.log(`✅ sessionStorage limpiado: ${keysToRemove.length} claves removidas`);
}

// Función para interceptar requests al archivo problemático
function interceptProblematicRequests() {
    console.log('🛡️ Interceptando requests problemáticos...');
    
    // Interceptar fetch requests
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const url = args[0];
        if (typeof url === 'string' && url.includes(PROBLEMATIC_FILE)) {
            console.warn(`🚫 INTERCEPTADO: Request a archivo problemático bloqueado: ${url}`);
            return Promise.reject(new Error(`Archivo ${PROBLEMATIC_FILE} no existe - request interceptado`));
        }
        return originalFetch.apply(this, args);
    };
    
    // Interceptar XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        if (typeof url === 'string' && url.includes(PROBLEMATIC_FILE)) {
            console.warn(`🚫 INTERCEPTADO: XMLHttpRequest a archivo problemático bloqueado: ${url}`);
            throw new Error(`Archivo ${PROBLEMATIC_FILE} no existe - request interceptado`);
        }
        return originalOpen.apply(this, [method, url, ...args]);
    };
}

// Función para remover elementos DOM que referencien el archivo problemático
function cleanDOMReferences() {
    console.log('🧹 Limpiando referencias DOM...');
    
    const elementsToClean = [];
    
    // Buscar elementos video, audio, img con src problemático
    const mediaElements = document.querySelectorAll('video, audio, img, source');
    mediaElements.forEach(element => {
        const src = element.src || element.getAttribute('src') || '';
        if (src.includes(PROBLEMATIC_FILE)) {
            elementsToClean.push(element);
        }
    });
    
    // Buscar elementos con data-src problemático
    const dataElements = document.querySelectorAll('[data-src]');
    dataElements.forEach(element => {
        const dataSrc = element.getAttribute('data-src') || '';
        if (dataSrc.includes(PROBLEMATIC_FILE)) {
            elementsToClean.push(element);
        }
    });
    
    // Buscar elementos con onclick que referencien el archivo
    const clickableElements = document.querySelectorAll('[onclick]');
    clickableElements.forEach(element => {
        const onclick = element.getAttribute('onclick') || '';
        if (onclick.includes(PROBLEMATIC_FILE)) {
            elementsToClean.push(element);
        }
    });
    
    // Limpiar elementos encontrados
    elementsToClean.forEach(element => {
        console.log(`❌ Limpiando elemento problemático:`, element);
        
        // Si es un contenedor multimedia, reemplazar con mensaje
        if (element.tagName.toLowerCase() === 'video' || element.tagName.toLowerCase() === 'audio') {
            const placeholder = document.createElement('div');
            placeholder.className = 'alert alert-warning';
            placeholder.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                Archivo multimedia no disponible
            `;
            element.parentNode.replaceChild(placeholder, element);
        } else {
            // Para otros elementos, simplemente remover o limpiar
            element.style.display = 'none';
        }
    });
    
    console.log(`✅ DOM limpiado: ${elementsToClean.length} elementos procesados`);
}

// Función para limpiar window.catalogData si existe
function cleanCatalogData() {
    console.log('🧹 Limpiando window.catalogData...');
    
    if (window.catalogData && window.catalogData.rows) {
        let cleanedRows = 0;
        
        window.catalogData.rows.forEach((row, index) => {
            if (typeof row === 'object' && row !== null) {
                Object.keys(row).forEach(key => {
                    if (typeof row[key] === 'string' && row[key].includes(PROBLEMATIC_FILE)) {
                        console.log(`❌ Limpiando fila ${index + 1}, campo ${key}`);
                        row[key] = ''; // Limpiar el campo
                        cleanedRows++;
                    }
                });
            }
        });
        
        console.log(`✅ catalogData limpiado: ${cleanedRows} campos procesados`);
    }
}

// Función principal de limpieza
function solveMp4Problem() {
    console.log('🚀 INICIANDO SOLUCIÓN COMPLETA DEL PROBLEMA MP4');
    
    try {
        cleanLocalStorage();
        cleanSessionStorage();
        interceptProblematicRequests();
        cleanDOMReferences();
        cleanCatalogData();
        
        console.log('✅ SOLUCIÓN COMPLETADA - Archivo MP4 problemático neutralizado');
        console.log('🔄 Recomendación: Recarga la página para aplicar todos los cambios');
        
        // Mostrar notificación al usuario
        if (typeof alert === 'function') {
            alert('Problema de archivo MP4 solucionado. Recarga la página para aplicar los cambios.');
        }
        
    } catch (error) {
        console.error('❌ Error durante la solución:', error);
    }
}

// Auto-ejecutar la solución
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', solveMp4Problem);
} else {
    solveMp4Problem();
}

// Hacer la función disponible globalmente
window.solveMp4Problem = solveMp4Problem;

console.log('🎬 Solucionador MP4 cargado. Ejecuta solveMp4Problem() para limpiar manualmente.');
"""
    
    return js_content

def main():
    print("🎬 SOLUCIONADOR DE PROBLEMA MP4 PROBLEMÁTICO")
    print("=" * 50)
    
    # Crear el script JavaScript
    js_content = create_cache_cleaner_script()
    
    # Guardar el script
    script_path = 'app/static/js/mp4-problem-solver.js'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Script solucionador creado: {script_path}")
    
    # Crear versión simplificada para la consola del navegador
    console_script = """
// SOLUCIÓN RÁPIDA - Pega esto en la consola del navegador:
(function() {
    const PROBLEMATIC_FILE = 'cf342a562c104122a5ca9241bf1ef896_oUcGqQXIG8InPCfTAIeSA2gneLBJnRIInz4jwY.MP4';
    
    // Limpiar localStorage
    Object.keys(localStorage).forEach(key => {
        if (localStorage.getItem(key).includes(PROBLEMATIC_FILE)) {
            localStorage.removeItem(key);
            console.log('Removed from localStorage:', key);
        }
    });
    
    // Limpiar sessionStorage
    Object.keys(sessionStorage).forEach(key => {
        if (sessionStorage.getItem(key).includes(PROBLEMATIC_FILE)) {
            sessionStorage.removeItem(key);
            console.log('Removed from sessionStorage:', key);
        }
    });
    
    // Limpiar catalogData
    if (window.catalogData && window.catalogData.rows) {
        window.catalogData.rows.forEach((row, index) => {
            Object.keys(row).forEach(key => {
                if (typeof row[key] === 'string' && row[key].includes(PROBLEMATIC_FILE)) {
                    row[key] = '';
                    console.log(`Cleaned row ${index + 1}, field ${key}`);
                }
            });
        });
    }
    
    console.log('✅ Problema MP4 solucionado. Recarga la página.');
    alert('Cache limpiado. Recarga la página.');
})();
"""
    
    console_path = 'mp4-console-fix.js'
    with open(console_path, 'w', encoding='utf-8') as f:
        f.write(console_script)
    
    print(f"✅ Script para consola creado: {console_path}")
    
    print("\n📋 INSTRUCCIONES:")
    print("1. Abre el navegador en la página problemática")
    print("2. Abre DevTools (F12)")
    print("3. Ve a la pestaña Console")
    print(f"4. Copia y pega el contenido de {console_path}")
    print("5. Presiona Enter")
    print("6. Recarga la página (F5)")
    
    print("\n🔧 SOLUCIÓN AUTOMÁTICA:")
    print(f"- Script creado: {script_path}")
    print("- Incluye este script en las páginas problemáticas")
    print("- Se ejecutará automáticamente al cargar")

if __name__ == "__main__":
    main()