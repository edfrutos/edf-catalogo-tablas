// Funciones de modal para compatibilidad con pywebview - VERSIÓN FINAL
// Este archivo define las funciones que faltan en el contexto de pywebview

// Detectar si estamos en pywebview
const isPyWebView = typeof pywebview !== "undefined";
console.log("[MODAL-FINAL] Detección de pywebview:", {
  isPyWebView,
  pywebview: typeof pywebview,
});

// Función para mostrar PDF en modal - SOLUCIÓN SIMPLIFICADA
function showPDFInModal(pdfUrl, pdfTitle) {
  console.log("[PDF-FINAL] 🎯 Usuario solicitó ver PDF en modal:", pdfUrl);

  // SOLUCIÓN CORREGIDA: Usar modal Bootstrap en lugar de modificar DOM directamente
  console.log("[PDF-FINAL] 🔍 Buscando elementos del modal...");
  
  const modalElement = document.getElementById("documentModal");
  const modalContent = document.getElementById("documentContent");
  
  // BUSCAR TÍTULO ALTERNATIVO: Intentar diferentes selectores
  let modalTitle = document.getElementById("documentTitle");
  if (!modalTitle) {
    modalTitle = modalElement?.querySelector('.modal-title');
    console.log("[PDF-FINAL] 🔍 Título alternativo encontrado:", !!modalTitle);
  }

  console.log("[PDF-FINAL] 🔍 Elementos encontrados:", {
    modalElement: !!modalElement,
    modalContent: !!modalContent,
    modalTitle: !!modalTitle
  });

  if (!modalElement || !modalContent) {
    console.error(
      "[PDF-FINAL] ❌ Elementos esenciales del modal no encontrados"
    );
    
    // INTENTAR ALTERNATIVA: Buscar cualquier modal disponible
    const allModals = document.querySelectorAll('.modal');
    console.log("[PDF-FINAL] 🔍 Modales disponibles en la página:", allModals.length);
    allModals.forEach((modal, index) => {
      console.log(`[PDF-FINAL] 🔍 Modal ${index}:`, modal.id, modal.className);
    });
    
    alert("Error: Modal no disponible");
    return;
  }

  // SOLUCIÓN ALTERNATIVA: Si no hay título, usar el modal sin título
  if (!modalTitle) {
    console.log("[PDF-FINAL] ⚠️ Título no encontrado, continuando sin título");
  }

  // DETECCIÓN HÍBRIDA: Determinar si es S3 o local
  let isLocalFile = false;
  let localUrl = pdfUrl;
  
  if (pdfUrl.includes('s3.') || pdfUrl.includes('amazonaws.com')) {
    // Es un archivo S3
    console.log("[PDF-FINAL] 🔍 Archivo S3 detectado:", pdfUrl);
    isLocalFile = false;
  } else if (pdfUrl.includes('/imagenes_subidas/') || pdfUrl.includes('/uploads/') || pdfUrl.includes('static/')) {
    // Es un archivo local
    console.log("[PDF-FINAL] 🔍 Archivo local detectado:", pdfUrl);
    isLocalFile = true;
    
    // MAPEO DE RUTAS: Convertir /imagenes_subidas/ a /static/uploads/
    if (pdfUrl.includes('/imagenes_subidas/')) {
      const fileName = pdfUrl.split('/').pop();
      localUrl = `/static/uploads/${fileName}`;
      console.log("[PDF-FINAL] 🔧 Mapeo de ruta:", pdfUrl, "→", localUrl);
    } else if (pdfUrl.startsWith('/uploads/')) {
      localUrl = `/static${pdfUrl}`;
      console.log("[PDF-FINAL] 🔧 Ruta uploads convertida:", pdfUrl, "→", localUrl);
    } else if (pdfUrl.includes('static/')) {
      localUrl = pdfUrl;
      console.log("[PDF-FINAL] 🔧 Ruta static mantenida:", pdfUrl);
    }
  } else {
    // URL externa o desconocida
    console.log("[PDF-FINAL] 🔍 URL externa detectada:", pdfUrl);
    isLocalFile = false;
  }

  console.log("[PDF-FINAL] 🔧 URL local del PDF:", localUrl);

  // Configurar título del modal (si existe)
  if (modalTitle) {
    modalTitle.textContent = pdfTitle || "Documento PDF";
    console.log("[PDF-FINAL] ✅ Título del modal configurado");
  } else {
    console.log("[PDF-FINAL] ⚠️ Título del modal no disponible, continuando sin título");
  }

  // SOLUCIÓN COMPLETA: Cargar PDF.js y renderizar el PDF
  modalContent.innerHTML = `
        <div class="text-center p-4">
            <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
            <h5>Documento PDF</h5>
            <p class="text-muted mb-4">
                <strong>Archivo:</strong> ${pdfTitle || "PDF"}<br>
                <strong>Tipo:</strong> PDF<br>
                <strong>Ubicación:</strong> ${isLocalFile ? 'Local' : 'S3'}
            </p>
            
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                <strong>Nota:</strong> Cargando PDF con PDF.js...
            </div>
            
            <div id="pdf-viewer-container" class="mt-4">
                <canvas id="pdf-canvas" style="width: 100%; height: 600px; border: 2px solid #007bff; border-radius: 8px; background-color: #ffffff;"></canvas>
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

  // Mostrar el modal primero
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // VERIFICACIÓN INMEDIATA: Comprobar que el contenido del modal se mantiene
  console.log("[PDF-FINAL] 🔍 Modal mostrado, verificando contenido...");
  console.log("[PDF-FINAL] 🔍 Contenido del modal después de mostrarlo:", modalContent.innerHTML.substring(0, 300));
  
  // Verificar que el contenedor del PDF esté disponible
  const pdfContainer = document.getElementById("pdf-viewer-container");
  const canvas = document.getElementById("pdf-canvas");
  
  if (pdfContainer && canvas) {
    console.log("[PDF-FINAL] ✅ Contenedor PDF y canvas encontrados");
    
    // CARGAR PDF.js DESDE CDN Y RENDERIZAR PDF
    loadAndRenderPDF(localUrl, canvas, pdfTitle);
  } else {
    console.error("[PDF-FINAL] ❌ Contenedor PDF o canvas NO encontrados!");
  }
  
  // IR DIRECTO A PDF.js - Sin iframe, sin fallback
  console.log("[PDF-FINAL] 🚀 Iniciando PDF.js directamente...");
  
  // Llamar directamente a PDF.js
  attemptPDFJSFallback(localUrl, pdfContainer, modalContent);
}

// Función de fallback usando PDF.js
function attemptPDFJSFallback(pdfUrl, container, modalContent) {
  console.log("[PDF-FINAL] 🔄 Intentando fallback con PDF.js...");
  console.log("[PDF-FINAL] 🔍 Parámetros recibidos:");
  console.log("[PDF-FINAL] - pdfUrl:", pdfUrl);
  console.log("[PDF-FINAL] - container:", container);
  console.log("[PDF-FINAL] - modalContent:", modalContent);

  // Verificar que PDF.js esté disponible
  if (typeof pdfjsLib === "undefined") {
    console.error("[PDF-FINAL] ❌ PDF.js no está disponible para fallback");
    console.log("[PDF-FINAL] 🔍 typeof pdfjsLib:", typeof pdfjsLib);
    console.log("[PDF-FINAL] 🔍 pdfjsLib en window:", !!window.pdfjsLib);
    showPDFError(container, modalContent, "PDF.js no disponible");
    return;
  }

  console.log("[PDF-FINAL] ✅ PDF.js está disponible:", typeof pdfjsLib);
  console.log("[PDF-FINAL] 🔍 Versión PDF.js:", pdfjsLib.version);

  // Mostrar loading
  container.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando PDF...</span>
            </div>
            <p class="mt-2">Cargando PDF con PDF.js...</p>
        </div>
    `;

  console.log("[PDF-FINAL] 🔍 Loading mostrado en contenedor");

  // SOLUCIÓN CRÍTICA: Configurar worker de PDF.js
  if (pdfjsLib.GlobalWorkerOptions) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    console.log("[PDF-FINAL] 🔧 Worker de PDF.js configurado");
  }

  // Intentar cargar PDF con PDF.js
  console.log("[PDF-FINAL] 🚀 Iniciando carga de PDF con URL:", pdfUrl);
  
  // SOLUCIÓN CRÍTICA: Usar fetch para cargar el PDF primero
  fetch(pdfUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      console.log("[PDF-FINAL] ✅ Fetch exitoso, convirtiendo a arrayBuffer");
      return response.arrayBuffer();
    })
    .then(arrayBuffer => {
      console.log("[PDF-FINAL] ✅ ArrayBuffer creado, tamaño:", arrayBuffer.byteLength);
      
      // Cargar PDF desde arrayBuffer
      return pdfjsLib.getDocument({data: arrayBuffer}).promise;
    })
    .then(function (pdf) {
      console.log(
        "[PDF-FINAL] ✅ PDF cargado con PDF.js, páginas:",
        pdf.numPages
      );

      // Renderizar primera página
      return pdf.getPage(1);
    })
    .then(function (page) {
      console.log("[PDF-FINAL] ✅ Primera página obtenida, iniciando renderizado...");
      
      const viewport = page.getViewport({ scale: 1.5 });
      console.log("[PDF-FINAL] 🔍 Viewport creado:", viewport);

      // Crear canvas
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      canvas.id = "pdf-canvas";
      canvas.style.cssText = `
                width: 100%;
                height: auto;
                border: 2px solid #28a745;
                border-radius: 8px;
                background-color: #ffffff;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                z-index: 9999 !important;
            `;

      console.log("[PDF-FINAL] 🔍 Canvas creado con dimensiones:", canvas.width, "x", canvas.height);

      // Agregar canvas al contenedor ANTES de renderizar
      container.innerHTML = "";
      container.appendChild(canvas);
      
      console.log("[PDF-FINAL] 🔍 Canvas agregado al contenedor");

      // Renderizar página
      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      console.log("[PDF-FINAL] 🔄 Iniciando renderizado de página...");
      return page.render(renderContext).promise;
    })
    .then(function () {
      console.log("[PDF-FINAL] ✅ PDF renderizado exitosamente en canvas");

      // El canvas ya está en el contenedor, solo actualizar mensaje
      const alertElement = modalContent.querySelector(".alert");
      if (alertElement) {
        alertElement.className = "alert alert-success";
        alertElement.innerHTML = `
                    <i class="fas fa-check-circle"></i>
                    <strong>¡Éxito!</strong> PDF visible en modal
                `;
      }
      
      console.log("[PDF-FINAL] ✅ Canvas PDF visible y estable en modal");
      
      // VERIFICACIÓN VISUAL: Comprobar estado visual del canvas
      const canvasElement = container.querySelector("#pdf-canvas");
      if (canvasElement) {
        const computedStyle = window.getComputedStyle(canvasElement);
        console.log("[PDF-FINAL] 🔍 Estado visual del canvas:");
        console.log("[PDF-FINAL] - Display:", computedStyle.display);
        console.log("[PDF-FINAL] - Visibility:", computedStyle.visibility);
        console.log("[PDF-FINAL] - Opacity:", computedStyle.opacity);
        console.log("[PDF-FINAL] - Width:", computedStyle.width);
        console.log("[PDF-FINAL] - Height:", computedStyle.height);
        console.log("[PDF-FINAL] - Position:", computedStyle.position);
        console.log("[PDF-FINAL] - Z-index:", computedStyle.zIndex);
        
        // FORZAR VISIBILIDAD: Asegurar que el canvas sea visible
        canvasElement.style.display = "block";
        canvasElement.style.visibility = "visible";
        canvasElement.style.opacity = "1";
        canvasElement.style.zIndex = "9999";
        
        console.log("[PDF-FINAL] 🔧 Visibilidad del canvas forzada");
        
        // Verificar si el canvas tiene contenido
        if (canvasElement.getContext) {
          const context = canvasElement.getContext('2d');
          const imageData = context.getImageData(0, 0, 1, 1);
          console.log("[PDF-FINAL] - Canvas tiene contexto 2D:", !!context);
          console.log("[PDF-FINAL] - Canvas tiene datos de imagen:", !!imageData);
        }
        
        // AGREGAR CONTROLES DE PDF: Zoom, navegación, etc.
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'pdf-controls mt-3';
        controlsContainer.innerHTML = `
          <div class="btn-group" role="group" aria-label="Controles de PDF">
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(0.5)" title="Zoom Out">
              <i class="fas fa-search-minus"></i> Zoom Out
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.0)" title="Zoom Normal">
              <i class="fas fa-search"></i> 100%
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.5)" title="Zoom In">
              <i class="fas fa-search-plus"></i> Zoom In
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(2.0)" title="Zoom Doble">
              <i class="fas fa-expand"></i> 200%
            </button>
          </div>
          <div class="btn-group ms-2" role="group" aria-label="Navegación de PDF">
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="rotatePDF(-90)" title="Rotar Izquierda">
              <i class="fas fa-undo"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="rotatePDF(90)" title="Rotar Derecha">
              <i class="fas fa-redo"></i>
            </button>
          </div>
          <div class="btn-group ms-2" role="group" aria-label="Herramientas de PDF">
            <button type="button" class="btn btn-outline-info btn-sm" onclick="fitToWidth()" title="Ajustar al Ancho">
              <i class="fas fa-arrows-alt-h"></i> Ajustar
            </button>
            <button type="button" class="btn btn-outline-success btn-sm" onclick="printPDF()" title="Imprimir PDF">
              <i class="fas fa-print"></i> Imprimir
            </button>
          </div>
        `;
        
        // Agregar controles después del canvas
        container.appendChild(controlsContainer);
        console.log("[PDF-FINAL] 🔧 Controles de PDF agregados");
        
        // AGREGAR FUNCIONES DE CONTROL al objeto window
        window.zoomPDF = function(scale) {
          if (canvasElement) {
            canvasElement.style.width = (716 * scale) + 'px';
            canvasElement.style.height = 'auto';
            console.log(`[PDF-FINAL] 🔧 Zoom aplicado: ${scale * 100}%`);
          }
        };
        
        window.rotatePDF = function(degrees) {
          if (canvasElement) {
            const currentRotation = parseInt(canvasElement.style.transform.replace('rotate(', '').replace('deg)', '') || 0);
            const newRotation = currentRotation + degrees;
            canvasElement.style.transform = `rotate(${newRotation}deg)`;
            console.log(`[PDF-FINAL] 🔧 Rotación aplicada: ${newRotation}°`);
          }
        };
        
        window.fitToWidth = function() {
          if (canvasElement) {
            const containerWidth = container.offsetWidth;
            const scale = containerWidth / 716;
            canvasElement.style.width = '100%';
            canvasElement.style.height = 'auto';
            console.log(`[PDF-FINAL] 🔧 Ajustado al ancho del contenedor`);
          }
        };
        
        window.printPDF = function() {
          const printWindow = window.open('', '_blank');
          printWindow.document.write(`
            <html>
              <head><title>PDF - ${pdfTitle || 'Documento'}</title></head>
              <body>
                <img src="${canvasElement.toDataURL()}" style="width: 100%; height: auto;">
              </body>
            </html>
          `);
          printWindow.document.close();
          printWindow.print();
          console.log("[PDF-FINAL] 🔧 Ventana de impresión abierta");
        };
      }
      
      // DIAGNÓSTICO: Verificar qué está pasando con el contenido
      console.log("[PDF-FINAL] 🔍 Contenido del contenedor después del renderizado:", container.innerHTML.substring(0, 300));
      
      // DIAGNÓSTICO: Verificar que el canvas esté realmente en el DOM
      const canvasInDOM = document.getElementById("pdf-canvas");
      if (canvasInDOM) {
        console.log("[PDF-FINAL] ✅ Canvas encontrado en DOM con ID:", canvasInDOM.id);
        console.log("[PDF-FINAL] 🔍 Canvas padre:", canvasInDOM.parentElement);
      } else {
        console.error("[PDF-FINAL] ❌ Canvas NO encontrado en DOM después del renderizado");
      }
      
      // DIAGNÓSTICO: Verificar el estado del modal
      const modalElement = document.getElementById("documentModal");
      if (modalElement) {
        console.log("[PDF-FINAL] 🔍 Modal visible:", modalElement.classList.contains("show"));
        console.log("[PDF-FINAL] 🔍 Modal display:", window.getComputedStyle(modalElement).display);
      }
    })
    .catch(function (error) {
      console.error("[PDF-FINAL] ❌ Error con PDF.js:", error);
      showPDFError(
        container,
        modalContent,
        `Error con PDF.js: ${error.message}`
      );
    });
}

// Función para mostrar error de PDF
function showPDFError(container, modalContent, errorMessage) {
  console.log("[PDF-FINAL] ❌ Mostrando error:", errorMessage);

  container.innerHTML = `
        <div class="text-center p-4">
            <i class="fas fa-exclamation-triangle fa-4x text-warning mb-3"></i>
            <h5>PDF no visible en modal</h5>
            <p class="text-muted mb-4">
                El archivo PDF existe y es válido, pero no se puede mostrar directamente en el modal.<br>
                <strong>Razón:</strong> ${errorMessage}
            </p>
            
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                <strong>💡 Soluciones disponibles:</strong><br>
                • <strong>Abrir en Nueva Pestaña:</strong> El PDF se abrirá en una nueva ventana del navegador<br>
                • <strong>Descargar:</strong> Guardar el archivo PDF en tu dispositivo
            </div>
            
            <div class="mt-3">
                <small class="text-muted">
                    <i class="fas fa-lightbulb"></i>
                    <strong>Consejo:</strong> La mayoría de PDFs se abren mejor en aplicaciones nativas como Adobe Reader, Preview (Mac), o el visor del navegador.
                </small>
            </div>
        </div>
    `;

  // Actualizar mensaje principal
  const alertElement = modalContent.querySelector(".alert");
  if (alertElement) {
    alertElement.className = "alert alert-warning";
    alertElement.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Limitación técnica:</strong> PDF no visible en modal, pero archivo completamente accesible
        `;
  }
}

// Función para abrir PDF en nueva pestaña
function openPDFInNewTab(pdfUrl) {
  console.log("[PDF-FINAL] 🎯 openPDFInNewTab llamado con:", pdfUrl);

  try {
    // Construir URL local para PDFs
    let localUrl = pdfUrl;
    if (pdfUrl.startsWith("/uploads/")) {
      localUrl = `/static${pdfUrl}`;
    }

    console.log("[PDF-FINAL] 🔧 Abriendo PDF en nueva pestaña:", localUrl);
    window.open(localUrl, "_blank");
    console.log("[PDF-FINAL] ✅ PDF abierto en nueva pestaña");
  } catch (error) {
    console.error("[PDF-FINAL] ❌ Error abriendo PDF:", error);
  }
}

// Función para descargar archivo local
function downloadLocalFile(fileUrl, fileName) {
  console.log("[DOWNLOAD-FINAL] 🎯 Descargando archivo local:", fileUrl);

  try {
    // Determinar URL local para descarga
    let localUrl = fileUrl;
    if (fileUrl.startsWith("/uploads/")) {
      localUrl = `/static/uploads/documents/${fileUrl.split("/").pop()}`;
    }

    console.log("[DOWNLOAD-FINAL] 🔧 URL de descarga:", localUrl);

    // SOLUCIÓN ESPECÍFICA PARA PYWEBVIEW: usar fetch + blob
    if (window.isPyWebView) {
      console.log(
        "[DOWNLOAD-FINAL] 🔧 PyWebView detectado, usando fetch + blob para descarga forzada"
      );

      // Mostrar indicador de descarga
      const downloadIndicator = document.createElement("div");
      downloadIndicator.innerHTML = `
                <div class="alert alert-info" style="position: fixed; top: 20px; right: 20px; z-index: 10000;">
                    <i class="fas fa-download"></i> Descargando archivo...
                </div>
            `;
      document.body.appendChild(downloadIndicator);

      // Descargar usando fetch
      fetch(localUrl)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.blob();
        })
        .then((blob) => {
          console.log("[DOWNLOAD-FINAL] ✅ Blob creado, tamaño:", blob.size);

          // Crear URL del blob
          const blobUrl = window.URL.createObjectURL(blob);

          // Crear enlace de descarga con atributos forzados
          const downloadLink = document.createElement("a");
          downloadLink.href = blobUrl;
          downloadLink.download = fileName || "archivo";
          downloadLink.style.display = "none";
          downloadLink.setAttribute(
            "data-downloadurl",
            `application/octet-stream:${fileName}:${blobUrl}`
          );

          // Agregar al DOM
          document.body.appendChild(downloadLink);

          // Simular clic con evento personalizado
          const clickEvent = new MouseEvent("click", {
            view: window,
            bubbles: true,
            cancelable: true,
            ctrlKey: false,
            metaKey: false,
          });

          downloadLink.dispatchEvent(clickEvent);

          // Limpiar después de un tiempo
          setTimeout(() => {
            if (document.body.contains(downloadLink)) {
              document.body.removeChild(downloadLink);
            }
            window.URL.revokeObjectURL(blobUrl);
            if (document.body.contains(downloadIndicator)) {
              document.body.removeChild(downloadIndicator);
            }
          }, 2000);

          console.log(
            "[DOWNLOAD-FINAL] ✅ Descarga iniciada usando blob en PyWebView"
          );
        })
        .catch((error) => {
          console.error("[DOWNLOAD-FINAL] ❌ Error en fetch:", error);

          // Limpiar indicador
          if (document.body.contains(downloadIndicator)) {
            document.body.removeChild(downloadIndicator);
          }

          // Fallback: mostrar mensaje de error
          const errorAlert = document.createElement("div");
          errorAlert.innerHTML = `
                        <div class="alert alert-danger" style="position: fixed; top: 20px; right: 20px; z-index: 10000;">
                            <i class="fas fa-exclamation-triangle"></i> Error al descargar: ${error.message}
                        </div>
                    `;
          document.body.appendChild(errorAlert);

          setTimeout(() => {
            if (document.body.contains(errorAlert)) {
              document.body.removeChild(errorAlert);
            }
          }, 3000);
        });
    } else {
      // En navegador normal, crear enlace de descarga
      const downloadLink = document.createElement("a");
      downloadLink.href = localUrl;
      downloadLink.download = fileName || "archivo";
      downloadLink.target = "_blank";
      downloadLink.rel = "noopener";
      downloadLink.style.display = "none";

      document.body.appendChild(downloadLink);
      downloadLink.click();

      setTimeout(() => {
        if (document.body.contains(downloadLink)) {
          document.body.removeChild(downloadLink);
        }
      }, 1000);

      console.log("[DOWNLOAD-FINAL] ✅ Archivo descargado en navegador normal");
    }
  } catch (error) {
    console.error(
      "[DOWNLOAD-FINAL] ❌ Error descargando archivo local:",
      error
    );
    alert("Error al descargar el archivo");
  }
}

// Función para mostrar Markdown en modal
function showMarkdownInModal(markdownUrl, markdownTitle) {
  console.log(
    "[MARKDOWN-FINAL] 🎯 Usuario solicitó ver Markdown en modal:",
    markdownUrl
  );

  // Usar modal Bootstrap
  const modalElement = document.getElementById("documentModal");
  const modalContent = document.getElementById("documentContent");
  const modalTitle = document.getElementById("documentTitle");

  if (!modalElement || !modalContent || !modalTitle) {
    console.error(
      "[MARKDOWN-FINAL] ❌ Elementos del modal Bootstrap no encontrados"
    );
    alert("Error: Modal no disponible");
    return;
  }

  // Configurar título del modal
  modalTitle.textContent = markdownTitle || "Documento Markdown";

  // Mostrar loading
  modalContent.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2">Cargando documento Markdown...</p>
        </div>
    `;

  // Mostrar el modal primero
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // Determinar URL local para Markdown
  let localUrl = markdownUrl;
  if (markdownUrl.startsWith("/uploads/")) {
    localUrl = `/static/uploads/documents/${markdownUrl.split("/").pop()}`;
  }

  // Cargar Markdown desde URL local
  fetch(localUrl)
    .then((response) => response.text())
    .then((markdownText) => {
      console.log(
        "[MARKDOWN-FINAL] ✅ Contenido Markdown cargado, longitud:",
        markdownText.length
      );

      // Convertir Markdown a HTML (simplificado)
      const htmlContent = markdownText
        .replace(/^### (.*$)/gim, "<h3>$1</h3>")
        .replace(/^## (.*$)/gim, "<h2>$1</h2>")
        .replace(/^# (.*$)/gim, "<h1>$1</h1>")
        .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
        .replace(/\*(.*)\*/gim, "<em>$1</em>")
        .replace(/\n/gim, "<br>");

      // Configurar contenido del modal
      modalContent.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-file-code fa-4x text-info mb-3"></i>
                    <h5>Documento Markdown</h5>
                    <p class="text-muted mb-4">
                        <strong>Archivo:</strong> ${markdownTitle || "Markdown"}<br>
                        <strong>Tipo:</strong> Markdown<br>
                        <strong>Ubicación:</strong> Local
                    </p>
                    
                    <div class="markdown-content-wrapper" style="max-height: 50vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left; margin-bottom: 20px;">
                        <div class="markdown-rendered">
                            ${htmlContent}
                        </div>
                    </div>
                    
                    <div class="btn-group mt-3" role="group">
                        <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${markdownUrl}')">
                            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
                        </button>
                        <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${markdownUrl}', '${markdownTitle}')">
                            <i class="fas fa-download"></i> Descargar
                        </button>
                    </div>
                </div>
            `;

      console.log(
        "[MARKDOWN-FINAL] ✅ Modal de Markdown configurado correctamente"
      );
    })
    .catch((error) => {
      console.error("[MARKDOWN-FINAL] ❌ Error cargando Markdown:", error);
      modalContent.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
                    <h5>Error al cargar el archivo</h5>
                    <p class="text-muted mb-4">
                        No se pudo cargar el archivo Markdown.<br>
                        Error: ${error.message}
                    </p>
                    
                    <div class="btn-group mt-3" role="group">
                        <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${markdownUrl}', '${markdownTitle}')">
                            <i class="fas fa-download"></i> Descargar
                        </button>
                    </div>
                </div>
            `;
    });
}

// Función para mostrar Texto en modal
function showTextInModal(textUrl, textTitle) {
  console.log("[TEXT-FINAL] 🎯 Usuario solicitó ver Texto en modal:", textUrl);

  // Usar modal Bootstrap
  const modalElement = document.getElementById("documentModal");
  const modalContent = document.getElementById("documentContent");
  const modalTitle = document.getElementById("documentTitle");

  if (!modalElement || !modalContent || !modalTitle) {
    console.error(
      "[TEXT-FINAL] ❌ Elementos del modal Bootstrap no encontrados"
    );
    alert("Error: Modal no disponible");
    return;
  }

  // Configurar título del modal
  modalTitle.textContent = textTitle || "Documento de Texto";

  // Mostrar loading
  modalContent.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2">Cargando documento de texto...</p>
        </div>
    `;

  // Mostrar el modal primero
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // Determinar URL local para Texto
  let localUrl = textUrl;
  if (textUrl.startsWith("/uploads/")) {
    localUrl = `/static/uploads/documents/${textUrl.split("/").pop()}`;
  }

  // Cargar Texto desde URL local
  fetch(localUrl)
    .then((response) => response.text())
    .then((textContent) => {
      console.log(
        "[TEXT-FINAL] ✅ Contenido de texto cargado, longitud:",
        textContent.length
      );

      // Configurar contenido del modal
      modalContent.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-file-alt fa-4x text-secondary mb-3"></i>
                    <h5>Documento de Texto</h5>
                    <p class="text-muted mb-4">
                        <strong>Archivo:</strong> ${textTitle || "Texto"}<br>
                        <strong>Tipo:</strong> Texto<br>
                        <strong>Ubicación:</strong> Local
                    </p>
                    
                    <div class="text-content-wrapper" style="max-height: 50vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left; margin-bottom: 20px; font-family: monospace; white-space: pre-wrap;">
                        <div class="text-content">
                            ${textContent}
                        </div>
                    </div>
                    
                    <div class="btn-group mt-3" role="group">
                        <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${textUrl}')">
                            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
                        </button>
                        <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${textUrl}', '${textTitle}')">
                            <i class="fas fa-download"></i> Descargar
                        </button>
                    </div>
                </div>
            `;

      console.log("[TEXT-FINAL] ✅ Modal de texto configurado correctamente");
    })
    .catch((error) => {
      console.error("[TEXT-FINAL] ❌ Error cargando texto:", error);
      modalContent.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
                    <h5>Error al cargar el archivo</h5>
                    <p class="text-muted mb-4">
                        No se pudo cargar el archivo de texto.<br>
                        Error: ${error.message}
                    </p>
                    
                    <div class="btn-group mt-3" role="group">
                        <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${textUrl}', '${textTitle}')">
                            <i class="fas fa-download"></i> Descargar
                        </button>
                    </div>
                </div>
            `;
    });
}

// Exportar funciones para uso global
window.showPDFInModal = showPDFInModal;
window.openPDFInNewTab = openPDFInNewTab;
window.downloadLocalFile = downloadLocalFile;

// Función principal para mostrar documentos (compatibilidad con templates)
function showDocumentModal(documentSrc, documentTitle) {
  console.log("[MODAL-FINAL] 🔍 showDocumentModal llamado con:", { documentSrc, documentTitle });
  
  // DETECCIÓN HÍBRIDA: Determinar si es S3 o local
  let isLocalFile = false;
  let localPath = '';
  
  if (documentSrc.includes('s3.') || documentSrc.includes('amazonaws.com')) {
    // Es un archivo S3
    console.log('[MODAL-FINAL] Archivo S3 detectado:', documentSrc);
    isLocalFile = false;
  } else if (documentSrc.includes('/uploads/') || documentSrc.includes('static/') || documentSrc.includes('/imagenes_subidas/')) {
    // Es un archivo local
    console.log('[MODAL-FINAL] Archivo local detectado:', documentSrc);
    isLocalFile = true;
    
    // Construir ruta local
    if (documentSrc.includes('/imagenes_subidas/')) {
      // Convertir /imagenes_subidas/filename a /static/uploads/filename
      const filename = documentSrc.replace('/imagenes_subidas/', '');
      localPath = `/static/uploads/${filename}`;
      console.log('[MODAL-FINAL] 🔧 Ruta convertida:', documentSrc, '→', localPath);
    } else if (documentSrc.includes('/uploads/')) {
      localPath = documentSrc;
    } else {
      localPath = documentSrc;
    }
  } else {
    // URL externa o desconocida
    console.log('[MODAL-FINAL] URL externa detectada:', documentSrc);
    isLocalFile = false;
  }
  
  // DETERMINAR TIPO DE ARCHIVO
  const fileExtension = documentTitle.split('.').pop().toLowerCase();
  console.log('[MODAL-FINAL] Extensión del archivo:', fileExtension);
  
  // MOSTRAR MODAL SEGÚN TIPO
  if (fileExtension === 'pdf') {
    if (isLocalFile) {
      // Usar nuestro sistema de PDF local
      if (typeof showPDFInModal !== 'undefined') {
        showPDFInModal(localPath, documentTitle);
      } else {
        console.error('[MODAL-FINAL] ❌ showPDFInModal no disponible');
        alert('Error: Función de PDF no disponible');
      }
    } else {
      // Archivo S3 - usar sistema existente
      console.log('[MODAL-FINAL] Archivo S3 - redirigiendo a nueva pestaña');
      window.open(documentSrc, '_blank');
    }
  } else if (fileExtension === 'md') {
    if (isLocalFile) {
      // Usar nuestro sistema de Markdown local
      if (typeof showMarkdownInModal !== 'undefined') {
        showMarkdownInModal(localPath, documentTitle);
      } else {
        console.error('[MODAL-FINAL] ❌ showMarkdownInModal no disponible');
        alert('Error: Función de Markdown no disponible');
      }
    } else {
      console.log('[MODAL-FINAL] Archivo S3 - redirigiendo a nueva pestaña');
      window.open(documentSrc, '_blank');
    }
  } else if (fileExtension === 'txt') {
    if (isLocalFile) {
      // Usar nuestro sistema de texto local
      if (typeof showTextInModal !== 'undefined') {
        showTextInModal(localPath, documentTitle);
      } else {
        console.error('[MODAL-FINAL] ❌ showTextInModal no disponible');
        alert('Error: Función de texto no disponible');
      }
    } else {
      console.log('[MODAL-FINAL] Archivo S3 - redirigiendo a nueva pestaña');
      window.open(documentSrc, '_blank');
    }
  } else {
    // Otros tipos de archivo - redirigir a nueva pestaña
    console.log('[MODAL-FINAL] Tipo de archivo no soportado - redirigiendo a nueva pestaña');
    window.open(documentSrc, '_blank');
  }
}

// Función para cargar PDF.js y renderizar PDF
function loadAndRenderPDF(pdfUrl, canvas, pdfTitle) {
  console.log("[PDF-FINAL] 🚀 Iniciando carga de PDF.js y renderizado...");
  
  // CARGAR PDF.js DESDE CDN
  if (typeof pdfjsLib === 'undefined') {
    console.log("[PDF-FINAL] 📥 PDF.js no disponible, cargando desde CDN...");
    
    // Crear script para PDF.js
    const pdfScript = document.createElement('script');
    pdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
    pdfScript.onload = function() {
      console.log("[PDF-FINAL] ✅ PDF.js cargado desde CDN");
      
      // Cargar worker
      if (pdfjsLib.GlobalWorkerOptions) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        console.log("[PDF-FINAL] 🔧 Worker de PDF.js configurado");
      }
      
      // Renderizar PDF
      renderPDFWithJS(pdfUrl, canvas, pdfTitle);
    };
    
    document.head.appendChild(pdfScript);
  } else {
    console.log("[PDF-FINAL] ✅ PDF.js ya disponible");
    renderPDFWithJS(pdfUrl, canvas, pdfTitle);
  }
}

// Función para renderizar PDF con PDF.js
function renderPDFWithJS(pdfUrl, canvas, pdfTitle) {
  console.log("[PDF-FINAL] 🎨 Iniciando renderizado de PDF:", pdfUrl);
  
  // Configurar canvas
  const ctx = canvas.getContext('2d');
  canvas.style.display = 'block';
  
  // Cargar PDF usando fetch
  fetch(pdfUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      console.log("[PDF-FINAL] ✅ Fetch exitoso, convirtiendo a arrayBuffer");
      return response.arrayBuffer();
    })
    .then(arrayBuffer => {
      console.log("[PDF-FINAL] ✅ ArrayBuffer creado, tamaño:", arrayBuffer.byteLength);
      
      // Cargar PDF desde arrayBuffer
      return pdfjsLib.getDocument({data: arrayBuffer}).promise;
    })
    .then(function (pdf) {
      console.log("[PDF-FINAL] ✅ PDF cargado, páginas:", pdf.numPages);
      
      // Renderizar primera página
      return pdf.getPage(1);
    })
    .then(function (page) {
      console.log("[PDF-FINAL] ✅ Primera página obtenida");
      
      // Configurar viewport
      const viewport = page.getViewport({scale: 1.0});
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      
      // Renderizar página
      const renderContext = {
        canvasContext: ctx,
        viewport: viewport
      };
      
      return page.render(renderContext).promise;
    })
    .then(function () {
      console.log("[PDF-FINAL] ✅ PDF renderizado exitosamente en el modal!");
      
      // Agregar controles de zoom
      addPDFControls(canvas);
    })
    .catch(function (error) {
      console.error("[PDF-FINAL] ❌ Error renderizando PDF:", error);
      
      // Mostrar error en el canvas
      ctx.fillStyle = '#f8d7da';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#721c24';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Error al cargar PDF', canvas.width/2, canvas.height/2);
      ctx.fillText(error.message, canvas.width/2, canvas.height/2 + 30);
    });
}

// Función para agregar controles de zoom
function addPDFControls(canvas) {
  console.log("[PDF-FINAL] 🔧 Agregando controles de zoom...");
  
  const container = canvas.parentElement;
  
  // Crear controles
  const controls = document.createElement('div');
  controls.className = 'pdf-controls mt-3';
  controls.innerHTML = `
    <div class="btn-group" role="group" aria-label="Controles de PDF">
      <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(0.5)" title="Zoom Out">
        <i class="fas fa-search-minus"></i> Zoom Out
      </button>
      <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.0)" title="Zoom Normal">
        <i class="fas fa-search"></i> 100%
      </button>
      <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.5)" title="Zoom In">
        <i class="fas fa-search-plus"></i> Zoom In
      </button>
    </div>
  `;
  
  container.appendChild(controls);
  
  // Agregar funciones de zoom al objeto window
  window.zoomPDF = function(scale) {
    if (canvas) {
      canvas.style.width = (canvas.width * scale) + 'px';
      canvas.style.height = 'auto';
      console.log(`[PDF-FINAL] 🔧 Zoom aplicado: ${scale * 100}%`);
    }
  };
}

// Exportar funciones adicionales
window.showMarkdownInModal = showMarkdownInModal;
window.showTextInModal = showTextInModal;
window.showDocumentModal = showDocumentModal;

console.log(
  "[MODAL-FINAL] ✅ Todas las funciones de modal cargadas correctamente - VERSION: 2025-01-03-15:30"
);
