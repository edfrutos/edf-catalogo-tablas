// DEBUG: Enhanced modal functions with extensive logging
console.log("🔧 DEBUG: Loading enhanced modal functions with debugging...");

// Global debug flag
window.modalDebugMode = true;

function debugLog(message, data = null) {
    if (window.modalDebugMode) {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] MODAL-DEBUG: ${message}`);
        if (data) console.log('Data:', data);
    }
}

// Enhanced showImageModal with debugging
function showImageModalDebug(imageUrl, title, catalog_name = null) {
    debugLog('showImageModal called', { imageUrl, title, catalog_name });
    
    try {
        // Verify modal exists
        const modalElement = document.getElementById('imageModal');
        if (!modalElement) {
            debugLog('ERROR: imageModal element not found in DOM');
            return false;
        }
        
        debugLog('imageModal element found');
        
        // Verify Bootstrap is available
        if (typeof bootstrap === 'undefined') {
            debugLog('ERROR: Bootstrap not loaded');
            return false;
        }
        
        debugLog('Bootstrap is available');
        
        // Get modal components
        const modalImage = document.getElementById('modalImage');
        const modalLabel = document.getElementById('imageModalLabel');
        
        if (!modalImage) {
            debugLog('ERROR: modalImage element not found');
            return false;
        }
        
        if (!modalLabel) {
            debugLog('ERROR: imageModalLabel element not found');
            return false;
        }
        
        debugLog('All modal components found');
        
        // Set image and title
        modalImage.src = imageUrl;
        modalLabel.textContent = title || 'Imagen';
        
        debugLog('Image and title set', { src: modalImage.src, title: modalLabel.textContent });
        
        // Store URL for download function
        window.currentImageUrl = imageUrl;
        
        // Create and show modal
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        debugLog('Bootstrap Modal instance created');
        
        // Add event listeners for debugging
        modalElement.addEventListener('show.bs.modal', function() {
            debugLog('Modal show.bs.modal event fired');
        });
        
        modalElement.addEventListener('shown.bs.modal', function() {
            debugLog('Modal shown.bs.modal event fired');
        });
        
        modalElement.addEventListener('hide.bs.modal', function() {
            debugLog('Modal hide.bs.modal event fired');
        });
        
        modalElement.addEventListener('hidden.bs.modal', function() {
            debugLog('Modal hidden.bs.modal event fired');
        });
        
        // Show the modal
        debugLog('Attempting to show modal...');
        modal.show();
        debugLog('modal.show() called');
        
        return true;
        
    } catch (error) {
        debugLog('ERROR in showImageModalDebug: ' + error.message);
        console.error('Full error:', error);
        return false;
    }
}

// Enhanced showMultimediaModal with debugging
function showMultimediaModalDebug(multimediaUrl, title, catalog_name = null) {
    debugLog('showMultimediaModal called', { multimediaUrl, title, catalog_name });
    
    try {
        const modalElement = document.getElementById('multimediaModal');
        if (!modalElement) {
            debugLog('ERROR: multimediaModal element not found');
            return false;
        }
        
        if (typeof bootstrap === 'undefined') {
            debugLog('ERROR: Bootstrap not loaded');
            return false;
        }
        
        const contentDiv = document.getElementById('multimediaContent');
        const modalLabel = document.getElementById('multimediaModalLabel');
        
        if (!contentDiv || !modalLabel) {
            debugLog('ERROR: Multimedia modal components not found');
            return false;
        }
        
        // Set title
        modalLabel.textContent = title || 'Multimedia';
        
        // Store URL for download
        window.currentMultimediaUrl = multimediaUrl;
        
        // Determine content type and create appropriate element
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
            content = `<div class="text-center">
                        <p>Archivo multimedia no soportado para vista previa</p>
                        <a href="${multimediaUrl}" target="_blank" class="btn btn-primary">Abrir en nueva pestaña</a>
                       </div>`;
        }
        
        contentDiv.innerHTML = content;
        debugLog('Multimedia content set', { extension, contentLength: content.length });
        
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        debugLog('Attempting to show multimedia modal...');
        modal.show();
        debugLog('multimedia modal.show() called');
        
        return true;
        
    } catch (error) {
        debugLog('ERROR in showMultimediaModalDebug: ' + error.message);
        console.error('Full error:', error);
        return false;
    }
}

// Enhanced showDocumentModal with debugging
function showDocumentModalDebug(documentUrl, title, catalog_name = null) {
    debugLog('showDocumentModal called', { documentUrl, title, catalog_name });
    
    try {
        const modalElement = document.getElementById('documentModal');
        if (!modalElement) {
            debugLog('ERROR: documentModal element not found');
            return false;
        }
        
        if (typeof bootstrap === 'undefined') {
            debugLog('ERROR: Bootstrap not loaded');
            return false;
        }
        
        const contentDiv = document.getElementById('documentContent');
        const modalLabel = document.getElementById('documentModalLabel');
        
        if (!contentDiv || !modalLabel) {
            debugLog('ERROR: Document modal components not found');
            return false;
        }
        
        modalLabel.textContent = title || 'Documento';
        window.currentDocumentUrl = documentUrl;
        
        // Create iframe for document
        const content = `<iframe src="${documentUrl}" style="width: 100%; height: 500px; border: none;" 
                                 onload="console.log('Document iframe loaded')" 
                                 onerror="console.error('Document iframe error')"></iframe>`;
        
        contentDiv.innerHTML = content;
        debugLog('Document content set');
        
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        debugLog('Attempting to show document modal...');
        modal.show();
        debugLog('document modal.show() called');
        
        return true;
        
    } catch (error) {
        debugLog('ERROR in showDocumentModalDebug: ' + error.message);
        console.error('Full error:', error);
        return false;
    }
}

// Download functions with debugging
function downloadImageDebug() {
    debugLog('downloadImage called');
    if (window.currentImageUrl) {
        debugLog('Opening image URL: ' + window.currentImageUrl);
        window.open(window.currentImageUrl, '_blank');
    } else {
        debugLog('ERROR: No current image URL stored');
    }
}

function downloadMultimediaDebug() {
    debugLog('downloadMultimedia called');
    if (window.currentMultimediaUrl) {
        debugLog('Opening multimedia URL: ' + window.currentMultimediaUrl);
        window.open(window.currentMultimediaUrl, '_blank');
    } else {
        debugLog('ERROR: No current multimedia URL stored');
    }
}

function downloadDocumentDebug() {
    debugLog('downloadDocument called');
    if (window.currentDocumentUrl) {
        debugLog('Opening document URL: ' + window.currentDocumentUrl);
        window.open(window.currentDocumentUrl, '_blank');
    } else {
        debugLog('ERROR: No current document URL stored');
    }
}

// Override the original functions temporarily for debugging
if (window.modalDebugMode) {
    debugLog('Overriding original modal functions with debug versions');
    
    window.showImageModal = showImageModalDebug;
    window.showMultimediaModal = showMultimediaModalDebug;
    window.showDocumentModal = showDocumentModalDebug;
    window.downloadImage = downloadImageDebug;
    window.downloadMultimedia = downloadMultimediaDebug;
    window.downloadDocument = downloadDocumentDebug;
    
    debugLog('Debug modal functions are now active');
}

// Test function to verify everything works
function testAllModalsDebug() {
    debugLog('Starting modal test suite...');
    
    // Test basic modal existence
    const imageModal = document.getElementById('imageModal');
    const multimediaModal = document.getElementById('multimediaModal');
    const documentModal = document.getElementById('documentModal');
    
    debugLog('Modal elements check:', {
        imageModal: !!imageModal,
        multimediaModal: !!multimediaModal,
        documentModal: !!documentModal
    });
    
    // Test Bootstrap availability
    debugLog('Bootstrap check:', typeof bootstrap !== 'undefined');
    
    if (typeof bootstrap !== 'undefined') {
        debugLog('Bootstrap Modal class available:', typeof bootstrap.Modal !== 'undefined');
    }
    
    // Test function availability
    debugLog('Function availability:', {
        showImageModal: typeof window.showImageModal,
        showMultimediaModal: typeof window.showMultimediaModal,
        showDocumentModal: typeof window.showDocumentModal
    });
    
    return {
        modalElements: {
            imageModal: !!imageModal,
            multimediaModal: !!multimediaModal,
            documentModal: !!documentModal
        },
        bootstrap: typeof bootstrap !== 'undefined',
        functions: {
            showImageModal: typeof window.showImageModal,
            showMultimediaModal: typeof window.showMultimediaModal,
            showDocumentModal: typeof window.showDocumentModal
        }
    };
}

// Make test function globally available
window.testAllModalsDebug = testAllModalsDebug;

debugLog('Enhanced modal debugging script loaded completely');

// Auto-run test on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    debugLog('DOM loaded, running auto-test...');
    testAllModalsDebug();
});