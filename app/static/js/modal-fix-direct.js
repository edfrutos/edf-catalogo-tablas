// SOLUCIÓN DIRECTA PARA MODALES - modal-fix-direct.js
console.log("🔧 MODAL-FIX: Cargando solución directa para modales...");

// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log("🔧 MODAL-FIX: DOM cargado, inicializando fix...");
    
    // Verificar que Bootstrap esté disponible
    if (typeof bootstrap === 'undefined') {
        console.error("🔧 MODAL-FIX: Bootstrap no disponible!");
        return;
    }
    
    // Verificar que los modales existan
    const imageModal = document.getElementById('imageModal');
    const multimediaModal = document.getElementById('multimediaModal');
    const documentModal = document.getElementById('documentModal');
    
    console.log("🔧 MODAL-FIX: Estado de modales:", {
        imageModal: !!imageModal,
        multimediaModal: !!multimediaModal,
        documentModal: !!documentModal
    });
    
    // FUNCIÓN DIRECTA PARA IMAGEN - Sobrescribir completamente
    window.showImageModal = function(imageUrl, title, _catalogName) {
        console.log("🔧 MODAL-FIX: showImageModal llamada directamente", { imageUrl, title });
        
        try {
            const modalElement = document.getElementById('imageModal');
            if (!modalElement) {
                console.error("🔧 MODAL-FIX: imageModal no encontrado");
                return;
            }
            
            const modalImage = document.getElementById('modalImage');
            const modalLabel = document.getElementById('imageModalLabel');
            
            if (modalImage && modalLabel) {
                modalImage.src = imageUrl;
                modalLabel.textContent = title || 'Imagen';
                window.currentImageUrl = imageUrl;
                
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log("🔧 MODAL-FIX: Modal de imagen mostrado exitosamente");
            } else {
                console.error("🔧 MODAL-FIX: Elementos del modal de imagen no encontrados");
            }
        } catch (error) {
            console.error("🔧 MODAL-FIX: Error en showImageModal:", error);
        }
    };
    
    // FUNCIÓN DIRECTA PARA MULTIMEDIA - Sobrescribir completamente
    window.showMultimediaModal = function(multimediaUrl, title, _catalogName) {
        console.log("🔧 MODAL-FIX: showMultimediaModal llamada directamente", { multimediaUrl, title });
        
        try {
            const modalElement = document.getElementById('multimediaModal');
            if (!modalElement) {
                console.error("🔧 MODAL-FIX: multimediaModal no encontrado");
                return;
            }
            
            const contentDiv = document.getElementById('multimediaContent');
            const modalLabel = document.getElementById('multimediaModalLabel');
            
            if (contentDiv && modalLabel) {
                modalLabel.textContent = title || 'Multimedia';
                window.currentMultimediaUrl = multimediaUrl;
                
                // Detectar tipo de archivo
                const extension = multimediaUrl.split('.').pop().toLowerCase();
                let content = '';
                
                if (['mp4', 'webm', 'ogg', 'avi', 'mov'].includes(extension)) {
                    content = `<video controls style="width: 100%; max-height: 400px;" preload="metadata">
                                <source src="${multimediaUrl}" type="video/${extension === 'mp4' ? 'mp4' : extension}">
                                Tu navegador no soporta el elemento video.
                               </video>`;
                } else if (['mp3', 'wav', 'ogg'].includes(extension)) {
                    content = `<audio controls style="width: 100%;">
                                <source src="${multimediaUrl}" type="audio/${extension}">
                                Tu navegador no soporta el elemento audio.
                               </audio>`;
                } else {
                    // Para URLs que no son archivos multimedia locales
                    content = `<div class="text-center p-4">
                                <h5>Contenido Multimedia</h5>
                                <p>URL: <code>${multimediaUrl}</code></p>
                                <a href="${multimediaUrl}" target="_blank" class="btn btn-primary">
                                    <i class="fas fa-external-link-alt"></i> Abrir en nueva pestaña
                                </a>
                               </div>`;
                }
                
                contentDiv.innerHTML = content;
                
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log("🔧 MODAL-FIX: Modal de multimedia mostrado exitosamente");
            } else {
                console.error("🔧 MODAL-FIX: Elementos del modal de multimedia no encontrados");
            }
        } catch (error) {
            console.error("🔧 MODAL-FIX: Error en showMultimediaModal:", error);
        }
    };
    
    // FUNCIÓN DIRECTA PARA DOCUMENTO - Sobrescribir completamente
    window.showDocumentModal = function(documentUrl, title, _catalogName) {
        console.log("🔧 MODAL-FIX: showDocumentModal llamada directamente", { documentUrl, title });
        
        try {
            const modalElement = document.getElementById('documentModal');
            if (!modalElement) {
                console.error("🔧 MODAL-FIX: documentModal no encontrado");
                return;
            }
            
            const contentDiv = document.getElementById('documentContent');
            const modalLabel = document.getElementById('documentModalLabel');
            
            if (contentDiv && modalLabel) {
                modalLabel.textContent = title || 'Documento';
                window.currentDocumentUrl = documentUrl;
                
                const content = `<iframe src="${documentUrl}" style="width: 100%; height: 500px; border: none;" 
                                         onload="console.log('🔧 MODAL-FIX: Documento cargado en iframe')" 
                                         onerror="console.error('🔧 MODAL-FIX: Error cargando documento en iframe')"></iframe>`;
                
                contentDiv.innerHTML = content;
                
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log("🔧 MODAL-FIX: Modal de documento mostrado exitosamente");
            } else {
                console.error("🔧 MODAL-FIX: Elementos del modal de documento no encontrados");
            }
        } catch (error) {
            console.error("🔧 MODAL-FIX: Error en showDocumentModal:", error);
        }
    };
    
    // FUNCIONES DE DESCARGA DIRECTAS
    window.downloadImage = function() {
        console.log("🔧 MODAL-FIX: downloadImage llamada");
        if (window.currentImageUrl) {
            window.open(window.currentImageUrl, '_blank');
        } else {
            console.warn("🔧 MODAL-FIX: No hay URL de imagen para descargar");
        }
    };
    
    window.downloadMultimedia = function() {
        console.log("🔧 MODAL-FIX: downloadMultimedia llamada");
        if (window.currentMultimediaUrl) {
            window.open(window.currentMultimediaUrl, '_blank');
        } else {
            console.warn("🔧 MODAL-FIX: No hay URL de multimedia para descargar");
        }
    };
    
    window.downloadDocument = function() {
        console.log("🔧 MODAL-FIX: downloadDocument llamada");
        if (window.currentDocumentUrl) {
            window.open(window.currentDocumentUrl, '_blank');
        } else {
            console.warn("🔧 MODAL-FIX: No hay URL de documento para descargar");
        }
    };
    
    // FUNCIÓN DE PRUEBA
    window.testModalsFix = function() {
        console.log("🔧 MODAL-FIX: Probando modales...");
        
        // Test imagen
        setTimeout(() => {
            console.log("🔧 MODAL-FIX: Probando modal de imagen...");
            // eslint-disable-next-line no-undef
            showImageModal('https://via.placeholder.com/400x300/0066cc/ffffff?text=TEST', 'Imagen de Prueba');
        }, 1000);
        
        // Test multimedia después de cerrar imagen
        setTimeout(() => {
            console.log("🔧 MODAL-FIX: Probando modal de multimedia...");
            const imageModalElement = document.getElementById('imageModal');
            const imageModal = bootstrap.Modal.getInstance(imageModalElement);
            if (imageModal) imageModal.hide();
            
            setTimeout(() => {
                // eslint-disable-next-line no-undef
                showMultimediaModal('https://www.w3schools.com/html/mov_bbb.mp4', 'Video de Prueba');
            }, 500);
        }, 3000);
    };
    
    // Inicialización completada
    console.log("🔧 MODAL-FIX: Funciones de modal reemplazadas exitosamente");
    console.log("🔧 MODAL-FIX: Usa testModalsFix() para probar");
    
    // Auto-test opcional (comentado por defecto)
    // setTimeout(testModalsFix, 2000);
});

console.log("🔧 MODAL-FIX: Script de solución directa cargado");