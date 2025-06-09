console.log("Script cargado correctamente");

// Función para manejar mensajes de error de extensiones
function handleExtensionErrors() {
    // Verificar si estamos en Chrome
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.lastError) {
        // Guardar la función de error original
        const originalError = console.error;
        
        // Sobrescribir console.error para filtrar mensajes específicos
        console.error = function() {
            // Ignorar errores de cierre de puerto de mensajes
            if (arguments[0] && 
                (arguments[0].includes('The message port closed before a response was received') ||
                 arguments[0].message === 'The message port closed before a response was received')) {
                return;
            }
            // Mantener el stack trace para otros errores
            return originalError.apply(console, arguments);
        };
        
        // Manejar errores no capturados
        window.addEventListener('error', function(event) {
            if (event.message && event.message.includes('message port closed')) {
                event.preventDefault();
                event.stopPropagation();
                return false;
            }
        });
    }
}

// Función para limpiar antes de descargar la página
function setupPageUnload() {
    // Usar pagehide en lugar de unload para mejor compatibilidad
    window.addEventListener('pagehide', function() {
        // Limpiar cualquier listener de mensajes de extensiones
        if (chrome && chrome.runtime && chrome.runtime.onMessage) {
            chrome.runtime.onMessage.removeListener();
        }
        
        // Limpiar timeouts pendientes
        const maxTimeoutId = setTimeout(() => {}, 0);
        for (let i = 1; i < maxTimeoutId; i++) {
            clearTimeout(i);
        }
    }, false);
}

// Inicializar manejadores
document.addEventListener('DOMContentLoaded', function() {
    handleExtensionErrors();
    setupPageUnload();
});
