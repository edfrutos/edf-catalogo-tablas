// pywebview_compatibility.js - Mejoras de compatibilidad para pywebview
console.log("🔧 pywebview_compatibility.js cargado - Timestamp:", new Date().toISOString());

// Detectar si estamos en pywebview
window.isPyWebView = typeof pywebview !== 'undefined';

// Función para inicializar compatibilidad con pywebview
function initPyWebViewCompatibility() {
    console.log("🔧 Inicializando compatibilidad con pywebview...");
    
    // Configurar jQuery para funcionar mejor con pywebview
    if (typeof $ !== 'undefined') {
        // Mejorar el manejo de eventos en pywebview
        $(document).ready(function() {
            console.log("🔧 jQuery inicializado en pywebview");
            
            // Mejorar el manejo de modales
            $('.modal').on('shown.bs.modal', function() {
                console.log("🔧 Modal abierto en pywebview");
                // Forzar re-renderizado
                $(this).find('.modal-content').css('transform', 'scale(1)');
            });
            
            // Mejorar el manejo de tooltips
            $('[data-bs-toggle="tooltip"]').tooltip({
                container: 'body',
                trigger: 'hover focus'
            });
            
            // Mejorar el manejo de popovers
            $('[data-bs-toggle="popover"]').popover({
                container: 'body',
                trigger: 'click'
            });
        });
    }
    
    // Mejorar el manejo de formularios
    document.addEventListener('submit', function(e) {
        console.log("🔧 Formulario enviado en pywebview");
        
        // Prevenir envío múltiple
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            // Guardar el texto original del botón
            const originalText = submitBtn.innerHTML;
            const originalDisabled = submitBtn.disabled;
            
            // Deshabilitar botón y mostrar spinner
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
            
            // Restaurar botón después de 30 segundos (timeout de seguridad)
            const timeoutId = setTimeout(() => {
                console.log("🔧 Timeout de seguridad: restaurando botón");
                submitBtn.disabled = originalDisabled;
                submitBtn.innerHTML = originalText;
            }, 30000);
            
            // Restaurar botón cuando la página se recarga o cambia
            const restoreButton = () => {
                clearTimeout(timeoutId);
                submitBtn.disabled = originalDisabled;
                submitBtn.innerHTML = originalText;
            };
            
            // Eventos para restaurar el botón
            window.addEventListener('beforeunload', restoreButton);
            window.addEventListener('pagehide', restoreButton);
            
            // Restaurar después de 5 segundos si no hay respuesta (fallback)
            setTimeout(() => {
                if (submitBtn.innerHTML.includes('Procesando...')) {
                    console.log("🔧 Fallback: restaurando botón después de 5 segundos");
                    restoreButton();
                }
            }, 5000);
        }
        
        // Asegurar que los datos se envíen correctamente
        if (form.method === 'post') {
            // Agregar timestamp para evitar caché
            const timestamp = document.createElement('input');
            timestamp.type = 'hidden';
            timestamp.name = '_timestamp';
            timestamp.value = Date.now();
            form.appendChild(timestamp);
            
            // Agregar token CSRF si existe
            const csrfToken = document.querySelector('meta[name="csrf-token"]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = csrfToken.getAttribute('content');
                form.appendChild(csrfInput);
            }
        }
        
        // Permitir que el formulario se envíe normalmente
        return true;
    });
    
    // Mejorar el manejo de enlaces
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' && e.target.href) {
            console.log("🔧 Enlace clickeado en pywebview:", e.target.href);
            // Permitir que los enlaces funcionen normalmente
        }
    });
    
    // Mejorar el manejo de AJAX
    if (typeof $ !== 'undefined') {
        $.ajaxSetup({
            cache: false,
            timeout: 30000,
            error: function(xhr, status, error) {
                console.error("🔧 Error AJAX en pywebview:", error);
                console.error("🔧 Status:", status);
                console.error("🔧 Response:", xhr.responseText);
            }
        });
    }
    
    // Mejorar el manejo de WebSockets si están disponibles
    if (typeof WebSocket !== 'undefined') {
        console.log("🔧 WebSockets disponibles en pywebview");
    }
    
    // Mejorar el manejo de localStorage
    try {
        localStorage.setItem('pywebview_test', 'test');
        localStorage.removeItem('pywebview_test');
        console.log("🔧 localStorage funciona en pywebview");
    } catch (e) {
        console.warn("🔧 localStorage no disponible en pywebview:", e);
    }
    
    // Mejorar el manejo de sessionStorage
    try {
        sessionStorage.setItem('pywebview_test', 'test');
        sessionStorage.removeItem('pywebview_test');
        console.log("🔧 sessionStorage funciona en pywebview");
    } catch (e) {
        console.warn("🔧 sessionStorage no disponible en pywebview:", e);
    }
    
    // Mejorar el manejo de cookies
    document.cookie = "pywebview_test=test; path=/";
    if (document.cookie.includes('pywebview_test')) {
        console.log("🔧 Cookies funcionan en pywebview");
        // Limpiar cookie de prueba
        document.cookie = "pywebview_test=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    } else {
        console.warn("🔧 Cookies no funcionan correctamente en pywebview");
    }
}

// Función para restaurar botones manualmente
function restoreSubmitButtons() {
    console.log("🔧 Restaurando botones de envío...");
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(btn => {
        if (btn.innerHTML.includes('Procesando...')) {
            btn.disabled = false;
            // Intentar restaurar texto original o usar texto por defecto
            const originalText = btn.getAttribute('data-original-text') || 'Enviar';
            btn.innerHTML = originalText;
            console.log("🔧 Botón restaurado:", btn);
        }
    });
}

// Función para mejorar el manejo de alertas en pywebview
function showPyWebViewAlert(message, type = 'info') {
    console.log(`🔧 showPyWebViewAlert: ${message} (${type})`);
    
    // Crear alerta personalizada para pywebview
    const alertId = `pywebview-alert-${Date.now()}`;
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <strong>${type.toUpperCase()}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        </div>
    `;
    
    // Insertar al inicio del contenedor principal
    const container = document.querySelector('.container') || document.body;
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Función para manejar errores específicos de pywebview
function handlePyWebViewError(error) {
    console.error("🔧 Error en pywebview:", error);
    
    // Restaurar botones que puedan estar en estado "Procesando..."
    restoreSubmitButtons();
    
    // Remover alertas de error existentes
    const existingAlerts = document.querySelectorAll('.alert-warning');
    existingAlerts.forEach(alert => {
        if (alert.textContent.includes('Ha ocurrido un error al procesar la solicitud')) {
            alert.remove();
        }
    });
    
    // Mostrar mensaje de error más específico
    showPyWebViewAlert(`Error: ${error.message || 'Error desconocido'}`, 'danger');
}

// Función para mejorar el manejo de confirmaciones en pywebview
function showPyWebViewConfirm(message, callback) {
    console.log(`🔧 showPyWebViewConfirm: ${message}`);
    
    // Crear modal de confirmación personalizado
    const modalId = `pywebview-confirm-${Date.now()}`;
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirmar acción</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="confirmAction('${modalId}', true)">Confirmar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Agregar al body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
    
    // Configurar callback
    window.confirmAction = function(modalId, confirmed) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        modal.hide();
        
        // Limpiar modal después de ocultar
        setTimeout(() => {
            const modalElement = document.getElementById(modalId);
            if (modalElement) {
                modalElement.remove();
            }
        }, 300);
        
        if (callback) {
            callback(confirmed);
        }
    };
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPyWebViewCompatibility);
} else {
    initPyWebViewCompatibility();
}

// Manejador global de errores para pywebview
window.addEventListener('error', function(e) {
    console.error("🔧 Error global detectado:", e.error);
    handlePyWebViewError(e.error);
});

// Manejador de errores no capturados
window.addEventListener('unhandledrejection', function(e) {
    console.error("🔧 Promesa rechazada no manejada:", e.reason);
    handlePyWebViewError(e.reason);
});

// Exportar funciones para uso global
window.showPyWebViewAlert = showPyWebViewAlert;
window.showPyWebViewConfirm = showPyWebViewConfirm;
window.initPyWebViewCompatibility = initPyWebViewCompatibility;
window.handlePyWebViewError = handlePyWebViewError;
window.restoreSubmitButtons = restoreSubmitButtons; // Exportar la nueva función

console.log("🔧 pywebview_compatibility.js inicializado completamente");
