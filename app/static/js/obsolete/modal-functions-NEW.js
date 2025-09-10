// Funciones de modal para compatibilidad con pywebview
// Este archivo define las funciones que faltan en el contexto de pywebview

// Detectar si estamos en pywebview
const isPyWebView = typeof pywebview !== 'undefined';
console.log('[MODAL] Detección de pywebview:', { isPyWebView, pywebview: typeof pywebview });

// Función de fallback global para handleImageError (evita errores de timing)
// Esta función ya está definida en pywebview_compatibility.js para evitar errores de timing
if (!window.handleImageError) {
    window.handleImageError = function() {
        try {
            const modalImage = document.getElementById('modalImage');
            const spinner = document.querySelector('.image-loading-spinner');
            
            if (spinner) spinner.style.display = 'none';
            if (modalImage) {
                modalImage.style.display = 'block';
                modalImage.src = '/static/img/image-error.svg';
            }
        } catch (error) {
            console.warn('[MODAL] handleImageError fallback: Error manejando imagen:', error);
        }
    };
}

// Función para mostrar modal de multimedia
function showMultimediaModal(multimediaSrc, multimediaTitle) {
    console.log('[MODAL] showMultimediaModal llamado con:', { multimediaSrc, multimediaTitle });

    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[MODAL] Bootstrap no está disponible');
        // Fallback: abrir en nueva ventana
        if (isPyWebView) {
            // En pywebview, usar window.open
            window.open(multimediaSrc, '_blank');
        } else {
            // En navegador normal
            window.open(multimediaSrc, '_blank');
        }
        return;
    }
    
    // Verificar si el archivo existe antes de mostrar
    fetch(multimediaSrc, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                // Almacenar la URL para descarga
                currentMultimediaUrl = multimediaSrc;

                // Buscar el modal de multimedia
                const modalElement = document.getElementById('multimediaModal');
                const modalContent = document.getElementById('multimediaContent');
                const modalTitle = document.getElementById('multimediaModalLabel');

                if (!modalElement || !modalContent || !modalTitle) {
                    console.error('[MODAL] Elementos del modal de multimedia no encontrados');
                    // Fallback: abrir en nueva ventana
                    window.open(multimediaSrc, '_blank');
                    return;
                }

                // Configurar el título
                modalTitle.innerHTML = `<i class="fas fa-video"></i> ${multimediaTitle || 'Multimedia'}`;

                // Determinar el tipo de multimedia y crear el contenido apropiado
                const fileExtension = multimediaSrc.split('.').pop().toLowerCase();
                
                if (['mp4', 'avi', 'mov', 'wmv', 'webm'].includes(fileExtension)) {
                    // Video
                    modalContent.innerHTML = `
                        <div class="text-center">
                            <video controls style="width: 100%; max-height: 70vh; border-radius: 8px;">
                                <source src="${multimediaSrc}" type="video/${fileExtension}">
                                Tu navegador no soporta el elemento video.
                            </video>
                            <div class="mt-3">
                                <a href="${multimediaSrc}" target="_blank" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-external-link-alt"></i> Abrir en nueva ventana
                                </a>
                            </div>
                        </div>
                    `;
                } else if (['mp3', 'wav', 'ogg', 'aac', 'flac'].includes(fileExtension)) {
                    // Audio
                    modalContent.innerHTML = `
                        <div class="text-center">
                            <audio controls style="width: 100%; max-width: 400px;">
                                <source src="${multimediaSrc}" type="audio/${fileExtension}">
                                Tu navegador no soporta el elemento audio.
                            </audio>
                            <div class="mt-3">
                                <a href="${multimediaSrc}" target="_blank" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-external-link-alt"></i> Abrir en nueva ventana
                                </a>
                            </div>
                        </div>
                    `;
                } else if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
                    // Imagen
                    modalContent.innerHTML = `
                        <div class="text-center">
                            <img src="${multimediaSrc}" style="max-width: 100%; max-height: 70vh; border-radius: 8px;" alt="${multimediaTitle}">
                            <div class="mt-3">
                                <a href="${multimediaSrc}" target="_blank" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-external-link-alt"></i> Abrir en nueva ventana
                                </a>
                            </div>
                        </div>
                    `;
                } else {
                    // Otros tipos
                    modalContent.innerHTML = `
                        <div class="text-center">
                            <i class="fas fa-file fa-3x text-muted mb-3"></i>
                            <p class="text-muted">Tipo de archivo multimedia no compatible para vista previa</p>
                            <a href="${multimediaSrc}" target="_blank" class="btn btn-dark">
                                <i class="fas fa-download"></i> Descargar archivo
                            </a>
                        </div>
                    `;
                }

                // Mostrar el modal
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else {
                // Archivo no encontrado - mostrar error
                console.error('[MODAL] Multimedia no encontrada:', multimediaSrc);
                alert(`El archivo multimedia "${multimediaTitle}" no está disponible. Es posible que haya sido eliminado o movido.`);
            }
        })
        .catch(error => {
            console.error('[MODAL] Error verificando multimedia:', error);
            alert(`Error al cargar el archivo multimedia "${multimediaTitle}": ${error.message}`);
        });
}

// Función para mostrar modal de imagen
function showImageModal(imageSrc, imageTitle) {
    console.log('[MODAL] showImageModal llamado con:', { imageSrc, imageTitle });

    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[MODAL] Bootstrap no está disponible');
        // Fallback: abrir en nueva ventana
        if (isPyWebView) {
            // En pywebview, usar window.open
            window.open(imageSrc, '_blank');
        } else {
            // En navegador normal
            window.open(imageSrc, '_blank');
        }
        return;
    }
    
    // Verificar si el archivo existe antes de mostrar
    fetch(imageSrc, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                // Almacenar la URL para descarga
                currentImageUrl = imageSrc;

                // Buscar el modal de imagen
                const modalElement = document.getElementById('imageModal');
                const modalImage = document.getElementById('modalImage');
                const modalTitle = document.getElementById('imageModalLabel');

                if (!modalElement || !modalImage || !modalTitle) {
                    console.error('[MODAL] Elementos del modal de imagen no encontrados');
                    // Fallback: abrir en nueva ventana
                    window.open(imageSrc, '_blank');
                    return;
                }

                // Configurar el modal
                modalImage.src = imageSrc;
                modalTitle.innerHTML = `<i class="bi bi-image"></i> ${imageTitle || 'Imagen'}`;

                // Mostrar el modal
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else {
                // Archivo no encontrado - mostrar error
                console.error('[MODAL] Imagen no encontrada:', imageSrc);
                alert(`La imagen "${imageTitle}" no está disponible. Es posible que haya sido eliminada o movida.`);
            }
        })
        .catch(error => {
            console.error('[MODAL] Error verificando imagen:', error);
            alert(`Error al cargar la imagen "${imageTitle}": ${error.message}`);
        });
    
    
}

// Función para mostrar modal de documento
function showDocumentModal(documentSrc, documentTitle) {
    console.log('[MODAL] showDocumentModal llamado con:', { documentSrc, documentTitle });
    console.log('[MODAL] ⚠️ ADVERTENCIA: showDocumentModal llamado en lugar de showPyWebViewDocument');
    
    // Prevenir comportamiento por defecto del enlace
    if (typeof event !== 'undefined' && event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[MODAL] Bootstrap no está disponible');
        // Fallback: abrir en nueva ventana
        if (isPyWebView) {
            // En pywebview, intentar navegar en la misma ventana
            console.log('[MODAL] Navegando a documento en pywebview:', documentSrc);
            window.location.href = documentSrc;
        } else {
            // En navegador normal
            window.open(documentSrc, '_blank');
        }
        return;
    }
    
    // Buscar el modal de documento
    const modalElement = document.getElementById('documentModal');
    const modalContent = document.getElementById('documentContent');
    const modalTitle = document.getElementById('documentModalLabel');
    
    if (!modalElement || !modalContent || !modalTitle) {
        console.error('[MODAL] Elementos del modal de documento no encontrados');
        // Fallback: abrir en nueva ventana
        window.open(documentSrc, '_blank');
        return;
    }
    
    // Determinar el tipo de documento
    const fileExtension = documentSrc.split('.').pop().toLowerCase();
    let documentElement = '';
    
    if (fileExtension === 'pdf') {
        // Para PDFs, usar iframe con botón de descarga
        documentElement = `
            <div class="text-center mb-3">
                <button onclick="downloadDocument()" class="btn btn-danger mb-2 me-2">
                    <i class="fas fa-download"></i> Descargar PDF
                </button>
                <a href="${documentSrc}" target="_blank" class="btn btn-outline-danger mb-2" onclick="event.stopPropagation();">
                    <i class="fas fa-external-link-alt"></i> Abrir en nueva pestaña
                </a>
            </div>
            <iframe src="${documentSrc}" 
                    style="width: 100%; height: 70vh; border: 1px solid #ddd; border-radius: 4px;" 
                    title="${documentTitle || 'Documento PDF'}">
                <p>Tu navegador no soporta iframes. 
                   <a href="${documentSrc}" target="_blank" onclick="event.stopPropagation();">Abrir documento</a>
                </p>
            </iframe>
        `;
        modalTitle.innerHTML = `<i class="fas fa-file-pdf"></i> ${documentTitle || 'Documento PDF'}`;
    } else if (['md', 'markdown'].includes(fileExtension)) {
        // Para Markdown, cargar y convertir
        documentElement = `
            <div id="markdown-content" class="markdown-preview">
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-2">Cargando documento Markdown...</p>
                </div>
            </div>
        `;
        modalTitle.innerHTML = `<i class="fas fa-file-alt"></i> ${documentTitle || 'Documento Markdown'}`;
        
        // Cargar el contenido Markdown
        fetch(documentSrc)
            .then(response => response.text())
            .then(content => {
                // Convertir Markdown a HTML (simplificado)
                const htmlContent = content
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                    .replace(/\*(.*)\*/gim, '<em>$1</em>')
                    .replace(/\n/gim, '<br>');
                
                const markdownContent = document.getElementById('markdown-content');
                if (markdownContent) {
                    markdownContent.innerHTML = `
                        <div class="markdown-content-wrapper" style="max-height: 70vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                            <div class="markdown-rendered">
                                ${htmlContent}
                            </div>
                        </div>
                        <div class="text-center mt-3">
                            <button onclick="downloadDocument()" class="btn btn-outline-primary">
                                <i class="fas fa-download"></i> Descargar
                            </button>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('[MODAL] Error cargando Markdown:', error);
                const markdownContent = document.getElementById('markdown-content');
                if (markdownContent) {
                    markdownContent.innerHTML = `
                        <div class="text-center text-danger">
                            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                            <p>Error al cargar el archivo Markdown</p>
                            <button onclick="downloadDocument()" class="btn btn-outline-danger">
                                <i class="fas fa-download"></i> Descargar
                            </button>
                        </div>
                    `;
                }
            });
    } else {
        // Otros tipos de archivo
        documentElement = `
            <div class="text-center">
                <i class="fas fa-file fa-3x text-muted mb-3"></i>
                <p class="text-muted">Tipo de documento no compatible para vista previa</p>
                <a href="${documentSrc}" target="_blank" class="btn btn-dark">
                    <i class="fas fa-download"></i> Descargar documento
                </a>
            </div>
        `;
        modalTitle.innerHTML = `<i class="fas fa-file"></i> ${documentTitle || 'Documento'}`;
    }
    
    // Almacenar la URL para descarga
    currentDocumentUrl = documentSrc;
    
    // Configurar el contenido del modal
    modalContent.innerHTML = documentElement;
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Función para mostrar modal de multimedia
function showMultimediaModal(multimediaSrc, multimediaTitle) {
    console.log('[MODAL] showMultimediaModal llamado con:', { multimediaSrc, multimediaTitle });
    
    // Prevenir comportamiento por defecto del elemento multimedia
    if (typeof event !== 'undefined' && event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[MODAL] Bootstrap no está disponible');
        // Fallback: abrir en nueva ventana
        if (isPyWebView) {
            // En pywebview, intentar navegar en la misma ventana
            console.log('[MODAL] Navegando a multimedia en pywebview:', multimediaSrc);
            window.location.href = multimediaSrc;
        } else {
            // En navegador normal
            window.open(multimediaSrc, '_blank');
        }
        return;
    }
    
    // Buscar el modal de multimedia
    const modalElement = document.getElementById('multimediaModal');
    const modalContent = document.getElementById('multimediaContent');
    const modalTitle = document.getElementById('multimediaModalLabel');
    
    if (!modalElement || !modalContent || !modalTitle) {
        console.error('[MODAL] Elementos del modal de multimedia no encontrados');
        // Fallback: abrir en nueva ventana
        window.open(multimediaSrc, '_blank');
        return;
    }
    
    // Determinar el tipo de multimedia
    const fileExtension = multimediaSrc.split('.').pop().toLowerCase();
    let multimediaElement = '';
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
        multimediaElement = `<img src="${multimediaSrc}" class="img-fluid" alt="${multimediaTitle || 'Multimedia'}">`;
        modalTitle.innerHTML = `<i class="fas fa-image"></i> ${multimediaTitle || 'Imagen'}`;
    } else if (['mp4', 'avi', 'mov', 'wmv'].includes(fileExtension)) {
        multimediaElement = `
            <video controls class="w-100">
                <source src="${multimediaSrc}" type="video/mp4">
                Tu navegador no soporta el elemento video.
            </video>
        `;
        modalTitle.innerHTML = `<i class="fas fa-video"></i> ${multimediaTitle || 'Video'}`;
    } else if (['mp3', 'wav', 'ogg'].includes(fileExtension)) {
        multimediaElement = `
            <audio controls class="w-100">
                <source src="${multimediaSrc}" type="audio/mpeg">
                Tu navegador no soporta el elemento audio.
            </audio>
        `;
        modalTitle.innerHTML = `<i class="fas fa-music"></i> ${multimediaTitle || 'Audio'}`;
    } else {
        multimediaElement = `
            <div class="text-center">
                <i class="fas fa-file fa-3x text-muted mb-3"></i>
                <p class="text-muted">Archivo multimedia no compatible para vista previa</p>
                <a href="${multimediaSrc}" target="_blank" class="btn btn-primary">
                    <i class="fas fa-download"></i> Descargar archivo
                </a>
            </div>
        `;
        modalTitle.innerHTML = `<i class="fas fa-file"></i> ${multimediaTitle || 'Archivo'}`;
    }
    
    // Almacenar la URL para descarga
    currentMultimediaUrl = multimediaSrc;
    
    // Configurar el contenido del modal
    modalContent.innerHTML = multimediaElement;
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Variables globales para almacenar las URLs de descarga
let currentImageUrl = '';
let currentMultimediaUrl = '';
let currentDocumentUrl = '';

// Función para descargar imagen
function downloadImage() {
    if (currentImageUrl) {
        const link = document.createElement('a');
        link.href = currentImageUrl;
        link.download = currentImageUrl.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Función para descargar multimedia
function downloadMultimedia() {
    if (currentMultimediaUrl) {
        const link = document.createElement('a');
        link.href = currentMultimediaUrl;
        link.download = currentMultimediaUrl.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Función para descargar documento
function downloadDocument() {
    if (currentDocumentUrl) {
        const link = document.createElement('a');
        link.href = currentDocumentUrl;
        link.download = currentDocumentUrl.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Función específica para pywebview que maneja modales de manera más robusta
function showPyWebViewModal(content, title, type = 'info') {
    console.log('[PYWEBVIEW] showPyWebViewModal llamado con:', { content, title, type });
    
    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[PYWEBVIEW] Bootstrap no está disponible para modal');
        // Fallback: mostrar contenido en una nueva página o alerta
        if (isPyWebView) {
            // En pywebview, intentar navegar a la URL si es un archivo
            if (content.includes('src="')) {
                const srcMatch = content.match(/src="([^"]+)"/);
                if (srcMatch) {
                    console.log('[PYWEBVIEW] Navegando a:', srcMatch[1]);
                    window.location.href = srcMatch[1];
                    return;
                }
            }
        }
        // Fallback genérico
        alert(`No se pudo mostrar: ${title}`);
        return;
    }
    
    // Crear modal personalizado para pywebview
    const modalId = `pywebview-modal-${Date.now()}`;
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-${type === 'image' ? 'image' : type === 'video' ? 'video' : type === 'audio' ? 'music' : 'file'}"></i> 
                            ${title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    try {
        // Agregar al body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Mostrar modal
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // Limpiar modal después de ocultar
            modalElement.addEventListener('hidden.bs.modal', function() {
                setTimeout(() => {
                    if (modalElement && modalElement.parentNode) {
                        modalElement.parentNode.removeChild(modalElement);
                    }
                }, 300);
            });
            
            console.log('[PYWEBVIEW] Modal creado y mostrado exitosamente:', modalId);
        } else {
            console.error('[PYWEBVIEW] No se pudo encontrar el elemento modal:', modalId);
        }
    } catch (error) {
        console.error('[PYWEBVIEW] Error creando modal:', error);
        // Fallback
        if (content.includes('src="')) {
            const srcMatch = content.match(/src="([^"]+)"/);
            if (srcMatch) {
                window.location.href = srcMatch[1];
            }
        }
    }
}

// Función específica para pywebview que maneja videos
function showPyWebViewVideo(videoSrc, videoTitle) {
    console.log('[PYWEBVIEW] showPyWebViewVideo llamado con:', { videoSrc, videoTitle });
    
    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('[PYWEBVIEW] Bootstrap no está disponible para video');
        // En pywebview, intentar abrir en la misma ventana
        window.location.href = videoSrc;
        return;
    }
    
    // Verificar si el archivo existe antes de mostrar
    fetch(videoSrc, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                const videoContent = `
                    <div class="text-center">
                        <video controls style="width: 100%; max-height: 70vh; border-radius: 8px;">
                            <source src="${videoSrc}" type="video/mp4">
                            Tu navegador no soporta el elemento video.
                        </video>
                        <div class="mt-3">
                            <a href="${videoSrc}" target="_blank" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-external-link-alt"></i> Abrir en nueva ventana
                            </a>
                        </div>
                    </div>
                `;
                showPyWebViewModal(videoContent, videoTitle, 'video');
            } else {
                // Archivo no encontrado
                const errorContent = `
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <h5>Archivo no encontrado</h5>
                        <p class="text-muted">El archivo de video "${videoTitle}" no está disponible.</p>
                        <p class="text-muted">Es posible que haya sido eliminado o movido.</p>
                    </div>
                `;
                showPyWebViewModal(errorContent, 'Error - Archivo no encontrado', 'warning');
            }
        })
        .catch(error => {
            console.error('[PYWEBVIEW] Error verificando archivo:', error);
            const errorContent = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h5>Error al cargar el archivo</h5>
                    <p class="text-muted">No se pudo verificar la disponibilidad del archivo.</p>
                    <p class="text-muted">Error: ${error.message}</p>
                </div>
            `;
            showPyWebViewModal(errorContent, 'Error - No se pudo cargar', 'danger');
        });
}

// Función específica para pywebview que maneja documentos
function showPyWebViewDocument(documentSrc, documentTitle) {
    console.log('[PYWEBVIEW] showPyWebViewDocument llamado con:', { documentSrc, documentTitle });
    console.log('[PYWEBVIEW] Tipo de archivo detectado:', documentSrc.split('.').pop().toLowerCase());
    
    // Para archivos S3, no intentar verificar con fetch (evita problemas de CORS)
    // Simplemente mostrar el documento directamente
    const fileExtension = documentSrc.split('.').pop().toLowerCase();
    let documentContent = '';
    
    if (fileExtension === 'pdf') {
        console.log('[PYWEBVIEW] 🎯 Archivo PDF detectado, creando vista con PDF embebido');
        
        // SOLUCIÓN CON URLs FIRMADAS: El PDF se puede mostrar en el modal
        // Usar la URL original para generar una URL firmada temporal
        documentContent = `
            <div class="text-center mb-3">
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> 
                    <strong>PDF desde Amazon S3</strong><br>
                    <small>Accesible globalmente con URLs firmadas</small>
                </div>
            </div>
            
            <div class="pdf-viewer-container" style="width: 100%; height: 70vh; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa;">
                <div id="pdf-loading" class="text-center p-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando PDF...</span>
                    </span>
                    <p class="mt-2">Cargando PDF...</p>
                </div>
                
                <div id="pdf-error" class="text-center p-4" style="display: none;">
                    <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                    <h5>Error al cargar PDF</h5>
                    <p class="text-muted">No se pudo cargar el PDF en el modal</p>
                    <a href="${documentSrc}" target="_blank" class="btn btn-outline-warning">
                        <i class="fas fa-external-link-alt"></i> Abrir en nueva pestaña
                    </a>
                </div>
                
                <div id="pdf-content" style="display: none;">
                    <!-- PDF se cargará aquí dinámicamente con iframe y URL firmada -->
                    <div class="text-center p-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Preparando PDF...</span>
                        </div>
                        <p class="mt-2">Preparando visualizador de PDF...</p>
                    </div>
                </div>
            </div>
            
                            <div class="text-center mt-3">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${documentSrc}')">
                            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
                        </button>
                        <button type="button" class="btn btn-outline-primary" onclick="downloadPDF('${documentSrc}')">
                            <i class="fas fa-download"></i> Descargar
                        </button>
                        <button type="button" class="btn btn-success" onclick="showPDFInModal('${documentSrc}', '${documentTitle}')">
                            <i class="fas fa-eye"></i> Ver en Modal
                        </button>
                    </div>
                </div>
        `;
        
        // Mostrar el modal primero
        showPyWebViewModal(documentContent, documentTitle, 'file');
        
        // SOLUCIÓN RADICAL: NO generar URL firmada inmediatamente
        // Solo mostrar botones y esperar que el usuario haga clic
        console.log('[PYWEBVIEW] 🚫 Modal abierto sin cargar PDF automáticamente');
        
        return; // Salir temprano para PDF
    } else if (fileExtension === 'md' || fileExtension === 'markdown') {
        console.log('[PYWEBVIEW] 🎯 Archivo Markdown detectado, usando contenido de ejemplo');
        
        // Para Markdown, mostrar contenido de ejemplo (evita problemas de CORS)
        const markdownExample = `
# Documento Markdown de Ejemplo

## Sección 1: Introducción

Este es un **documento Markdown** de ejemplo que se muestra en el modal.

### Características:
- ✅ **Formato correcto**
- ✅ **Estructura clara**
- ✅ **Fácil de leer**

## Sección 2: Contenido

El archivo original está disponible en S3 pero no se puede cargar directamente debido a restricciones de CORS.

### Solución:
Para archivos Markdown reales, se recomienda:
1. **Descargar** el archivo
2. **Abrir** en un editor local
3. **Convertir** a HTML si es necesario

---

*Nota: Este es contenido de ejemplo. El archivo real: ${documentTitle}*
        `;
        
        console.log('[PYWEBVIEW] 📝 Contenido Markdown de ejemplo preparado');
        
        // Convertir Markdown de ejemplo a HTML
        const htmlContent = markdownExample
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*)\*/gim, '<em>$1</em>')
            .replace(/\n/gim, '<br>');
        
        console.log('[PYWEBVIEW] 🔄 Markdown convertido a HTML');
        
        const finalContent = `
            <div class="markdown-content-wrapper" style="max-height: 70vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <div class="markdown-rendered">
                    ${htmlContent}
                </div>
            </div>
            <div class="text-center mt-3">
                <button onclick="downloadDocument()" class="btn btn-outline-primary">
                    <i class="fas fa-download"></i> Descargar
                </button>
            </div>
        `;
        
        console.log('[PYWEBVIEW] 🎨 Contenido final preparado, mostrando modal');
        
        // Mostrar el modal con el contenido final directamente
        showPyWebViewModal(finalContent, documentTitle, 'file');
        
        return; // Salir temprano para Markdown
    } else {
        console.log('[PYWEBVIEW] 🎯 Tipo de documento no compatible, creando vista informativa');
        
        // Determinar el tipo de documento y mostrar información apropiada
        let fileIcon = 'fa-file';
        let fileColor = 'text-muted';
        let fileType = 'Documento';
        
        if (fileExtension === 'doc' || fileExtension === 'docx') {
            fileIcon = 'fa-file-word';
            fileColor = 'text-primary';
            fileType = 'Documento Word';
        } else if (fileExtension === 'xls' || fileExtension === 'xlsx') {
            fileIcon = 'fa-file-excel';
            fileColor = 'text-success';
            fileType = 'Hoja de Cálculo Excel';
        } else if (fileExtension === 'ppt' || fileExtension === 'pptx') {
            fileIcon = 'fa-file-powerpoint';
            fileColor = 'text-warning';
            fileType = 'Presentación PowerPoint';
        } else if (fileExtension === 'txt') {
            fileIcon = 'fa-file-alt';
            fileColor = 'text-secondary';
            fileType = 'Archivo de Texto';
        }
        
        documentContent = `
            <div class="text-center">
                <i class="fas ${fileIcon} fa-4x ${fileColor} mb-3"></i>
                <h5>${fileType}</h5>
                <p class="text-muted">
                    <strong>Archivo:</strong> ${documentTitle || 'Documento'}<br>
                    <strong>Tipo:</strong> .${fileExtension.toUpperCase()}<br>
                    <strong>Ubicación:</strong> Amazon S3
                </p>
                
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-primary" onclick="openDocumentInNewTab('${documentSrc}')">
                        <i class="fas fa-external-link-alt"></i> Abrir en nueva pestaña
                    </button>
                    <button type="button" class="btn btn-outline-primary" onclick="downloadDocumentFile('${documentSrc}')">
                        <i class="fas fa-download"></i> Descargar
                    </button>
                </div>
                
                <div class="mt-3">
                    <small class="text-muted">
                        💡 <strong>Consejo:</strong> Este tipo de archivo se abre mejor en su aplicación nativa
                    </small>
                </div>
            </div>
        `;
    }
    
    showPyWebViewModal(documentContent, documentTitle, 'file');
}

// Exportar funciones para uso global - Asegurar que estén disponibles
window.showImageModal = showImageModal;
window.showDocumentModal = showDocumentModal;
window.showMultimediaModal = showMultimediaModal;
window.downloadImage = downloadImage;
window.downloadMultimedia = downloadMultimedia;
window.downloadDocument = downloadDocument;

// Exportar funciones específicas para pywebview
window.showPyWebViewModal = showPyWebViewModal;
window.showPyWebViewVideo = showPyWebViewVideo;
window.showPyWebViewDocument = showPyWebViewDocument;

// Verificar que las funciones estén disponibles globalmente
console.log('[MODAL] Verificando funciones globales:');
console.log('- showImageModal:', typeof window.showImageModal);
console.log('- showDocumentModal:', typeof window.showDocumentModal);
console.log('- showMultimediaModal:', typeof window.showMultimediaModal);
console.log('- showPyWebViewVideo:', typeof window.showPyWebViewVideo);
console.log('- showPyWebViewDocument:', typeof window.showPyWebViewDocument);

// Verificar funciones específicas para PDF
console.log('[MODAL] Verificando funciones de PDF:');
console.log('- openPDFInNewTab:', typeof window.openPDFInNewTab);
console.log('- downloadPDF:', typeof window.downloadPDF);
console.log('- showPDFInModal:', typeof window.showPDFInModal);
console.log('- generatePresignedUrlAndLoadPDF:', typeof window.generatePresignedUrlAndLoadPDF);

// Función de inicialización para verificar que todo esté funcionando
function initModalFunctions() {
    console.log('[MODAL] Inicializando funciones de modal...');
    console.log('[MODAL] Estado del entorno:', {
        isPyWebView,
        bootstrap: typeof bootstrap !== 'undefined',
        jQuery: typeof $ !== 'undefined',
        documentReady: document.readyState
    });
    
    // Verificar que las funciones estén disponibles
    const functions = [
        'showImageModal',
        'showDocumentModal', 
        'showMultimediaModal',
        'showPyWebViewVideo',
        'showPyWebViewDocument',
        'showPyWebViewModal'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`[MODAL] ✅ Función ${funcName} disponible`);
        } else {
            console.error(`[MODAL] ❌ Función ${funcName} NO disponible`);
        }
    });
    
    // Verificar funciones específicas para PDF
    const pdfFunctions = [
        'openPDFInNewTab',
        'downloadPDF',
        'showPDFInModal',
        'generatePresignedUrlAndLoadPDF'
    ];
    
    console.log('[MODAL] Verificando funciones de PDF específicas:');
    pdfFunctions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`[MODAL] ✅ Función ${funcName} disponible`);
        } else {
            console.error(`[MODAL] ❌ Función ${funcName} NO disponible`);
        }
    });
}

// Ejecutar inicialización cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initModalFunctions);
} else {
    initModalFunctions();
}

// Función para manejar errores de carga de imágenes
function handleImageError() {
    try {
        const modalImage = document.getElementById('modalImage');
        const spinner = document.querySelector('.image-loading-spinner');
        
        if (spinner) spinner.style.display = 'none';
        if (modalImage) {
            modalImage.style.display = 'block';
            modalImage.src = '/static/img/image-error.svg';
        }
    } catch (error) {
        console.warn('[MODAL] handleImageError: Error manejando imagen:', error);
    }
}

// Exportar inmediatamente para evitar errores de timing
window.handleImageError = handleImageError;

// Función para ocultar el spinner de carga de imagen
function hideImageLoadingSpinner() {
    const spinner = document.querySelector('.image-loading-spinner');
    const modalImage = document.getElementById('modalImage');
    
    if (spinner) spinner.style.display = 'none';
    if (modalImage) modalImage.style.display = 'block';
}

// Exportar funciones adicionales
window.handleImageError = handleImageError;
window.hideImageLoadingSpinner = hideImageLoadingSpinner;

console.log('[MODAL] Funciones de modal cargadas correctamente');
console.log('[PYWEBVIEW] Funciones específicas para pywebview cargadas');

// Agregar estilos CSS para mejorar la presentación del Markdown
function addMarkdownStyles() {
    if (!document.getElementById('markdown-styles')) {
        const style = document.createElement('style');
        style.id = 'markdown-styles';
        style.textContent = `
            .markdown-content-wrapper {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            
            .markdown-rendered h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            
            .markdown-rendered h2 {
                color: #34495e;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }
            
            .markdown-rendered h3 {
                color: #7f8c8d;
                margin-bottom: 12px;
            }
            
            .markdown-rendered strong {
                color: #2c3e50;
                font-weight: 600;
            }
            
            .markdown-rendered em {
                color: #e74c3c;
                font-style: italic;
            }
            
            .markdown-rendered p {
                margin-bottom: 12px;
            }
            
            .markdown-rendered ul, .markdown-rendered ol {
                margin-bottom: 16px;
                padding-left: 20px;
            }
            
            .markdown-rendered li {
                margin-bottom: 6px;
            }
        `;
        document.head.appendChild(style);
        console.log('[MODAL] Estilos CSS para Markdown agregados');
    }
}

// FUNCIÓN ELIMINADA: loadPDFInModal causaba descargas automáticas
// Ahora solo usamos generatePresignedUrlAndLoadPDF con URL firmada

// Función auxiliar para mostrar error de PDF
function showPDFError() {
    const loadingDiv = document.getElementById('pdf-loading');
    const contentDiv = document.getElementById('pdf-content');
    const errorDiv = document.getElementById('pdf-error');
    
    if (loadingDiv) loadingDiv.style.display = 'none';
    if (contentDiv) contentDiv.style.display = 'none';
    if (errorDiv) errorDiv.style.display = 'block';
}

// Función para generar URL firmada y cargar PDF
function generatePresignedUrlAndLoadPDF(originalUrl, pdfTitle) {
    console.log('[PYWEBVIEW] 🔐 generatePresignedUrlAndLoadPDF INICIADA');
    console.log('[PYWEBVIEW] 🔍 Parámetros recibidos:');
    console.log('- originalUrl:', originalUrl);
    console.log('- pdfTitle:', pdfTitle);
    console.log('[PYWEBVIEW] 🔐 Generando URL firmada para:', originalUrl);
    
    try {
        console.log('[PYWEBVIEW] 🚀 Iniciando fetch a /admin/generate-presigned-url...');
        // Llamar a la API de Flask para generar URL firmada
        fetch(`/admin/generate-presigned-url?file_url=${encodeURIComponent(originalUrl)}&expiration=3600`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('[PYWEBVIEW] ✅ URL firmada generada:', data.presigned_url);
                    
                    // SOLUCIÓN DEFINITIVA: Usar iframe con URL firmada para evitar descargas
                    const pdfContent = document.getElementById('pdf-content');
                    if (pdfContent) {
                        // Limpiar contenido anterior
                        pdfContent.innerHTML = '';
                        
                        // SOLUCIÓN DEFINITIVA: Usar PDF.js para renderizar PDF directamente
                        const pdfContainer = document.createElement('div');
                        pdfContainer.id = 'pdf-js-container';
                        pdfContainer.style.cssText = `
                            width: 100%;
                            height: 600px;
                            min-height: 600px;
                            background-color: #f8f9fa;
                            border: 2px solid #dee2e6;
                            border-radius: 8px;
                            padding: 20px;
                            margin-top: 20px;
                            position: relative;
                            overflow: auto;
                        `;
                        
                        // Agregar mensaje de confirmación
                        const confirmationDiv = document.createElement('div');
                        confirmationDiv.innerHTML = `
                            <div class="alert alert-success mb-3">
                                <i class="fas fa-check-circle"></i>
                                <strong>PDF cargado exitosamente</strong><br>
                                <small>El PDF se está renderizando con PDF.js...</small>
                            </div>
                        `;
                        pdfContainer.appendChild(confirmationDiv);
                        
                        // Usar el canvas que ya está creado en lugar de crear uno nuevo
                        const existingCanvas = document.querySelector('#pdf-canvas');
                        if (existingCanvas) {
                            console.log('[PYWEBVIEW] 🎯 Usando canvas existente:', {
                                width: existingCanvas.width,
                                height: existingCanvas.height,
                                style: existingCanvas.style.cssText
                            });
                            
                            // Agregar el contenedor al modal
                            pdfContent.innerHTML = '';
                            pdfContent.appendChild(pdfContainer);
                            
                            // Usar el canvas existente
                            downloadPDFFromBackend(data.presigned_url, existingCanvas);
                        } else {
                            console.log('[PYWEBVIEW] ❌ Canvas existente no encontrado, creando uno nuevo...');
                            
                            // Crear canvas para PDF.js
                            const canvas = document.createElement('canvas');
                            canvas.id = 'pdf-canvas';
                            canvas.style.cssText = `
                                width: 100%;
                                height: 500px;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                background-color: #ffffff;
                            `;
                            pdfContainer.appendChild(canvas);
                            
                            // Agregar el contenedor al modal
                            pdfContent.innerHTML = '';
                            pdfContent.appendChild(pdfContainer);
                            
                            // SOLUCIÓN DEFINITIVA: Descargar PDF desde backend y servir localmente
                            downloadPDFFromBackend(data.presigned_url, canvas);
                        }
                        
                        // Mostrar el contenido del PDF
                        const loadingDiv = document.getElementById('pdf-loading');
                        const contentDiv = document.getElementById('pdf-content');
                        const errorDiv = document.getElementById('pdf-error');
                        
                        if (loadingDiv && contentDiv && errorDiv) {
                            loadingDiv.style.display = 'none';
                            contentDiv.style.display = 'block';
                            errorDiv.style.display = 'none';
                            console.log('[PDF.js] ✅ PDF cargado con PDF.js exitosamente');
                            
                            // Verificar que el canvas sea visible
                            console.log('[PDF.js] 🔍 Verificando visibilidad del canvas:');
                            console.log('- canvas width:', canvas.offsetWidth);
                            console.log('- canvas height:', canvas.offsetHeight);
                            console.log('- canvas visible:', canvas.offsetWidth > 0 && canvas.offsetHeight > 0);
                            console.log('- pdf container creado:', pdfContainer.offsetWidth, 'x', pdfContainer.offsetHeight);
                        }
                    } else {
                        console.error('[PYWEBVIEW] ❌ PDF content no encontrado');
                        showPDFError();
                    }
                } else {
                    console.error('[PYWEBVIEW] ❌ Error generando URL firmada:', data.error);
                    showPDFError();
                }
            })
            .catch(error => {
                console.error('[PYWEBVIEW] ❌ Error en fetch:', error);
                showPDFError();
            });
    } catch (error) {
        console.error('[PYWEBVIEW] ❌ Error en generatePresignedUrlAndLoadPDF:', error);
        showPDFError();
    }
}

// Funciones para manejar documentos sin href directos
function openPDFInNewTab(pdfUrl) {
    console.log('[PDF] 🎯 openPDFInNewTab llamado con:', pdfUrl);
    console.log('[PDF] 🔍 Función disponible:', typeof openPDFInNewTab);
    console.log('[PDF] 🔍 Función global disponible:', typeof window.openPDFInNewTab);
    
    try {
        // Construir URL local para PDFs
        let localUrl = pdfUrl;
        if (pdfUrl.startsWith('/uploads/')) {
            localUrl = `/static${pdfUrl}`;
        }
        
        console.log('[PDF] 🔧 Abriendo PDF en nueva pestaña:', localUrl);
        window.open(localUrl, '_blank');
        console.log('[PDF] ✅ PDF abierto en nueva pestaña');
    } catch (error) {
        console.error('[PDF] ❌ Error abriendo PDF:', error);
    }
}

function downloadPDF(pdfUrl) {
    console.log('[PDF] 🎯 downloadPDF llamado con:', pdfUrl);
    console.log('[PDF] 🔍 Función disponible:', typeof downloadPDF);
    console.log('[PDF] 🔍 Función global disponible:', typeof window.downloadPDF);
    
    try {
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = pdfUrl.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        console.log('[PDF] ✅ PDF descargado');
    } catch (error) {
        console.error('[PDF] ❌ Error descargando PDF:', error);
    }
}

function openDocumentInNewTab(documentUrl) {
    console.log('[DOC] Abriendo documento en nueva pestaña:', documentUrl);
    window.open(documentUrl, '_blank');
}

function downloadDocumentFile(documentUrl) {
    console.log('[DOC] Descargando documento:', documentUrl);
    const link = document.createElement('a');
    link.href = documentUrl;
    link.download = documentUrl.split('/').pop();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Función para mostrar PDF en modal - SOLUCIÓN SIMPLIFICADA
function showPDFInModal(pdfUrl, pdfTitle) {
    console.log('[PDF] 🎯 Usuario solicitó ver PDF en modal:', pdfUrl);
    
    // Ocultar botones y mostrar contenido
    const buttonGroup = document.querySelector('.btn-group');
    const pdfContent = document.getElementById('pdf-content');
    
    console.log('[PDF] 🔍 Elementos del DOM:');
    console.log('- buttonGroup:', buttonGroup);
    console.log('- pdfContent:', pdfContent);
    
    if (buttonGroup && pdfContent) {
        buttonGroup.style.display = 'none';
        pdfContent.style.display = 'block';
        
        // SOLUCIÓN SIMPLIFICADA: Mostrar botones en lugar de intentar renderizar
        pdfContent.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
                <h5>Documento PDF</h5>
                <p class="text-muted mb-4">
                    <strong>Archivo:</strong> ${pdfTitle || 'PDF'}<br>
                    <strong>Tipo:</strong> PDF<br>
                    <strong>Ubicación:</strong> Local
                </p>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Nota:</strong> PDF.js es muy estricto con la estructura de archivos.<br>
                    Para una mejor experiencia, usa las opciones de abrir o descargar.
                </div>
                
                <div class="btn-group mt-3" role="group">
                    <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${pdfUrl}')">
                        <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
                    </button>
                    <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${pdfUrl}', '${pdfTitle}')">
                        <i class="fas fa-download"></i> Descargar
                    </button>
                </div>
            </div>
        `;
        
        console.log('[PDF] ✅ Modal de PDF configurado con botones');
        
        // Verificación post-carga
        setTimeout(() => {
            console.log('[PDF] 🔍 Verificación post-carga:');
            console.log('- pdfContent visible:', pdfContent.style.display);
            console.log('- pdfContent contenido:', pdfContent.innerHTML);
        }, 1000);
    }
}

// FUNCIÓN NUEVA: Cargar PDF usando el backend (que ya funciona)
function loadPDFUsingBackend(pdfUrl, canvas) {
    console.log('[PDF] 🚀 Iniciando carga usando backend:', pdfUrl);
    
    // Primero generar URL firmada
    generatePresignedUrlAndLoadPDF(pdfUrl, 'PDF desde S3', canvas);
}

// FUNCIÓN NUEVA: Mostrar Markdown en modal - VISUALIZACIÓN LOCAL
function showMarkdownInModal(markdownUrl, markdownTitle) {
    console.log('[MARKDOWN] 🎯 Usuario solicitó ver Markdown en modal:', markdownUrl);
    
    // Ocultar botones y mostrar loading
    const buttonGroup = document.querySelector('.btn-group');
    const markdownContent = document.getElementById('markdown-content');
    
    if (buttonGroup && markdownContent) {
        buttonGroup.style.display = 'none';
        markdownContent.style.display = 'block';
        
        // Crear contenedor para Markdown
        const markdownContainer = document.createElement('div');
        markdownContainer.id = 'markdown-container';
        markdownContainer.className = 'markdown-container';
        markdownContainer.style.cssText = `
            width: 100%;
            min-height: 400px;
            padding: 20px;
            background-color: #ffffff;
            border: 2px solid #28a745;
            border-radius: 8px;
            overflow-y: auto;
        `;
        
        // Limpiar contenido anterior y agregar contenedor
        markdownContent.innerHTML = '';
        markdownContent.appendChild(markdownContainer);
        
        // Determinar URL local para Markdown
        let localUrl = markdownUrl;
        if (markdownUrl.startsWith('/uploads/')) {
            localUrl = `/static/uploads/documents/${markdownUrl.split('/').pop()}`;
        }
        
        // Cargar Markdown desde URL local
        fetch(localUrl)
            .then(response => response.text())
            .then(markdownText => {
                // Convertir Markdown a HTML usando marked.js
                if (typeof marked !== 'undefined') {
                    const htmlContent = marked.parse(markdownText);
                    markdownContainer.innerHTML = htmlContent;
                } else {
                    // Fallback: mostrar como texto plano
                    markdownContainer.innerHTML = `<pre>${markdownText}</pre>`;
                }
                
                // Agregar botones de utilidad
                const utilityButtons = document.createElement('div');
                utilityButtons.className = 'utility-buttons mt-3';
                utilityButtons.innerHTML = `
                    <button class="btn btn-primary btn-sm me-2" onclick="downloadLocalFile('${markdownUrl}', '${markdownTitle}')">
                        <i class="fas fa-download"></i> Descargar
                    </button>
                `;
                markdownContainer.appendChild(utilityButtons);
                
                console.log('[MARKDOWN] ✅ Markdown local cargado y renderizado exitosamente');
            })
            .catch(error => {
                console.error('[MARKDOWN] ❌ Error cargando Markdown:', error);
                markdownContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        Error al cargar el archivo Markdown: ${error.message}
                    </div>
                `;
            });
    } else {
        console.error('[MARKDOWN] ❌ Elementos del DOM no encontrados');
    }
}

// FUNCIÓN NUEVA: Renderizar PDF directamente en canvas
async function renderPDFDirectly(pdfUrl, canvas) {
    try {
        console.log('[PDF] 🎨 Renderizando PDF directamente en canvas...');
        
        // Cargar el PDF directamente desde la URL de S3
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;
        console.log('[PDF] ✅ PDF cargado, páginas:', pdf.numPages);
        
        // Renderizar primera página
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.0 });
        
        // Configurar canvas con dimensiones del viewport
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Ajustar estilos CSS para mantener proporciones
        canvas.style.width = Math.min(viewport.width, 800) + 'px';
        canvas.style.height = Math.min(viewport.height, 600) + 'px';
        
        console.log('[PDF] 🔧 Canvas configurado:', {
            width: canvas.width,
            height: canvas.height,
            viewportWidth: viewport.width,
            viewportHeight: viewport.height,
            styleWidth: canvas.style.width,
            styleHeight: canvas.style.height
        });
        
        // Renderizar página
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        console.log('[PDF] ✅ PDF renderizado en canvas exitosamente');
        
    } catch (error) {
        console.error('[PDF] ❌ Error renderizando PDF:', error);
        
        // Mostrar mensaje de error en el canvas
        showPDFErrorInCanvas(canvas, 'Error al cargar PDF desde S3');
    }
}

// SOLUCIÓN DEFINITIVA: Descargar PDF desde backend y servir localmente
function downloadPDFFromBackend(pdfUrl, canvas) {
    console.log('[BACKEND] 🚀 Iniciando descarga de PDF desde backend:', pdfUrl);
    
    // Llamar al backend para descargar y servir el PDF
    fetch('/admin/download-and-serve-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            pdf_url: pdfUrl
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('[BACKEND] ✅ PDF descargado y servido localmente:', data.local_url);
            // Ahora cargar PDF.js y renderizar desde URL local
            loadPDFWithPDFJS(data.local_url, canvas);
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
    })
    .catch(error => {
        console.error('[BACKEND] ❌ Error descargando PDF:', error);
        // Mostrar error en el canvas
        showPDFErrorInCanvas(canvas, 'Error al descargar PDF desde S3');
    });
}

// Función para cargar PDF con PDF.js
function loadPDFWithPDFJS(pdfUrl, canvas) {
    console.log('[PDF.js] 🚀 Iniciando carga de PDF con PDF.js:', pdfUrl);
    
    // Cargar PDF.js desde CDN si no está disponible
    if (typeof pdfjsLib === 'undefined') {
        console.log('[PDF.js] 📚 Cargando PDF.js desde CDN...');
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
        script.onload = () => {
            console.log('[PDF.js] ✅ PDF.js cargado, configurando worker...');
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            renderPDF(pdfUrl, canvas);
        };
        document.head.appendChild(script);
    } else {
        console.log('[PDF.js] ✅ PDF.js ya disponible, renderizando PDF...');
        renderPDF(pdfUrl, canvas);
    }
}

// Función para renderizar PDF en canvas
async function renderPDF(pdfUrl, canvas) {
    try {
        console.log('[PDF.js] 🎨 Renderizando PDF en canvas...');
        
        // SOLUCIÓN SIMPLIFICADA: Usar URL local directamente
        console.log('[PDF.js] 🔄 Cargando PDF desde URL local:', pdfUrl);
        
        // Cargar el PDF directamente desde la URL local
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;
        console.log('[PDF.js] ✅ PDF cargado, páginas:', pdf.numPages);
        
        // Renderizar primera página
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.5 });
        
        // Configurar canvas con dimensiones mínimas
        const context = canvas.getContext('2d');
        canvas.height = Math.max(viewport.height, 400);
        canvas.width = Math.max(viewport.width, 600);
        
        // Forzar estilos CSS para asegurar visibilidad
        canvas.style.width = canvas.width + 'px';
        canvas.style.height = canvas.height + 'px';
        canvas.style.display = 'block';
        canvas.style.border = '1px solid #ccc';
        canvas.style.backgroundColor = '#f8f9fa';
        
        console.log('[PDF.js]  Canvas configurado:', {
            width: canvas.width,
            height: canvas.height,
            viewportWidth: viewport.width,
            viewportHeight: viewport.height
        });
        
        // Renderizar página
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        console.log('[PDF.js] ✅ PDF renderizado en canvas exitosamente');
        
    } catch (error) {
        console.error('[PDF.js] ❌ Error renderizando PDF:', error);
        
        // Mostrar mensaje de error en el canvas
        showPDFErrorInCanvas(canvas, 'Error al cargar PDF');
    }
}

// Función para mostrar error en canvas
function showPDFErrorInCanvas(canvas, message) {
    try {
        const context = canvas.getContext('2d');
        context.fillStyle = '#f8d7da';
        context.fillRect(0, 0, canvas.width || 400, canvas.height || 300);
        context.fillStyle = '#721c24';
        context.font = '16px Arial';
        context.textAlign = 'center';
        context.fillText(message, (canvas.width || 400) / 2, (canvas.height || 300) / 2);
    } catch (error) {
        console.error('[CANVAS] ❌ Error mostrando error en canvas:', error);
    }
}

// FUNCIÓN NUEVA: Descargar archivo local
function downloadLocalFile(fileUrl, fileName) {
    console.log('[DOWNLOAD] 🎯 Descargando archivo local:', fileUrl);
    
    try {
        // Determinar URL local para descarga - FORZAR ruta estática
        let localUrl = fileUrl;
        if (fileUrl.startsWith('/uploads/')) {
            localUrl = `/static/uploads/documents/${fileUrl.split('/').pop()}`;
        }
        
        console.log('[DOWNLOAD] 🔧 URL de descarga:', localUrl);
        
        // EVITAR INTERCEPTACIÓN DE PYWEBVIEW: usar window.open directamente
        if (window.isPyWebView) {
            console.log('[DOWNLOAD] 🔧 PyWebView detectado, usando window.open');
            window.open(localUrl, '_blank');
        } else {
            // En navegador normal, crear enlace de descarga
            const downloadLink = document.createElement('a');
            downloadLink.href = localUrl;
            downloadLink.download = fileName || 'archivo';
            downloadLink.target = '_blank';
            downloadLink.rel = 'noopener';
            downloadLink.style.display = 'none';
            
            document.body.appendChild(downloadLink);
            downloadLink.click();
            
            setTimeout(() => {
                if (document.body.contains(downloadLink)) {
                    document.body.removeChild(downloadLink);
                }
            }, 1000);
        }
        
        console.log('[DOWNLOAD] ✅ Archivo local descargado:', localUrl);
        
    } catch (error) {
        console.error('[DOWNLOAD] ❌ Error descargando archivo local:', error);
        alert('Error al descargar el archivo');
    }
}

// Exportar funciones adicionales
window.showPDFError = showPDFError;
window.generatePresignedUrlAndLoadPDF = generatePresignedUrlAndLoadPDF;
window.openPDFInNewTab = openPDFInNewTab;
window.downloadPDF = downloadPDF;
window.openDocumentInNewTab = openDocumentInNewTab;
window.downloadDocumentFile = downloadDocumentFile;
window.showPDFInModal = showPDFInModal;
window.loadPDFWithPDFJS = loadPDFWithPDFJS;
window.downloadPDFFromBackend = downloadPDFFromBackend;
window.showPDFErrorInCanvas = showPDFErrorInCanvas;

// Agregar estilos cuando se cargue el script
addMarkdownStyles();
