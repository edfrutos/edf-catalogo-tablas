// MODAL FORCE DISPLAY - Solución definitiva para modales invisibles
console.log("🔧 MODAL-FORCE: Cargando sistema de forzado de modales...");

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔧 MODAL-FORCE: DOM cargado, inicializando...");
    
    // Función para crear panel de debug
    function createDebugPanel() {
        let panel = document.getElementById('modal-debug-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'modal-debug-panel';
            panel.className = 'modal-debug-panel';
            panel.style.cssText = `
                position: fixed; 
                bottom: 10px; 
                left: 10px; 
                background: rgba(0,0,0,0.9); 
                color: white; 
                padding: 10px; 
                font-family: monospace; 
                font-size: 11px; 
                z-index: 10002; 
                max-width: 350px; 
                border-radius: 5px; 
                border: 2px solid #00ff00;
                display: none;
            `;
            document.body.appendChild(panel);
        }
        return panel;
    }
    
    // Función para logging en panel de debug
    function debugLog(message, data = null) {
        console.log("🔧 MODAL-FORCE:", message, data);
        const panel = createDebugPanel();
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${message}`;
        if (data) {
            logEntry += `\nData: ${JSON.stringify(data, null, 2)}`;
        }
        panel.innerHTML += logEntry + '\n';
        panel.style.display = 'block';
        panel.scrollTop = panel.scrollHeight;
        
        // Auto-hide después de 10 segundos
        setTimeout(() => {
            if (panel.innerHTML.includes(logEntry)) {
                panel.style.display = 'none';
                panel.innerHTML = '';
            }
        }, 10000);
    }
    
    // Función para verificar estado del modal
    function checkModalState(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return { exists: false };
        
        const computedStyle = window.getComputedStyle(modal);
        const rect = modal.getBoundingClientRect();
        
        return {
            exists: true,
            display: computedStyle.display,
            visibility: computedStyle.visibility,
            opacity: computedStyle.opacity,
            zIndex: computedStyle.zIndex,
            position: computedStyle.position,
            hasShowClass: modal.classList.contains('show'),
            hasFadeClass: modal.classList.contains('fade'),
            rect: {
                width: rect.width,
                height: rect.height,
                top: rect.top,
                left: rect.left
            },
            style: modal.getAttribute('style') || 'none'
        };
    }
    
    // Función para forzar la visualización del modal
    function forceShowModal(modalId, title = 'Modal Debug') {
        debugLog(`Intentando forzar visualización de ${modalId}...`);
        
        const modal = document.getElementById(modalId);
        if (!modal) {
            debugLog(`ERROR: Modal ${modalId} no encontrado`);
            return false;
        }
        
        // Estado antes
        const stateBefore = checkModalState(modalId);
        debugLog(`Estado antes de forzar ${modalId}:`, stateBefore);
        
        // Remover todas las clases problemáticas
        modal.classList.remove('fade');
        
        // Forzar estilos directamente
        modal.style.cssText = `
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            z-index: 9999 !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: rgba(0, 0, 0, 0.5) !important;
            outline: 0 !important;
        `;
        
        // Agregar clase show
        modal.classList.add('show');
        
        // Forzar modal-dialog
        const modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.cssText = `
                transform: none !important;
                position: relative !important;
                z-index: 10000 !important;
                margin: 50px auto !important;
                pointer-events: auto !important;
            `;
        }
        
        // Forzar modal-content
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.cssText = `
                background-color: #fff !important;
                border: 3px solid #ff0000 !important;
                border-radius: 8px !important;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
                pointer-events: auto !important;
            `;
        }
        
        // Agregar clase modal-open al body
        document.body.classList.add('modal-open');
        document.body.style.overflow = 'hidden';
        
        // Estado después
        const stateAfter = checkModalState(modalId);
        debugLog(`Estado después de forzar ${modalId}:`, stateAfter);
        
        // Agregar handler para cerrar con ESC o click en backdrop
        const closeHandler = (e) => {
            if (e.key === 'Escape' || e.target === modal) {
                forceHideModal(modalId);
                document.removeEventListener('keydown', closeHandler);
                modal.removeEventListener('click', closeHandler);
            }
        };
        
        document.addEventListener('keydown', closeHandler);
        modal.addEventListener('click', closeHandler);
        
        debugLog(`Modal ${modalId} forzado a mostrar`);
        return true;
    }
    
    // Función para ocultar modal forzadamente
    function forceHideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('show');
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            debugLog(`Modal ${modalId} ocultado`);
        }
    }
    
    // Sobrescribir funciones originales con versión forzada
    const originalShowImageModal = window.showImageModal;
    const originalShowMultimediaModal = window.showMultimediaModal;
    const originalShowDocumentModal = window.showDocumentModal;
    
    window.showImageModal = function(imageUrl, title, catalogName) {
        debugLog("showImageModal FORZADO llamado", { imageUrl, title });
        
        // Intentar método original primero
        if (originalShowImageModal) {
            try {
                originalShowImageModal(imageUrl, title, catalogName);
                
                // Verificar si se mostró
                setTimeout(() => {
                    const state = checkModalState('imageModal');
                    debugLog("Estado después de método original:", state);
                    
                    if (!state.hasShowClass || state.display === 'none') {
                        debugLog("Método original falló, forzando visualización...");
                        forceShowModal('imageModal', title);
                        
                        // Configurar imagen
                        const img = document.getElementById('modalImage');
                        const titleEl = document.getElementById('imageModalLabel');
                        if (img) img.src = imageUrl;
                        if (titleEl) titleEl.textContent = title || 'Imagen';
                    }
                }, 100);
                
            } catch (error) {
                debugLog("Error en método original, forzando:", error);
                forceShowModal('imageModal', title);
            }
        } else {
            debugLog("No hay método original, forzando directamente");
            forceShowModal('imageModal', title);
        }
    };
    
    window.showMultimediaModal = function(multimediaUrl, title, catalogName) {
        debugLog("showMultimediaModal FORZADO llamado", { multimediaUrl, title });
        
        if (originalShowMultimediaModal) {
            try {
                originalShowMultimediaModal(multimediaUrl, title, catalogName);
                
                setTimeout(() => {
                    const state = checkModalState('multimediaModal');
                    if (!state.hasShowClass || state.display === 'none') {
                        forceShowModal('multimediaModal', title);
                        
                        // Configurar contenido multimedia
                        const content = document.getElementById('multimediaContent');
                        const titleEl = document.getElementById('multimediaModalLabel');
                        if (content) {
                            content.innerHTML = `
                                <div class="p-3 text-center">
                                    <h5>Archivo Multimedia</h5>
                                    <p><strong>URL:</strong> ${multimediaUrl}</p>
                                    <a href="${multimediaUrl}" target="_blank" class="btn btn-primary">
                                        <i class="fas fa-external-link-alt"></i> Abrir en nueva pestaña
                                    </a>
                                </div>
                            `;
                        }
                        if (titleEl) titleEl.textContent = title || 'Multimedia';
                    }
                }, 100);
                
            } catch (error) {
                debugLog("Error en multimedia original:", error);
                forceShowModal('multimediaModal', title);
            }
        } else {
            forceShowModal('multimediaModal', title);
        }
    };
    
    window.showDocumentModal = function(documentUrl, title, catalogName) {
        debugLog("showDocumentModal FORZADO llamado", { documentUrl, title });
        
        if (originalShowDocumentModal) {
            try {
                originalShowDocumentModal(documentUrl, title, catalogName);
                
                setTimeout(() => {
                    const state = checkModalState('documentModal');
                    if (!state.hasShowClass || state.display === 'none') {
                        forceShowModal('documentModal', title);
                        
                        // Configurar documento
                        const content = document.getElementById('documentContent');
                        const titleEl = document.getElementById('documentModalLabel');
                        if (content) {
                            content.innerHTML = `<iframe src="${documentUrl}" style="width: 100%; height: 500px; border: none;"></iframe>`;
                        }
                        if (titleEl) titleEl.textContent = title || 'Documento';
                    }
                }, 100);
                
            } catch (error) {
                debugLog("Error en documento original:", error);
                forceShowModal('documentModal', title);
            }
        } else {
            forceShowModal('documentModal', title);
        }
    };
    
    // Función de prueba global
    window.testModalForce = function() {
        debugLog("Iniciando test de forzado de modales...");
        setTimeout(() => showImageModal('https://via.placeholder.com/400x300', 'Test Forzado'), 1000);
    };
    
    // Debug info inicial
    debugLog("Sistema de forzado de modales inicializado");
    debugLog("Funciones disponibles: testModalForce()");
    
    console.log("🔧 MODAL-FORCE: Sistema de forzado inicializado completamente");
});