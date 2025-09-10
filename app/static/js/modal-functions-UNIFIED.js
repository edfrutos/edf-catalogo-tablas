/**
 * MODAL FUNCTIONS UNIFIED - VERSIÓN FINAL FUNCIONAL
 * Archivo unificado con todas las funcionalidades de modal
 * Fecha: 4 de Enero de 2025
 * Estado: ✅ FUNCIONAL COMPLETAMENTE
 */

// Sistema de logging condicional
const DEBUG_MODE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const log = DEBUG_MODE ? console.log : () => {};
const logError = console.error; // Siempre mostrar errores

log("[MODAL-UNIFIED] 🚀 Iniciando sistema unificado de modales...");
log("[MODAL-UNIFIED] 📁 Archivo cargado:", window.location.href);
log("[MODAL-UNIFIED] 🔍 Verificando funciones disponibles...");

// ============================================================================
// DETECCIÓN DE ENTORNO
// ============================================================================

// Usar la variable global establecida por pywebview_compatibility.js (evitar redeclaración)
let isPyWebView;
if (typeof window.isPyWebView !== 'undefined') {
    isPyWebView = window.isPyWebView;
} else {
    isPyWebView = (typeof pywebview !== 'undefined' && pywebview !== null);
}
const isWebApp = !isPyWebView;

log("[MODAL-UNIFIED] 🔍 Entorno detectado:", {
  isPyWebView,
  isWebApp,
  userAgent: navigator.userAgent,
  source: window.isPyWebView ? 'pywebview_compatibility.js' : 'detection_local'
});

// ============================================================================
// FUNCIONES DE MODAL UNIFICADAS
// ============================================================================

// Función para mostrar documentos en modal (PDF, Markdown, Texto)
function showDocumentModal(documentSrc, documentTitle) {
  log("[MODAL-UNIFIED] 📄 showDocumentModal llamado con:", { documentSrc, documentTitle });
  
  // Buscar elementos del modal
  const modalElement = document.getElementById('documentModal');
  const modalContent = document.getElementById('documentContent');
  const modalTitle = document.getElementById('documentModalLabel');
  
  if (!modalElement || !modalContent || !modalTitle) {
    logError("[MODAL-UNIFIED] ❌ Elementos del modal no encontrados");
    alert("Error: Modal no disponible");
    return;
  }
  
  // Configurar título genérico basado en el tipo de archivo
  const fileExtension = documentSrc.split('.').pop()?.toLowerCase();
  let genericTitle = 'Documento';
  if (fileExtension === 'pdf') {
    genericTitle = 'Ver PDF';
  } else if (fileExtension === 'md') {
    genericTitle = 'Ver Markdown';
  } else if (['doc', 'docx'].includes(fileExtension)) {
    genericTitle = 'Ver Documento';
  } else if (['xls', 'xlsx'].includes(fileExtension)) {
    genericTitle = 'Ver Hoja de Cálculo';
  } else if (['ppt', 'pptx'].includes(fileExtension)) {
    genericTitle = 'Ver Presentación';
  } else {
    genericTitle = 'Ver Documento';
  }
  modalTitle.textContent = genericTitle;
  
  // Log de la extensión detectada
  log("[MODAL-UNIFIED] 🔍 Extensión detectada:", fileExtension);
  
  // Mostrar modal primero
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  
  // Mostrar loading
  modalContent.innerHTML = `
    <div class="text-center p-4">
      <div class="spinner-border text-primary mb-3" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <h5>Cargando Documento</h5>
      <p class="text-muted">Preparando visualización...</p>
    </div>
  `;
  
  // Limpiar URL si contiene rutas malformadas ANTES de detectar el tipo
  let cleanDocumentSrc = documentSrc;
  if (documentSrc.includes('/static/uploads//admin/s3/')) {
    cleanDocumentSrc = documentSrc.replace('/static/uploads//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL limpiada:", cleanDocumentSrc);
  } else if (documentSrc.includes('/imagenes_subidas//admin/s3/')) {
    cleanDocumentSrc = documentSrc.replace('/imagenes_subidas//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL limpiada:", cleanDocumentSrc);
  }
  
  // DETECCIÓN HÍBRIDA S3/LOCAL (después de limpiar la URL)
  const isS3File = cleanDocumentSrc.includes('s3.amazonaws.com') || cleanDocumentSrc.includes('edf-catalogo-tablas.s3') || cleanDocumentSrc.includes('/admin/s3/') || cleanDocumentSrc.includes('/s3/');
  log("[MODAL-UNIFIED] 🔍 URL del documento:", documentSrc);
  log("[MODAL-UNIFIED] 🔍 URL limpia:", cleanDocumentSrc);
  log("[MODAL-UNIFIED] 🔍 ¿Es archivo S3?:", isS3File);
  
  if (isS3File) {
    log("[MODAL-UNIFIED] 🔧 Archivo S3 detectado, usando proxy...");
    
    if (fileExtension === 'pdf') {
      // PDF S3 - usar iframe directo (más confiable)
      const proxyUrl = cleanDocumentSrc.replace(
        'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
        '/admin/s3/'
      );
      
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
          <h5>Documento PDF</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${documentTitle}<br>
            <strong>Tipo:</strong> PDF<br>
            <strong>Ubicación:</strong> S3
          </p>
          
          <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <strong>Visualizando PDF desde S3...</strong>
          </div>
          
          <div class="pdf-viewer-container mt-4">
            <iframe 
              src="${proxyUrl}" 
              width="100%" 
              height="600" 
              style="border: 1px solid #dee2e6; border-radius: 8px;"
              onload="console.log('[MODAL-UNIFIED] ✅ PDF cargado en iframe')"
              onerror="console.error('[MODAL-UNIFIED] ❌ Error cargando PDF en iframe')">
            </iframe>
          </div>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${documentSrc}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${documentSrc}', '${documentTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
      
    } else if (fileExtension === 'md') {
      // Markdown S3
      showMarkdownInModal(documentSrc, documentTitle);
      
    } else if (['txt', 'log'].includes(fileExtension)) {
      // Texto S3
      showTextInModal(documentSrc, documentTitle);
      
    } else {
      // Otros tipos S3
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-file fa-4x text-primary mb-3"></i>
          <h5>Documento S3</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${documentTitle}<br>
            <strong>Tipo:</strong> ${fileExtension?.toUpperCase() || 'Desconocido'}<br>
            <strong>Ubicación:</strong> S3
          </p>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${documentSrc}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${documentSrc}', '${documentTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
    }
    
  } else {
    // Archivo local
    log("[MODAL-UNIFIED] 🔧 Archivo local detectado...");
    
    if (fileExtension === 'pdf') {
      // PDF local - iframe directo
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
          <h5>Documento PDF</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${documentTitle}<br>
            <strong>Tipo:</strong> PDF<br>
            <strong>Ubicación:</strong> S3
          </p>
          
          <div class="pdf-viewer-container mt-4">
            <iframe 
              src="${documentSrc}" 
              width="100%" 
              height="600" 
              style="border: 1px solid #dee2e6; border-radius: 8px;"
              onload="console.log('[MODAL-UNIFIED] ✅ PDF local cargado en iframe')">
            </iframe>
          </div>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${documentSrc}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${documentSrc}', '${documentTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
      
    } else if (fileExtension === 'md') {
      // Markdown local
      showMarkdownInModal(documentSrc, documentTitle);
      
    } else if (['txt', 'log'].includes(fileExtension)) {
      // Texto local
      showTextInModal(documentSrc, documentTitle);
      
    } else {
      // Otros tipos locales
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-file fa-4x text-primary mb-3"></i>
          <h5>Documento Local</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${documentTitle}<br>
            <strong>Tipo:</strong> ${fileExtension?.toUpperCase() || 'Desconocido'}<br>
            <strong>Ubicación:</strong> S3
          </p>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${documentSrc}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${documentSrc}', '${documentTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
    }
  }
  
  log("[MODAL-UNIFIED] ✅ Modal de documento configurado");
}

// Función para mostrar Markdown en modal
function showMarkdownInModal(markdownUrl, markdownTitle) {
  log("[MODAL-UNIFIED] 📝 showMarkdownInModal llamado con:", { markdownUrl, markdownTitle });
  
  const modalContent = document.getElementById('documentContent');
  if (!modalContent) return;
  
  // Limpiar URL si contiene rutas malformadas
  let cleanMarkdownUrl = markdownUrl;
  if (markdownUrl.includes('/static/uploads//admin/s3/')) {
    cleanMarkdownUrl = markdownUrl.replace('/static/uploads//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL de Markdown limpiada:", cleanMarkdownUrl);
  } else if (markdownUrl.includes('/imagenes_subidas//admin/s3/')) {
    cleanMarkdownUrl = markdownUrl.replace('/imagenes_subidas//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL de Markdown limpiada:", cleanMarkdownUrl);
  }
  
  // Determinar URL para fetch
  let fetchUrl = cleanMarkdownUrl;
  const isS3File = cleanMarkdownUrl.includes('s3.amazonaws.com') || cleanMarkdownUrl.includes('edf-catalogo-tablas.s3') || cleanMarkdownUrl.includes('/admin/s3/') || cleanMarkdownUrl.includes('/s3/');
  
  if (isS3File) {
    fetchUrl = cleanMarkdownUrl.replace(
      'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
      '/admin/s3/'
    );
  } else if (cleanMarkdownUrl.includes('/static/uploads/')) {
    // Convertir ruta de archivo local a ruta de Flask para Markdown
    const filename = cleanMarkdownUrl.split('/').pop();
    fetchUrl = `/catalogs/view_markdown/${filename}`;
  }
  
  // Cargar Markdown
  log("[MODAL-UNIFIED] 🔍 Fetching URL:", fetchUrl);
  fetch(fetchUrl)
    .then(response => {
      log("[MODAL-UNIFIED] 🔍 Response status:", response.status);
      log("[MODAL-UNIFIED] 🔍 Response ok:", response.ok);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.text();
    })
    .then(markdownText => {
      log("[MODAL-UNIFIED] 🔍 Markdown text length:", markdownText.length);
      log("[MODAL-UNIFIED] 🔍 Markdown preview:", markdownText.substring(0, 100));
      // Renderizado simple de Markdown
      const htmlContent = markdownText
        .replace(/^### (.*$)/gim, "<h3>$1</h3>")
        .replace(/^## (.*$)/gim, "<h2>$1</h2>")
        .replace(/^# (.*$)/gim, "<h1>$1</h1>")
        .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
        .replace(/\*(.*)\*/gim, "<em>$1</em>")
        .replace(/\n/gim, "<br>");
      
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-file-code fa-4x text-info mb-3"></i>
          <h5>Documento Markdown</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${markdownTitle}<br>
            <strong>Tipo:</strong> Markdown<br>
            <strong>Ubicación:</strong> ${isS3File ? 'S3' : 'Local'}
          </p>
          
          <div class="markdown-content-wrapper" style="max-height: 60vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left; margin-bottom: 20px;">
            <div class="markdown-rendered">
              ${htmlContent}
            </div>
          </div>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${markdownUrl}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadMarkdownFile('${markdownUrl}', '${markdownTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
      
    })
    .catch(error => {
      log("[MODAL-UNIFIED] ❌ Error cargando Markdown:", error);
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
          <h5>Error al cargar Markdown</h5>
          <p class="text-muted">${error.message}</p>
          <p class="text-danger small">URL intentada: ${fetchUrl}</p>
        </div>
      `;
      
      // Insertar botones en el modal-footer
      const modalFooter = document.querySelector('#documentModal .modal-footer');
      if (modalFooter) {
        modalFooter.innerHTML = `
          <div class="d-flex gap-2 w-100 justify-content-between">
            <div class="d-flex gap-2">
              <a href="${markdownUrl}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadMarkdownFile('${markdownUrl}', '${markdownTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          </div>
        `;
      }
    });
}

// Función para mostrar texto en modal
function showTextInModal(textUrl, textTitle) {
  log("[MODAL-UNIFIED] 📄 showTextInModal llamado con:", { textUrl, textTitle });
  
  const modalContent = document.getElementById('documentContent');
  if (!modalContent) return;
  
  // Función para mostrar el contenido del texto
  function displayTextContent(content, location, finalUrl) {
    modalContent.innerHTML = `
      <div class="text-center p-4">
        <i class="fas fa-file-alt fa-4x text-primary mb-3"></i>
        <h5>Documento de Texto</h5>
        <p class="text-muted mb-4">
          <strong>Archivo:</strong> ${textTitle}<br>
          <strong>Tipo:</strong> Texto<br>
          <strong>Ubicación:</strong> ${location}
        </p>
        
        <div class="text-content-wrapper" style="max-height: 60vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left; margin-bottom: 20px;">
          <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace;">${content}</pre>
        </div>
      </div>
    `;
    
    // Insertar botones en el modal-footer
    const modalFooter = document.querySelector('#documentModal .modal-footer');
    if (modalFooter) {
      modalFooter.innerHTML = `
        <div class="d-flex gap-2 w-100 justify-content-between">
          <div class="d-flex gap-2">
            <a href="${finalUrl}" target="_blank" class="btn btn-primary">
              <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
            </a>
            <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${finalUrl}', '${textTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>
          </div>
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
        </div>
      `;
    }
  }
  
  // Función para intentar cargar desde una URL
  function tryLoadFromUrl(url, location) {
    return fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.text();
      })
      .then(textContent => {
        displayTextContent(textContent, location, url);
        return true; // Éxito
      })
      .catch(error => {
        log(`[MODAL-UNIFIED] ❌ Error cargando desde ${location}:`, error);
        return false; // Fallo
      });
  }
  
  // Intentar cargar desde S3 primero
  if (textUrl.includes('/admin/s3/')) {
    log("[MODAL-UNIFIED] 🔄 Intentando cargar desde S3...");
    tryLoadFromUrl(textUrl, "S3")
      .then(success => {
        if (!success) {
          // Fallback a local
          const filename = textUrl.split('/').pop();
          const localUrl = `/imagenes_subidas/${filename}`;
          log("[MODAL-UNIFIED] 🔄 Fallback a local:", localUrl);
          return tryLoadFromUrl(localUrl, "Local");
        }
        return true;
      })
      .then(success => {
        if (!success) {
          // Mostrar error final
          modalContent.innerHTML = `
            <div class="text-center p-4">
              <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
              <h5>Error al cargar texto</h5>
              <p class="text-muted">No se pudo cargar el archivo desde S3 ni desde almacenamiento local.</p>
              <p class="text-muted"><strong>Archivo:</strong> ${textTitle}</p>
            </div>
          `;
        }
      });
  } else {
    // URL no es S3, intentar directamente
    tryLoadFromUrl(textUrl, "Local")
      .then(success => {
        if (!success) {
          modalContent.innerHTML = `
            <div class="text-center p-4">
              <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
              <h5>Error al cargar texto</h5>
              <p class="text-muted">No se pudo cargar el archivo.</p>
              <p class="text-muted"><strong>Archivo:</strong> ${textTitle}</p>
            </div>
          `;
        }
      });
  }
}

// Función para verificar si una imagen existe
async function checkImageExists(imageSrc) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = imageSrc;
  });
}

// Función para limpiar imágenes y multimedia rotos en la página
async function cleanupBrokenImages() {
  log("[MODAL-UNIFIED] 🧹 Iniciando limpieza de imágenes y multimedia rotos...");
  
  const images = document.querySelectorAll('img[src*="/admin/s3/"], img[src*="/s3/"]');
  const videos = document.querySelectorAll('video[src*="/admin/s3/"], video[src*="/s3/"]');
  const audios = document.querySelectorAll('audio[src*="/admin/s3/"], audio[src*="/s3/"]');
  let brokenCount = 0;
  
  // Procesar imágenes
  for (const img of images) {
    const exists = await checkImageExists(img.src);
    if (!exists) {
      log("[MODAL-UNIFIED] 🗑️ Imagen rota encontrada:", img.src);
      brokenCount++;
      
      // Reemplazar con imagen placeholder
      img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzUiIGhlaWdodD0iMzUiIHZpZXdCb3g9IjAgMCAzNSAzNSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjM1IiBoZWlnaHQ9IjM1IiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0xNy41IDEwQzE5LjQzIDEwIDIxIDExLjU3IDIxIDEzLjVDMjEgMTUuNDMgMTkuNDMgMTcgMTcuNSAxN0MxNS41NyAxNyAxNCAxNS40MyAxNCAxMy41QzE0IDExLjU3IDE1LjU3IDEwIDE3LjUgMTBaIiBmaWxsPSIjQ0NDQ0NDIi8+CjxwYXRoIGQ9Ik0xMCAyMkMyMCAyMiAyMCAyMiAyMCAyMkgxMEMxMCAyMiAxMCAyMiAxMCAyMloiIGZpbGw9IiNDQ0NDQ0MiLz4KPC9zdmc+';
      img.style.opacity = '0.5';
      img.alt = 'Imagen no encontrada';
      img.title = 'Imagen no encontrada en S3';
    }
  }
  
  // Procesar videos
  for (const video of videos) {
    const exists = await checkImageExists(video.src);
    if (!exists) {
      log("[MODAL-UNIFIED] 🗑️ Video roto encontrado:", video.src);
      brokenCount++;
      
      // Reemplazar con placeholder
      video.style.display = 'none';
      const placeholder = document.createElement('div');
      placeholder.innerHTML = `
        <div style="width: 100%; height: 200px; background: #f5f5f5; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; flex-direction: column;">
          <i class="fas fa-video-slash fa-3x text-muted mb-2"></i>
          <span class="text-muted">Video no encontrado</span>
        </div>
      `;
      video.parentNode.insertBefore(placeholder, video);
    }
  }
  
  // Procesar audios
  for (const audio of audios) {
    const exists = await checkImageExists(audio.src);
    if (!exists) {
      log("[MODAL-UNIFIED] 🗑️ Audio roto encontrado:", audio.src);
      brokenCount++;
      
      // Reemplazar con placeholder
      audio.style.display = 'none';
      const placeholder = document.createElement('div');
      placeholder.innerHTML = `
        <div style="width: 100%; height: 60px; background: #f5f5f5; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;">
          <i class="fas fa-music-slash fa-2x text-muted me-2"></i>
          <span class="text-muted">Audio no encontrado</span>
        </div>
      `;
      audio.parentNode.insertBefore(placeholder, audio);
    }
  }
  
  if (brokenCount > 0) {
    log(`[MODAL-UNIFIED] ✅ Limpieza completada: ${brokenCount} archivos rotos reemplazados`);
  } else {
    log("[MODAL-UNIFIED] ✅ No se encontraron archivos rotos");
  }
}

// Función para mostrar imágenes en modal
function showImageModal(imageSrc, imageTitle) {
  log("[MODAL-UNIFIED] 🖼️ showImageModal llamado con:", { imageSrc, imageTitle });
  
  const modalElement = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  const modalTitle = document.getElementById('imageModalLabel');
  
  if (!modalElement || !modalImage || !modalTitle) {
    console.error("[MODAL-UNIFIED] ❌ Elementos del modal de imagen no encontrados");
    return;
  }
  
  // Configurar título e imagen
  modalTitle.textContent = imageTitle || 'Imagen';
  modalImage.src = imageSrc;
  modalImage.alt = imageTitle || 'Imagen';
  
  // Manejar errores de carga de imagen
  modalImage.onerror = function() {
    log("[MODAL-UNIFIED] ❌ Error cargando imagen:", imageSrc);
    modalImage.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlbiBubyBlbmNvbnRyYWRhPC90ZXh0Pjwvc3ZnPg==';
    modalImage.alt = 'Imagen no encontrada';
    modalTitle.textContent = 'Imagen no encontrada';
  };
  
  modalImage.onload = function() {
    log("[MODAL-UNIFIED] ✅ Imagen cargada correctamente:", imageSrc);
  };
  
  // Mostrar modal
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  
  log("[MODAL-UNIFIED] ✅ Modal de imagen mostrado");
}

// Función para mostrar multimedia en modal
function showMultimediaModal(multimediaSrc, multimediaTitle) {
  log("[MODAL-UNIFIED] 🎬 showMultimediaModal llamado con:", { multimediaSrc, multimediaTitle });
  
  const modalElement = document.getElementById('multimediaModal');
  const modalContent = document.getElementById('multimediaContent');
  const modalTitle = document.getElementById('multimediaModalLabel');
  
  if (!modalElement || !modalContent || !modalTitle) {
    console.error("[MODAL-UNIFIED] ❌ Elementos del modal multimedia no encontrados");
    return;
  }
  
  // Configurar título (sin mostrar ruta completa)
  modalTitle.textContent = 'Reproduciendo Video';
  
  // Determinar tipo de archivo
  const fileExtension = multimediaSrc.split('.').pop()?.toLowerCase();
  let mediaHTML = '';
  
  // Limpiar URL si contiene rutas incorrectas
  let cleanMultimediaSrc = multimediaSrc;
  if (multimediaSrc.includes('/static/uploads//admin/s3/')) {
    cleanMultimediaSrc = multimediaSrc.replace('/static/uploads//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL de multimedia limpiada:", cleanMultimediaSrc);
  } else if (multimediaSrc.includes('/imagenes_subidas//admin/s3/')) {
    cleanMultimediaSrc = multimediaSrc.replace('/imagenes_subidas//admin/s3/', '/admin/s3/');
    log("[MODAL-UNIFIED] 🔧 URL de multimedia limpiada:", cleanMultimediaSrc);
  }
  
  // DETECCIÓN HÍBRIDA S3/LOCAL
  const isS3File = cleanMultimediaSrc.includes('s3.amazonaws.com') || cleanMultimediaSrc.includes('edf-catalogo-tablas.s3') || cleanMultimediaSrc.includes('/admin/s3/') || cleanMultimediaSrc.includes('/s3/');
  
  if (['mp4', 'webm', 'avi', 'mov'].includes(fileExtension)) {
    // Video
    mediaHTML = `
      <div class="text-center mb-3">
        <h5><i class="fas fa-video text-primary"></i> Reproduciendo Video</h5>
      </div>
      <div class="d-flex justify-content-center">
        <video controls class="img-fluid" style="max-width: 100%; height: auto; max-height: 70vh;">
          <source src="${cleanMultimediaSrc}" type="video/${fileExtension}">
          Tu navegador no soporta el elemento de video.
        </video>
      </div>
    `;
  } else if (['mp3', 'wav', 'ogg', 'aac'].includes(fileExtension)) {
    // Audio
    mediaHTML = `
      <div class="text-center mb-3">
        <h5><i class="fas fa-music text-success"></i> Reproduciendo Audio</h5>
      </div>
      <div class="d-flex justify-content-center">
        <audio controls class="img-fluid" style="width: 100%; max-width: 500px;">
          <source src="${cleanMultimediaSrc}" type="audio/${fileExtension}">
          Tu navegador no soporta el elemento de audio.
        </audio>
      </div>
    `;
  } else {
    // Otros tipos
    mediaHTML = `
      <div class="text-center">
        <i class="fas fa-file-video fa-4x text-primary mb-3"></i>
        <h5>Archivo Multimedia</h5>
        <p class="text-muted">Tipo: ${fileExtension || 'Desconocido'}</p>
        <p class="text-muted">${multimediaTitle}</p>
        <a href="${cleanMultimediaSrc}" target="_blank" class="btn btn-primary">
          <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
        </a>
      </div>
    `;
  }
  
  // Configurar contenido y mostrar modal
  modalContent.innerHTML = mediaHTML;
  
  // Agregar manejo de errores para elementos multimedia
  const videoElements = modalContent.querySelectorAll('video');
  const audioElements = modalContent.querySelectorAll('audio');
  
  [...videoElements, ...audioElements].forEach(element => {
    element.onerror = function() {
      log("[MODAL-UNIFIED] ❌ Error cargando multimedia:", cleanMultimediaSrc);
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-exclamation-triangle fa-4x text-warning mb-3"></i>
          <h5>Error al cargar multimedia</h5>
          <p class="text-muted">No se pudo cargar el archivo multimedia.</p>
          <p class="text-danger small">URL: ${cleanMultimediaSrc}</p>
        </div>
      `;
    };
    
    element.onload = function() {
      log("[MODAL-UNIFIED] ✅ Multimedia cargado correctamente:", cleanMultimediaSrc);
    };
  });
  
  // Insertar botones en el modal-footer
  const modalFooter = document.querySelector('#multimediaModal .modal-footer');
  if (modalFooter) {
    modalFooter.innerHTML = `
      <div class="d-flex gap-2 w-100 justify-content-between">
        <div class="d-flex gap-2">
          <a href="${cleanMultimediaSrc}" target="_blank" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
          </a>
          ${isS3File ? 
            `<button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${cleanMultimediaSrc}', '${multimediaTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>` : 
            `<button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${cleanMultimediaSrc}', '${multimediaTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>`
          }
        </div>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      </div>
    `;
  }
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  
  log("[MODAL-UNIFIED] ✅ Modal multimedia mostrado");
}

// ============================================================================
// FUNCIONES DE DESCARGA
// ============================================================================

// Función para descargar archivos S3
function downloadS3File(fileUrl, fileName) {
  log("[MODAL-UNIFIED] 🔧 Descargando archivo S3:", fileUrl);
  
  try {
    const proxyUrl = fileUrl.replace(
      'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
      '/admin/s3/'
    );
    
    const link = document.createElement('a');
    link.href = proxyUrl;
    link.download = fileName || 'archivo';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    log("[MODAL-UNIFIED] ✅ Descarga S3 iniciada");
  } catch (error) {
    console.error("[MODAL-UNIFIED] ❌ Error descargando S3:", error);
    alert('Error al descargar: ' + error.message);
  }
}

// Función para descargar archivos locales
function downloadLocalFile(fileUrl, fileName) {
  log("[MODAL-UNIFIED] 🔧 Descargando archivo local:", fileUrl);
  
  try {
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = fileName || 'archivo';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    log("[MODAL-UNIFIED] ✅ Descarga local iniciada");
  } catch (error) {
    console.error("[MODAL-UNIFIED] ❌ Error descargando local:", error);
    alert('Error al descargar: ' + error.message);
  }
}

// Función para descargar Markdown
function downloadMarkdownFile(fileUrl, fileName) {
  log("[MODAL-UNIFIED] 🔧 Descargando Markdown:", fileUrl);
  
  if (fileUrl.includes('s3.amazonaws.com')) {
    downloadS3File(fileUrl, fileName);
  } else {
    downloadLocalFile(fileUrl, fileName);
  }
}

// Función para descargar documento (genérica)
function downloadDocument() {
  log("[MODAL-UNIFIED] 🔧 downloadDocument llamado");
  
  const modalContent = document.getElementById('documentContent');
  if (!modalContent) return;
  
  // Buscar enlaces de descarga en el contenido del modal
  const downloadLinks = modalContent.querySelectorAll('a[href*="download"], button[onclick*="download"]');
  
  if (downloadLinks.length > 0) {
    // Simular clic en el primer enlace de descarga encontrado
    downloadLinks[0].click();
  } else {
    console.warn("[MODAL-UNIFIED] ⚠️ No se encontraron enlaces de descarga");
  }
}

// Función para descargar multimedia
function downloadMultimedia() {
  log("[MODAL-UNIFIED] 🔧 downloadMultimedia llamado");
  
  const modalContent = document.getElementById('multimediaContent');
  if (!modalContent) return;
  
  // Buscar enlaces de descarga en el contenido del modal
  const downloadLinks = modalContent.querySelectorAll('a[href*="download"], button[onclick*="download"]');
  
  if (downloadLinks.length > 0) {
    // Simular clic en el primer enlace de descarga encontrado
    downloadLinks[0].click();
  } else {
    console.warn("[MODAL-UNIFIED] ⚠️ No se encontraron enlaces de descarga");
  }
}

// Función para abrir PDF en nueva pestaña
function openPDFInNewTab(pdfUrl) {
  log("[MODAL-UNIFIED] 🔧 Abriendo PDF en nueva pestaña:", pdfUrl);
  window.open(pdfUrl, '_blank');
}

// ============================================================================
// FUNCIONES DE UTILIDAD
// ============================================================================

// Función para manejar errores de imagen
function handleImageError(img) {
  log("[MODAL-UNIFIED] ⚠️ Error en imagen:", img);
  if (img && img.src && !img.src.includes('image-error-placeholder.png')) {
    // Evitar bucles infinitos estableciendo el placeholder solo una vez
    img.src = '/static/img/image-error-placeholder.png';
    img.alt = 'Error cargando imagen';
    img.onerror = null; // Remover el handler para evitar bucles
  }
}

// Función para ocultar el spinner de carga de imagen
function hideImageLoadingSpinner() {
  log("[MODAL-UNIFIED] 🔧 Ocultando spinner de carga de imagen");
  const spinner = document.querySelector('.image-loading-spinner');
  if (spinner) {
    spinner.style.display = 'none';
  }
}

// Función para descargar imagen
function downloadImage() {
  log("[MODAL-UNIFIED] 🔧 downloadImage llamado");
  
  const modalImage = document.getElementById('modalImage');
  if (!modalImage || !modalImage.src) {
    console.error("[MODAL-UNIFIED] ❌ No se encontró imagen para descargar");
    return;
  }
  
  const imageSrc = modalImage.src;
  const imageTitle = modalImage.alt || 'imagen';
  
  log("[MODAL-UNIFIED] 🔧 Descargando imagen:", { imageSrc, imageTitle });
  
  try {
    const link = document.createElement('a');
    link.href = imageSrc;
    link.download = imageTitle;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    log("[MODAL-UNIFIED] ✅ Descarga de imagen iniciada");
  } catch (error) {
    console.error("[MODAL-UNIFIED] ❌ Error descargando imagen:", error);
    alert('Error al descargar imagen: ' + error.message);
  }
}

// ============================================================================
// EXPORTACIÓN GLOBAL
// ============================================================================

// Exportar todas las funciones principales
window.showDocumentModal = showDocumentModal;
window.showMarkdownInModal = showMarkdownInModal;
window.showTextInModal = showTextInModal;
window.showImageModal = showImageModal;
window.showMultimediaModal = showMultimediaModal;

// Exportar funciones de descarga
window.downloadS3File = downloadS3File;
window.downloadLocalFile = downloadLocalFile;
window.downloadMarkdownFile = downloadMarkdownFile;
window.downloadDocument = downloadDocument;
window.downloadMultimedia = downloadMultimedia;
window.openPDFInNewTab = openPDFInNewTab;

// Exportar funciones de utilidad
window.handleImageError = handleImageError;
window.hideImageLoadingSpinner = hideImageLoadingSpinner;
window.downloadImage = downloadImage;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

log("[MODAL-UNIFIED] ✅ Todas las funciones exportadas correctamente");
log("[MODAL-UNIFIED] 🎯 Sistema de modales unificado listo");
log("[MODAL-UNIFIED] 📅 VERSIÓN: 2025-01-04-09:20 - UNIFICADA + FUNCIONES COMPLETAS + DOWNLOAD IMAGE");

// Verificación final de funciones disponibles
log("[MODAL-UNIFIED] 🔍 VERIFICACIÓN FINAL:");
log("  - showImageModal:", typeof window.showImageModal);
log("  - showDocumentModal:", typeof window.showDocumentModal);
log("  - showMultimediaModal:", typeof window.showMultimediaModal);
log("  - downloadImage:", typeof window.downloadImage);
log("  - handleImageError:", typeof window.handleImageError);
log("  - hideImageLoadingSpinner:", typeof window.hideImageLoadingSpinner);

// Ejecutar limpieza de imágenes rotas después de que la página se cargue completamente
// COMENTADO TEMPORALMENTE PARA EVITAR INTERFERENCIA CON IMÁGENES FUNCIONANDO
// if (document.readyState === 'loading') {
//   document.addEventListener('DOMContentLoaded', cleanupBrokenImages);
// } else {
//   // Si el DOM ya está cargado, ejecutar inmediatamente
//   setTimeout(cleanupBrokenImages, 1000); // Esperar 1 segundo para que las imágenes se carguen
// }
