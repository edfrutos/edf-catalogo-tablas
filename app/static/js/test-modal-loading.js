// Script de prueba para verificar carga de funciones del modal
console.log("[TEST-MODAL] 🔍 Verificando carga de funciones del modal...");

// Esperar a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log("[TEST-MODAL] 📄 DOM cargado, verificando funciones...");
    
    // Verificar funciones principales
    const functions = [
        'showImageModal',
        'showDocumentModal', 
        'showMultimediaModal',
        'downloadImage',
        'handleImageError'
    ];
    
    let allFunctionsLoaded = true;
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`[TEST-MODAL] ✅ ${funcName}: CARGADA`);
        } else {
            console.log(`[TEST-MODAL] ❌ ${funcName}: NO CARGADA`);
            allFunctionsLoaded = false;
        }
    });
    
    if (allFunctionsLoaded) {
        console.log("[TEST-MODAL] 🎉 Todas las funciones están disponibles");
    } else {
        console.log("[TEST-MODAL] ⚠️ Algunas funciones no están disponibles");
    }
    
    // Verificar elementos del modal
    const modalElements = [
        'imageModal',
        'documentModal', 
        'multimediaModal',
        'modalImage',
        'documentContent',
        'multimediaContent'
    ];
    
    modalElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            console.log(`[TEST-MODAL] ✅ Elemento ${elementId}: ENCONTRADO`);
        } else {
            console.log(`[TEST-MODAL] ❌ Elemento ${elementId}: NO ENCONTRADO`);
        }
    });
});

// Verificación inmediata también
console.log("[TEST-MODAL] 🔍 Verificación inmediata:");
console.log("  - showImageModal:", typeof window.showImageModal);
console.log("  - showDocumentModal:", typeof window.showDocumentModal);
console.log("  - showMultimediaModal:", typeof window.showMultimediaModal);
