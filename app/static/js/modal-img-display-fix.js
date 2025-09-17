// SOLUCIÓN PERMANENTE PARA MODAL IMG DISPLAY
// Soluciona el problema de display:none en la clase modal-img-display
console.log("🔧 MODAL IMG DISPLAY FIX: Cargando solución permanente...");

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔧 MODAL IMG DISPLAY FIX: DOM cargado, aplicando soluciones...");
    
    // 1. Crear CSS que sobrescriba la clase problemática
    const style = document.createElement('style');
    style.id = 'modal-img-display-fix';
    style.textContent = `
        /* SOLUCIÓN DEFINITIVA PARA MODAL-IMG-DISPLAY */
        .modal-img-display {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            max-width: 90% !important;
            max-height: 80vh !important;
            width: auto !important;
            height: auto !important;
            margin: 0 auto !important;
            object-fit: contain !important;
        }
        
        #modalImage {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            max-width: 90% !important;
            max-height: 80vh !important;
            width: auto !important;
            height: auto !important;
            margin: 0 auto !important;
            object-fit: contain !important;
        }
        
        /* Asegurar que el modal-body también sea visible */
        #imageModal .modal-body {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            text-align: center !important;
            padding: 20px !important;
        }
    `;
    
    // Verificar si ya existe el style antes de agregarlo
    if (!document.getElementById('modal-img-display-fix')) {
        document.head.appendChild(style);
        console.log("✅ CSS fix aplicado");
    }
    
    // 2. Función que fuerza la visualización de imágenes
    window.forceImageDisplay = function() {
        const img = document.getElementById('modalImage');
        if (img) {
            // Forzar estilos directamente
            img.style.setProperty('display', 'block', 'important');
            img.style.setProperty('visibility', 'visible', 'important');
            img.style.setProperty('opacity', '1', 'important');
            
            // Remover clases problemáticas
            img.classList.remove('d-none');
            
            console.log("🔧 MODAL IMG DISPLAY FIX: Imagen forzada a visible");
        }
    };
    
    // 3. Observer para detectar cambios en el DOM (ej: después de editar filas)
    const observer = new MutationObserver(function(mutations) {
        let shouldFix = false;
        
        mutations.forEach(function(mutation) {
            // Detectar cambios en atributos de estilo o clase
            if (mutation.type === 'attributes' && 
                (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                const target = mutation.target;
                if (target.id === 'modalImage' || target.classList.contains('modal-img-display')) {
                    shouldFix = true;
                }
            }
            
            // Detectar cambios en hijos (cuando se actualiza el DOM)
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        if (node.id === 'modalImage' || 
                            node.querySelector && node.querySelector('#modalImage')) {
                            shouldFix = true;
                        }
                    }
                });
            }
        });
        
        if (shouldFix) {
            setTimeout(window.forceImageDisplay, 50);
            setTimeout(window.forceImageDisplay, 200);
        }
    });
    
    // Observar cambios en toda la página
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'style', 'src']
    });
    
    console.log("✅ Observer instalado para cambios en DOM");
    
    // 4. Interceptar showImageModal para aplicar fix automáticamente
    const originalShowImageModal = window.showImageModal;
    if (originalShowImageModal) {
        window.showImageModal = function(imageSrc, imageTitle) {
            console.log("🔧 MODAL IMG DISPLAY FIX: showImageModal interceptado");
            const result = originalShowImageModal(imageSrc, imageTitle);
            
            // Aplicar fix múltiples veces para asegurar
            setTimeout(window.forceImageDisplay, 100);
            setTimeout(window.forceImageDisplay, 300);
            setTimeout(window.forceImageDisplay, 500);
            
            return result;
        };
        console.log("✅ showImageModal interceptado permanentemente");
    }
    
    // 5. También interceptar cuando se carga el modal-functions-UNIFIED.js
    // Solo interceptar si no existe conflicto
    if (!Object.getOwnPropertyDescriptor(window, 'showImageModal') || 
        Object.getOwnPropertyDescriptor(window, 'showImageModal').configurable) {
        try {
            const originalDefineProperty = Object.defineProperty;
            Object.defineProperty(window, 'showImageModal', {
                configurable: true,
                enumerable: true,
                get: function() {
                    return this._showImageModal;
                },
                set: function(value) {
                    if (typeof value === 'function' && !value._fixed) {
                        // Interceptar la nueva función
                this._showImageModal = function(imageSrc, imageTitle) {
                    console.log("🔧 MODAL IMG DISPLAY FIX: Nueva showImageModal interceptada");
                    const result = value(imageSrc, imageTitle);
                    
                    setTimeout(window.forceImageDisplay, 100);
                    setTimeout(window.forceImageDisplay, 300);
                    setTimeout(window.forceImageDisplay, 500);
                    
                    return result;
                };
                this._showImageModal._fixed = true;
            } else {
                this._showImageModal = value;
            }
        }
    });
        } catch (error) {
            console.log("⚠️ No se pudo redefinir showImageModal (ya existe):", error.message);
        }
    } else {
        console.log("⚠️ showImageModal no es configurable, saltando redefinición");
    }
    
    // 6. Aplicar fix inmediato si hay elementos
    setTimeout(window.forceImageDisplay, 1000);
    
    console.log("✅ MODAL IMG DISPLAY FIX: Solución permanente instalada completamente");
});