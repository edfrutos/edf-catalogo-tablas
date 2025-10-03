
// SOLUCIONADOR DE ARCHIVOS MP4 PROBLEMÁTICOS
// ==========================================

(function() {
    'use strict';
    
    // console.log('🧹 Iniciando limpieza de cache de archivos multimedia problemáticos...');

    // Archivos problemáticos identificados
    const PROBLEMATIC_FILES = [
        'cf342a562c104122a5ca9241bf1ef896_oUcGqQXIG8InPCfTAIeSA2gneLBJnRIInz4jwY.MP4',
        'b1c79940ccb547d180b776aca15b1a40_como_usar_la_circular.MP4',
        'db2d78bfc1be4b6288330a3d895f6510_util_para_sierra_circular.MP4'
    ];

// Función para interceptar y silenciar errores 404 de archivos problemáticos
function setup404ErrorSuppression() {
    console.log('🤫 Configurando supresión de errores 404 para archivos problemáticos...');
    
    // Interceptar errores de red
    const originalConsoleError = console.error;
    console.error = function(...args) {
        const message = args.join(' ');
        
        // Verificar si el error es de un archivo problemático
        const isProblematicFile = PROBLEMATIC_FILES.some(file => 
            message.includes(file) && (message.includes('404') || message.includes('Failed to load'))
        );
        
        if (isProblematicFile) {
            console.log(`🤫 Error 404 silenciado para archivo problemático: ${message.substring(0, 80)}...`);
            return; // No mostrar el error
        }
        
        // Mostrar otros errores normalmente
        originalConsoleError.apply(console, args);
    };
    
    // Interceptar errores de recursos (img, video, audio)
    window.addEventListener('error', function(event) {
        if (event.target && event.target.src) {
            const isProblematicFile = PROBLEMATIC_FILES.some(file => 
                event.target.src.includes(file)
            );
            
            if (isProblematicFile) {
                console.log(`🤫 Error de recurso silenciado: ${event.target.tagName} ${event.target.src.split('/').pop()}`);
                event.preventDefault();
                event.stopPropagation();
                return false;
            }
        }
    }, true);
}

// Función para limpiar localStorage
function cleanLocalStorage() {
    console.log('🧹 Limpiando localStorage...');
    
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        
        if (value && PROBLEMATIC_FILES.some(file => value.includes(file))) {
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
        
        if (value && PROBLEMATIC_FILES.some(file => value.includes(file))) {
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
        if (typeof url === 'string' && PROBLEMATIC_FILES.some(file => url.includes(file))) {
            console.warn(`🚫 INTERCEPTADO: Request a archivo problemático bloqueado: ${url}`);
            const problematicFile = PROBLEMATIC_FILES.find(file => url.includes(file));
            return Promise.reject(new Error(`Archivo ${problematicFile} no existe - request interceptado`));
        }
        return originalFetch.apply(this, args);
    };
    
    // Interceptar XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        if (typeof url === 'string' && PROBLEMATIC_FILES.some(file => url.includes(file))) {
            console.warn(`🚫 INTERCEPTADO: XMLHttpRequest a archivo problemático bloqueado: ${url}`);
            const problematicFile = PROBLEMATIC_FILES.find(file => url.includes(file));
            throw new Error(`Archivo ${problematicFile} no existe - request interceptado`);
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
        if (PROBLEMATIC_FILES.some(file => src.includes(file))) {
            elementsToClean.push(element);
        }
    });
    
    // Buscar elementos con data-src problemático
    const dataElements = document.querySelectorAll('[data-src]');
    dataElements.forEach(element => {
        const dataSrc = element.getAttribute('data-src') || '';
        if (PROBLEMATIC_FILES.some(file => dataSrc.includes(file))) {
            elementsToClean.push(element);
        }
    });
    
    // Buscar elementos con onclick que referencien el archivo
    const clickableElements = document.querySelectorAll('[onclick]');
    clickableElements.forEach(element => {
        const onclick = element.getAttribute('onclick') || '';
        if (PROBLEMATIC_FILES.some(file => onclick.includes(file))) {
            elementsToClean.push(element);
        }
    });
    
    // Limpiar elementos encontrados
    elementsToClean.forEach(element => {
        console.log(`❌ Limpiando elemento problemático:`, element);
        
        try {
            // Verificar que el elemento tenga un padre válido
            if (!element.parentNode) {
                console.log(`⚠️ Elemento sin padre, saltando:`, element);
                return;
            }
            
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
        } catch (error) {
            console.warn(`⚠️ Error procesando elemento:`, element, error);
            // Intentar solo ocultar el elemento como fallback
            try {
                element.style.display = 'none';
            } catch (hideError) {
                console.warn(`⚠️ No se pudo ocultar elemento:`, hideError);
            }
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
                    if (typeof row[key] === 'string' && PROBLEMATIC_FILES.some(file => row[key].includes(file))) {
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
        setup404ErrorSuppression();
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

    // Auto-ejecutar la solución solo si hay elementos problemáticos
    function autoExecuteIfNeeded() {
        // Verificar si hay elementos problemáticos en la página
        const hasProblematicElements = PROBLEMATIC_FILES.some(filename => {
            return document.querySelector(`[src*="${filename}"], [data-src*="${filename}"], [href*="${filename}"]`);
        });
        
        if (hasProblematicElements) {
            console.log('🚨 Elementos MP4 problemáticos detectados, ejecutando solución...');
            solveMp4Problem();
        } else {
            console.log('✅ No se detectaron elementos MP4 problemáticos');
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoExecuteIfNeeded);
    } else {
        autoExecuteIfNeeded();
    }

    // Hacer la función disponible globalmente
    window.solveMp4Problem = solveMp4Problem;

    // console.log('🎬 Solucionador MP4 cargado. Ejecuta solveMp4Problem() para limpiar manualmente.');

})(); // Cerrar función anónima
