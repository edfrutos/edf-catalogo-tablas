// Funciones de modal para compatibilidad con pywebview - VERSIÓN FINAL
// Este archivo define las funciones que faltan en el contexto de pywebview

// Detectar si estamos en pywebview (evitando conflicto de nombres)
const modalIsPyWebView = typeof pywebview !== "undefined";
console.log("[MODAL-FINAL] Detección de pywebview:", {
  modalIsPyWebView,
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

  // SOLUCIÓN UNIFICADA: Todos los archivos se ven en modal
  let isLocalFile = false;
  let localUrl = pdfUrl;
  
  if (pdfUrl.includes('s3.') || pdfUrl.includes('amazonaws.com')) {
    // Es un archivo S3 - usar URL directa
    console.log("[PDF-FINAL] 🔍 Archivo S3 detectado:", pdfUrl);
    isLocalFile = false;
    localUrl = pdfUrl; // Mantener URL S3 para PDF.js
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
    // URL externa - usar URL directa
    console.log("[PDF-FINAL] 🔍 URL externa detectada:", pdfUrl);
    isLocalFile = false;
    localUrl = pdfUrl; // Mantener URL externa para PDF.js
  }

  console.log("[PDF-FINAL] 🔧 URL local del PDF:", localUrl);

  // Configurar título del modal (si existe)
  if (modalTitle) {
    modalTitle.textContent = pdfTitle || "Documento PDF";
    console.log("[PDF-FINAL] ✅ Título del modal configurado");
  } else {
    console.log("[PDF-FINAL] ⚠️ Título del modal no disponible, continuando sin título");
  }

  // SOLUCIÓN UNIFICADA: Manejar S3 y locales de forma diferente
  if (isLocalFile) {
    // Para archivos locales, usar PDF.js
    modalContent.innerHTML = `
        <div class="text-center p-4">
            <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
            <h5>Documento PDF</h5>
            <p class="text-muted mb-4">
                <strong>Archivo:</strong> ${pdfTitle || "PDF"}<br>
                <strong>Tipo:</strong> PDF<br>
                <strong>Ubicación:</strong> Local
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
  } else {
    // Para archivos S3, usar PDF.js con descarga temporal
    modalContent.innerHTML = `
        <div class="text-center p-4">
            <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
            <h5>Documento PDF</h5>
            <p class="text-muted mb-4">
                <strong>Archivo:</strong> ${pdfTitle || "PDF"}<br>
                <strong>Tipo:</strong> PDF<br>
                <strong>Ubicación:</strong> S3
            </p>
            
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                <strong>Archivo S3 detectado</strong><br>
                Descargando PDF para previsualización...
            </div>
            
            <div id="pdf-viewer-container" class="mt-4">
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Descargando PDF...</span>
                    </div>
                    <p class="mt-2">Descargando PDF desde S3...</p>
                </div>
            </div>
            
            <div class="btn-group mt-3" role="group">
                <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${pdfUrl}')">
                    <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
                </button>
                <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${pdfUrl}', '${pdfTitle}')">
                    <i class="fas fa-download"></i> Descargar
                </button>
            </div>
        </div>
    `;
    
    console.log("[PDF-FINAL] ✅ PDF S3 - iniciando descarga para previsualización");
    
    // MOSTRAR EL MODAL ANTES de cargar el PDF
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    console.log("[PDF-FINAL] 🔍 Modal S3 mostrado, iniciando carga de PDF...");
    
    // Descargar PDF de S3 y mostrarlo con PDF.js
    console.log("[PDF-FINAL] 🔍 Llamando a loadS3PDFWithJS...");
    loadS3PDFWithJS(pdfUrl, modalContent, pdfTitle);
    
    // Verificar que el modal siga abierto después de un breve delay
    setTimeout(() => {
      console.log("[PDF-FINAL] 🔍 Verificando modal después de 1 segundo...");
      const isVisible = modalElement.classList.contains('show');
      console.log("[PDF-FINAL] 🔍 Modal visible:", isVisible);
      if (!isVisible) {
        console.log("[PDF-FINAL] ⚠️ Modal se cerró, reabriendo...");
        modal.show();
      }
    }, 1000);
    
    return; // Salir aquí para archivos S3
  }

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
  
  // ✅ PDF.js se está cargando y renderizando automáticamente
  console.log("[PDF-FINAL] 🚀 PDF.js iniciado automáticamente");
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
              <head><title>PDF - ${fileName || 'Documento'}</title></head>
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

// Función para descargar archivos S3 usando el proxy
function downloadS3File(fileUrl, fileName) {
  console.log("[DOWNLOAD-FINAL] 🎯 Descargando archivo S3:", fileUrl);
  
  try {
    // Convertir URL S3 a proxy para evitar CORS
    const proxyUrl = fileUrl.replace(
      'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
      '/admin/s3/'
    );
    
    console.log("[DOWNLOAD-FINAL] 🔧 URL convertida a proxy:", proxyUrl);
    
    // Crear enlace temporal y hacer clic
    const link = document.createElement('a');
    link.href = proxyUrl;
    link.download = fileName || 'documento.pdf';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log("[DOWNLOAD-FINAL] ✅ Descarga iniciada para archivo S3");
    
  } catch (error) {
    console.error("[DOWNLOAD-FINAL] ❌ Error descargando archivo S3:", error);
    alert('Error al descargar el archivo: ' + error.message);
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

// Función para mostrar Markdown en modal PERFECTA
function showMarkdownInModal(markdownUrl, markdownTitle) {
  console.log(
    "[MARKDOWN-PERFECT] 🎯 Usuario solicitó ver Markdown en modal:",
    markdownUrl
  );

  // Usar modal Bootstrap con IDs CORRECTOS
  const modalElement = document.getElementById("documentModal");
  const modalContent = document.getElementById("documentContent");
  const modalTitle = document.getElementById("documentModalLabel");

  if (!modalElement || !modalContent || !modalTitle) {
    console.error(
      "[MARKDOWN-PERFECT] ❌ Elementos del modal Bootstrap no encontrados:", {
        modalElement: !!modalElement,
        modalContent: !!modalContent,
        modalTitle: !!modalTitle
      }
    );
    alert("Error: Modal no disponible");
    return;
  }

  // Configurar título del modal
  modalTitle.textContent = markdownTitle || "Documento Markdown";

  // Mostrar loading profesional
  modalContent.innerHTML = `
    <div class="text-center p-4">
      <div class="spinner-border text-primary mb-3" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <h5>Preparando Documento Markdown</h5>
      <p class="text-muted">Cargando y renderizando contenido...</p>
      <div class="progress mb-3">
        <div class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" style="width: 0%"></div>
      </div>
    </div>
  `;

  // Mostrar el modal primero
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // DETECCIÓN HÍBRIDA S3/LOCAL
  const isS3File = markdownUrl.includes('s3.amazonaws.com') || markdownUrl.includes('edf-catalogo-tablas.s3');
  let fetchUrl = markdownUrl;

  if (isS3File) {
    // Archivo S3 - usar proxy backend
    fetchUrl = markdownUrl.replace(
      'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
      '/admin/s3/'
    );
    console.log("[MARKDOWN-PERFECT] 🔧 Archivo S3 detectado, usando proxy:", fetchUrl);
  } else if (markdownUrl.startsWith("/uploads/")) {
    // Archivo local - convertir a ruta static
    fetchUrl = `/static/uploads/documents/${markdownUrl.split("/").pop()}`;
    console.log("[MARKDOWN-PERFECT] 🔧 Archivo local detectado, ruta convertida:", fetchUrl);
  }

  // Cargar Markdown con fetch robusto
  fetch(fetchUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.text();
    })
    .then((markdownText) => {
      console.log(
        "[MARKDOWN-PERFECT] ✅ Contenido Markdown cargado, longitud:",
        markdownText.length
      );

      // RENDERIZADO PROFESIONAL CON MARKED.JS
      renderMarkdownWithLibrary(markdownText, modalContent, markdownTitle, markdownUrl, isS3File);
    })
    .catch((error) => {
      console.error("[MARKDOWN-PERFECT] ❌ Error cargando Markdown:", error);
      
      // Mostrar error con opciones de fallback
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
          <h5>Error al cargar el archivo</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${markdownTitle || "Markdown"}<br>
            <strong>Error:</strong> ${error.message}
          </p>
          
          <div class="alert alert-warning">
            <i class="fas fa-info-circle"></i>
            <strong>Opciones disponibles:</strong>
          </div>
          
          <div class="btn-group mt-3" role="group">
            <a href="${markdownUrl}" target="_blank" class="btn btn-primary">
              <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
            </a>
            <button type="button" class="btn btn-outline-primary" onclick="downloadMarkdownFile('${markdownUrl}', '${markdownTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>
          </div>
        </div>
      `;
    });
}

// Función para renderizar Markdown con marked.js PROFESIONAL
function renderMarkdownWithLibrary(markdownText, modalContent, markdownTitle, originalUrl, isS3File) {
  console.log("[MARKDOWN-PERFECT] 🚀 Iniciando renderizado profesional con marked.js");
  
  // Cargar marked.js si no está disponible
  if (typeof marked === 'undefined') {
    console.log("[MARKDOWN-PERFECT] 📥 marked.js no disponible, cargando desde CDN...");
    
    const markedScript = document.createElement('script');
    markedScript.src = 'https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js';
    markedScript.onload = function() {
      console.log("[MARKDOWN-PERFECT] ✅ marked.js cargado desde CDN");
      renderMarkdownContent(markdownText, modalContent, markdownTitle, originalUrl, isS3File);
    };
    
    document.head.appendChild(markedScript);
  } else {
    console.log("[MARKDOWN-PERFECT] ✅ marked.js ya disponible");
    renderMarkdownContent(markdownText, modalContent, markdownTitle, originalUrl, isS3File);
  }
}

// Función para renderizar el contenido Markdown
function renderMarkdownContent(markdownText, modalContent, markdownTitle, originalUrl, isS3File) {
  try {
    // Configurar marked.js para máxima calidad
    marked.setOptions({
      breaks: true,           // Permitir saltos de línea
      gfm: true,              // GitHub Flavored Markdown
      headerIds: true,        // IDs en headers para navegación
      mangle: false,          // No manglear IDs
      sanitize: false,        // Permitir HTML (para flexibilidad)
      smartLists: true,       // Listas inteligentes
      smartypants: true,      // Tipografía inteligente
      xhtml: false            // No forzar XHTML
    });
    
    // Renderizar Markdown a HTML
    const htmlContent = marked.parse(markdownText);
    
    console.log("[MARKDOWN-PERFECT] ✅ Markdown renderizado exitosamente");
    
    // Configurar contenido del modal con UI moderna
    modalContent.innerHTML = `
      <div class="text-center p-4">
        <i class="fas fa-file-code fa-4x text-info mb-3"></i>
        <h5>Documento Markdown</h5>
        <p class="text-muted mb-4">
          <strong>Archivo:</strong> ${markdownTitle || "Markdown"}<br>
          <strong>Tipo:</strong> Markdown<br>
          <strong>Ubicación:</strong> ${isS3File ? 'S3' : 'Local'}
        </p>
        
        <div class="markdown-controls mb-3">
          <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-secondary" onclick="toggleMarkdownTheme()">
              <i class="fas fa-palette"></i> Tema
            </button>
            <button type="button" class="btn btn-outline-secondary" onclick="toggleMarkdownFontSize()">
              <i class="fas fa-text-height"></i> Tamaño
            </button>
            <button type="button" class="btn btn-outline-secondary" onclick="toggleMarkdownLineNumbers()">
              <i class="fas fa-list-ol"></i> Líneas
            </button>
          </div>
        </div>
        
        <div class="markdown-content-wrapper" style="max-height: 60vh; overflow-y: auto; padding: 20px; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; text-align: left; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <div class="markdown-rendered" id="markdown-content">
            ${htmlContent}
          </div>
        </div>
        
        <div class="btn-group mt-3" role="group">
          <a href="${originalUrl}" target="_blank" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
          </a>
          <button type="button" class="btn btn-outline-primary" onclick="downloadMarkdownFile('${originalUrl}', '${markdownTitle}')">
            <i class="fas fa-download"></i> Descargar
          </button>
          <button type="button" class="btn btn-outline-info" onclick="exportMarkdownToPDF('${markdownTitle}')">
            <i class="fas fa-file-pdf"></i> Exportar PDF
          </button>
        </div>
      </div>
    `;
    
    // Aplicar estilos CSS personalizados para Markdown
    applyMarkdownStyles();
    
    console.log("[MARKDOWN-PERFECT] ✅ Modal de Markdown configurado profesionalmente");
    
  } catch (error) {
    console.error("[MARKDOWN-PERFECT] ❌ Error renderizando Markdown:", error);
    
    // Fallback a renderizado básico
    modalContent.innerHTML = `
      <div class="text-center p-4">
        <i class="fas fa-exclamation-triangle fa-4x text-warning mb-3"></i>
        <h5>Renderizado Básico</h5>
        <p class="text-muted mb-4">
          <strong>Archivo:</strong> ${markdownTitle || "Markdown"}<br>
          <strong>Error:</strong> ${error.message}<br>
          <em>Usando renderizado básico como fallback</em>
        </p>
        
        <div class="markdown-content-wrapper" style="max-height: 60vh; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left; margin-bottom: 20px;">
          <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace;">${markdownText}</pre>
        </div>
        
        <div class="btn-group mt-3" role="group">
          <a href="${originalUrl}" target="_blank" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
          </a>
          <button type="button" class="btn btn-outline-primary" onclick="downloadMarkdownFile('${originalUrl}', '${markdownTitle}')">
            <i class="fas fa-download"></i> Descargar
          </button>
        </div>
      </div>
    `;
  }
}

// Función para aplicar estilos CSS personalizados para Markdown
function applyMarkdownStyles() {
  const markdownContent = document.getElementById('markdown-content');
  if (!markdownContent) return;
  
  // Agregar estilos CSS personalizados
  const style = document.createElement('style');
  style.textContent = `
    #markdown-content {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #333;
    }
    
    #markdown-content h1, #markdown-content h2, #markdown-content h3,
    #markdown-content h4, #markdown-content h5, #markdown-content h6 {
      margin-top: 1.5em;
      margin-bottom: 0.5em;
      font-weight: 600;
      line-height: 1.25;
    }
    
    #markdown-content h1 { font-size: 2em; border-bottom: 2px solid #eaecef; padding-bottom: 0.3em; }
    #markdown-content h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
    #markdown-content h3 { font-size: 1.25em; }
    
    #markdown-content p { margin-bottom: 1em; }
    
    #markdown-content ul, #markdown-content ol {
      margin-bottom: 1em;
      padding-left: 2em;
    }
    
    #markdown-content li { margin-bottom: 0.5em; }
    
    #markdown-content blockquote {
      margin: 1em 0;
      padding: 0 1em;
      color: #6a737d;
      border-left: 4px solid #dfe2e5;
      background-color: #f6f8fa;
    }
    
    #markdown-content code {
      background-color: #f6f8fa;
      padding: 0.2em 0.4em;
      border-radius: 3px;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.9em;
    }
    
    #markdown-content pre {
      background-color: #f6f8fa;
      padding: 1em;
      border-radius: 6px;
      overflow-x: auto;
      border: 1px solid #e1e4e8;
    }
    
    #markdown-content pre code {
      background-color: transparent;
      padding: 0;
      border-radius: 0;
    }
    
    #markdown-content table {
      border-collapse: collapse;
      width: 100%;
      margin: 1em 0;
    }
    
    #markdown-content th, #markdown-content td {
      border: 1px solid #dfe2e5;
      padding: 0.5em;
      text-align: left;
    }
    
    #markdown-content th {
      background-color: #f6f8fa;
      font-weight: 600;
    }
    
    #markdown-content img {
      max-width: 100%;
      height: auto;
      border-radius: 6px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    #markdown-content hr {
      border: none;
      border-top: 1px solid #eaecef;
      margin: 2em 0;
    }
  `;
  
  document.head.appendChild(style);
  console.log("[MARKDOWN-PERFECT] ✅ Estilos CSS aplicados");
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
      // Archivo S3 - usar modal con PDF.js
      console.log('[MODAL-FINAL] Archivo S3 - abriendo en modal con PDF.js');
      showPDFInModal(documentSrc, documentTitle);
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
      // Archivo S3 - usar modal con Markdown
      console.log('[MODAL-FINAL] Archivo S3 - abriendo en modal con Markdown');
      showMarkdownInModal(documentSrc, documentTitle);
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
      // Archivo S3 - usar modal con texto
      console.log('[MODAL-FINAL] Archivo S3 - abriendo en modal con texto');
      showTextInModal(documentSrc, documentTitle);
    }
  } else {
    // Otros tipos de archivo - usar modal genérico
    console.log('[MODAL-FINAL] Tipo de archivo no soportado - abriendo en modal genérico');
    showDocumentModal(documentSrc, documentTitle);
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
  
  // SOLUCIÓN HÍBRIDA: Manejar S3 y archivos locales
  if (pdfUrl.includes('s3.') || pdfUrl.includes('amazonaws.com')) {
    console.log("[PDF-FINAL] 🔍 Archivo S3 detectado, usando método alternativo");
    
    // Para S3, usar iframe como fallback
    const container = canvas.parentElement;
    container.innerHTML = `
      <div class="text-center p-4">
        <div class="alert alert-info">
          <i class="fas fa-info-circle"></i>
          <strong>Archivo S3 detectado</strong><br>
          El PDF se mostrará usando el visor del navegador
        </div>
        <iframe src="${pdfUrl}" width="100%" height="600" style="border: 2px solid #007bff; border-radius: 8px;">
          <p>Tu navegador no soporta iframes. <a href="${pdfUrl}" target="_blank">Abrir PDF</a></p>
        </iframe>
        <div class="mt-3">
          <a href="${pdfUrl}" target="_blank" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
          </a>
          <button type="button" class="btn btn-outline-primary" onclick="downloadLocalFile('${pdfUrl}', '${pdfTitle}')">
            <i class="fas fa-download"></i> Descargar
          </button>
        </div>
      </div>
    `;
    
    console.log("[PDF-FINAL] ✅ PDF S3 mostrado con iframe");
    return;
  }
  
  // Para archivos locales, usar PDF.js
  console.log("[PDF-FINAL] 🔍 Archivo local, usando PDF.js");
  
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
      
      // Guardar PDF en variable global para navegación
      window.currentPDF = pdf;
      
      // Renderizar primera página
      return renderPage(pdf, 1, canvas, canvas.parentElement);
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

// Función para renderizar una página específica
function renderPage(pdf, pageNumber, canvas, container) {
  console.log(`[PDF-FINAL] 🔄 Renderizando página ${pageNumber} de ${pdf.numPages}`);
  
  return pdf.getPage(pageNumber).then(function (page) {
    console.log(`[PDF-FINAL] ✅ Página ${pageNumber} obtenida`);
    
    // Configurar viewport con CALIDAD MÁXIMA
    const viewport = page.getViewport({scale: 2.0}); // Escala DOBLE para máxima nitidez
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    
    console.log(`[PDF-FINAL] 🔧 Canvas configurado - Ancho: ${canvas.width}, Alto: ${canvas.height}`);
    
    // Forzar visibilidad del canvas
    canvas.style.display = 'block';
    canvas.style.visibility = 'visible';
    canvas.style.opacity = '1';
    
    // Configurar canvas para CALIDAD MÁXIMA
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    
    // Configurar canvas para alta resolución
    const devicePixelRatio = window.devicePixelRatio || 1;
    canvas.style.width = (viewport.width / devicePixelRatio) + 'px';
    canvas.style.height = (viewport.height / devicePixelRatio) + 'px';
    
    // CENTRAR el PDF en el modal
    canvas.style.margin = '0 auto';
    canvas.style.display = 'block';
    canvas.style.maxWidth = '100%';
    canvas.style.height = 'auto';
    
    // Renderizar página con CALIDAD MÁXIMA
    const renderContext = {
      canvasContext: ctx,
      viewport: viewport,
      enableWebGL: true,
      renderInteractiveForms: true
    };
    
    return page.render(renderContext).promise;
  }).then(function () {
    console.log(`[PDF-FINAL] ✅ Página ${pageNumber} renderizada exitosamente`);
    
    // Verificar que el canvas esté visible
    console.log(`[PDF-FINAL] 🔍 Verificando canvas - Display: ${canvas.style.display}, Visibility: ${canvas.style.visibility}, Opacity: ${canvas.style.opacity}`);
    console.log(`[PDF-FINAL] 🔍 Canvas en DOM: ${document.contains(canvas)}`);
    console.log(`[PDF-FINAL] 🔍 Canvas parent: ${canvas.parentElement ? '✅' : '❌'}`);
    
    // Actualizar controles con la página actual
    const controlsContainer = container.querySelector('.pdf-controls');
    if (controlsContainer) {
      controlsContainer.remove(); // Remover controles antiguos
    }
    
    // Agregar controles actualizados
    addPDFControls(canvas, pdf, pageNumber);
    
    // Actualizar mensaje de estado
    const alertElement = container.parentElement.querySelector(".alert");
    if (alertElement) {
      alertElement.className = "alert alert-success";
      alertElement.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <strong>¡Éxito!</strong> Página ${pageNumber} de ${pdf.numPages} visible en modal
      `;
    }
  }).catch(function (error) {
    console.error(`[PDF-FINAL] ❌ Error renderizando página ${pageNumber}:`, error);
  });
}

// Función para agregar controles de zoom y navegación
function addPDFControls(canvas, pdf, currentPage = 1) {
  console.log("[PDF-FINAL] 🔧 Agregando controles completos...");
  
  if (!canvas || !canvas.parentElement) {
    console.log("[PDF-FINAL] ⚠️ Canvas o parent no disponible, saltando controles");
    return;
  }
  
  const container = canvas.parentElement;
  
  // Crear controles completos
  const controls = document.createElement('div');
  controls.className = 'pdf-controls mt-3';
  controls.innerHTML = `
    <div class="row">
      <div class="col-md-6">
        <div class="btn-group" role="group" aria-label="Navegación de páginas">
          <button type="button" class="btn btn-outline-secondary btn-sm" onclick="changePage(-1)" title="Página anterior" ${currentPage <= 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> Anterior
          </button>
          <span class="btn btn-outline-info btn-sm disabled">
            Página ${currentPage} de ${pdf.numPages}
          </span>
          <button type="button" class="btn btn-outline-secondary btn-sm" onclick="changePage(1)" title="Página siguiente" ${currentPage >= pdf.numPages ? 'disabled' : ''}>
            Siguiente <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
      <div class="col-md-6">
        <div class="btn-group" role="group" aria-label="Controles de PDF">
          <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(0.5)" title="Zoom Out">
            <i class="fas fa-search-minus"></i> 50%
          </button>
          <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.0)" title="Zoom Normal">
            <i class="fas fa-search"></i> 100%
          </button>
          <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(1.5)" title="Zoom In">
            <i class="fas fa-search-plus"></i> 150%
          </button>
          <button type="button" class="btn btn-outline-primary btn-sm" onclick="zoomPDF(2.0)" title="Zoom Doble">
            <i class="fas fa-expand"></i> 200%
          </button>
        </div>
      </div>
    </div>
    <div class="row mt-2">
      <div class="col-12 text-center">
        <div class="btn-group" role="group" aria-label="Herramientas adicionales">
          <button type="button" class="btn btn-outline-info btn-sm" onclick="fitToWidth()" title="Ajustar al ancho">
            <i class="fas fa-arrows-alt-h"></i> Ajustar
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" onclick="rotatePDF(-90)" title="Rotar izquierda">
            <i class="fas fa-undo"></i> Rotar
          </button>
          <button type="button" class="btn btn-outline-success btn-sm" onclick="printPDF()" title="Imprimir PDF">
            <i class="fas fa-print"></i> Imprimir
          </button>
        </div>
      </div>
    </div>
  `;
  
  try {
    container.appendChild(controls);
    console.log("[PDF-FINAL] ✅ Controles completos agregados exitosamente");
    
    // Agregar funciones de control al objeto window
    window.zoomPDF = function(scale) {
      if (canvas) {
        canvas.style.width = (canvas.width * scale) + 'px';
        canvas.style.height = 'auto';
        console.log(`[PDF-FINAL] 🔧 Zoom aplicado: ${scale * 100}%`);
      }
    };
    
    window.changePage = function(direction) {
      const newPage = currentPage + direction;
      if (newPage >= 1 && newPage <= pdf.numPages) {
        renderPage(pdf, newPage, canvas, container);
      }
    };
    
    window.fitToWidth = function() {
      if (canvas) {
        canvas.style.width = '100%';
        canvas.style.height = 'auto';
        console.log(`[PDF-FINAL] 🔧 Ajustado al ancho del contenedor`);
      }
    };
    
    window.rotatePDF = function(degrees) {
      if (canvas) {
        const currentRotation = parseInt(canvas.style.transform.replace('rotate(', '').replace('deg)', '') || 0);
        const newRotation = currentRotation + degrees;
        canvas.style.transform = `rotate(${newRotation}deg)`;
        console.log(`[PDF-FINAL] 🔧 Rotación aplicada: ${newRotation}°`);
      }
    };
    
    window.printPDF = function() {
      console.log("[PDF-FINAL] 🔧 Función de impresión iniciada");
      
      // Verificar que tenemos el PDF cargado
      if (typeof currentPDF === 'undefined' || !currentPDF) {
        console.log("[PDF-FINAL] ⚠️ PDF no disponible para impresión");
        alert('PDF no disponible para impresión. Intenta de nuevo.');
        return;
      }
      
      // Mostrar indicador de progreso en el modal
      const modalContent = document.getElementById('documentContent');
      const originalContent = modalContent.innerHTML;
      
      modalContent.innerHTML = `
        <div class="text-center p-4">
          <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">Preparando impresión...</span>
          </div>
          <h5>Preparando Impresión</h5>
          <p class="text-muted">Renderizando todas las páginas del PDF...</p>
          <div class="progress mb-3">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%"></div>
          </div>
        </div>
      `;
      
              // Función para renderizar todas las páginas
        const renderAllPages = async () => {
          const totalPages = currentPDF.numPages;
          console.log(`[PDF-FINAL] 🔧 Renderizando ${totalPages} páginas para impresión`);
          
          // NO crear ventana aún - solo preparar el contenido
          let allPagesHTML = '';
          
          for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
            try {
              // Actualizar progreso
              const progress = Math.round((pageNum / totalPages) * 100);
              const progressBar = modalContent.querySelector('.progress-bar');
              if (progressBar) {
                progressBar.style.width = progress + '%';
                progressBar.textContent = `${progress}%`;
              }
              
              const page = await currentPDF.getPage(pageNum);
              const viewport = page.getViewport({ scale: 1.5 });
              
              // Crear canvas temporal para esta página
              const tempCanvas = document.createElement('canvas');
              const tempCtx = tempCanvas.getContext('2d');
              tempCanvas.width = viewport.width;
              tempCanvas.height = viewport.height;
              
              // Renderizar página
              await page.render({
                canvasContext: tempCtx,
                viewport: viewport
              }).promise;
              
              // Agregar página al HTML
              allPagesHTML += `
                <div class="page">
                  <div class="page-number">Página ${pageNum} de ${totalPages}</div>
                  <img src="${tempCanvas.toDataURL()}" alt="Página ${pageNum}">
                </div>
              `;
              
              console.log(`[PDF-FINAL] ✅ Página ${pageNum} renderizada para impresión`);
              
            } catch (error) {
              console.error(`[PDF-FINAL] ❌ Error renderizando página ${pageNum}:`, error);
            }
          }
          
          // NO restaurar el modal aún - mantener el PDF visible
          console.log("[PDF-FINAL] 🔧 Creando ventana de impresión con contenido completo...");
          
          const printWindow = window.open('', '_blank', 'width=800,height=600');
          printWindow.document.write(`
            <html>
              <head>
                <title>PDF - Documento Completo</title>
                <style>
                  body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
                  .page { page-break-after: always; margin-bottom: 20px; }
                  .page:last-child { page-break-after: avoid; }
                  img { max-width: 100%; height: auto; display: block; }
                  .page-number { text-align: center; margin: 10px 0; font-size: 12px; color: #666; }
                </style>
              </head>
              <body>
                ${allPagesHTML}
              </body>
            </html>
          `);
          
          // Cerrar documento
          printWindow.document.close();
          
          // Esperar a que se renderice todo y luego imprimir
          setTimeout(() => {
            try {
              // Verificar que todas las imágenes estén cargadas
              const images = printWindow.document.querySelectorAll('img');
              let loadedImages = 0;
              const totalImages = images.length;
              
              console.log(`[PDF-FINAL] 🔧 Verificando ${totalImages} imágenes...`);
              
              if (totalImages === 0) {
                console.log("[PDF-FINAL] ⚠️ No hay imágenes para verificar");
                attemptPrint(printWindow);
                return;
              }
              
              // Función para verificar carga de imágenes
              const checkImageLoad = () => {
                loadedImages++;
                console.log(`[PDF-FINAL] ✅ Imagen ${loadedImages}/${totalImages} cargada`);
                
                if (loadedImages === totalImages) {
                  console.log("[PDF-FINAL] ✅ Todas las imágenes cargadas, iniciando impresión...");
                  attemptPrint(printWindow);
                }
              };
              
              // Verificar cada imagen
              images.forEach((img, index) => {
                if (img.complete && img.naturalHeight !== 0) {
                  console.log(`[PDF-FINAL] ✅ Imagen ${index + 1} ya cargada`);
                  loadedImages++;
                  if (loadedImages === totalImages) {
                    console.log("[PDF-FINAL] ✅ Todas las imágenes ya cargadas, iniciando impresión...");
                    attemptPrint(printWindow);
                  }
                } else {
                  img.onload = () => {
                    console.log(`[PDF-FINAL] ✅ Imagen ${index + 1} cargada onload`);
                    checkImageLoad();
                  };
                  img.onerror = () => {
                    console.log(`[PDF-FINAL] ⚠️ Error cargando imagen ${index + 1}`);
                    checkImageLoad();
                  };
                }
              });
              
            } catch (error) {
              console.error("[PDF-FINAL] ❌ Error verificando imágenes:", error);
              // Fallback: intentar imprimir de todas formas
              attemptPrint(printWindow);
            }
          }, 1000);
          
          // Función para intentar imprimir
          function attemptPrint(printWindow) {
            try {
              console.log("[PDF-FINAL] 🔧 Iniciando impresión...");
              
              // Usar eval para ejecutar window.print() en la ventana de impresión
              printWindow.eval(`
                console.log('Ejecutando impresión desde la ventana de impresión...');
                window.print();
              `);
              
              console.log("[PDF-FINAL] ✅ Impresión iniciada via eval");
              
              // Restaurar el modal DESPUÉS de iniciar la impresión
              setTimeout(() => {
                console.log("[PDF-FINAL] 🔧 Restaurando modal después de impresión...");
                
                // Restaurar el contenido original
                modalContent.innerHTML = originalContent;
                
                // Re-renderizar el PDF en el modal restaurado
                const restoredCanvas = modalContent.querySelector('#pdf-canvas');
                if (restoredCanvas && currentPDF) {
                  console.log("[PDF-FINAL] 🔧 Re-renderizando PDF en modal restaurado...");
                  renderPage(currentPDF, 1, restoredCanvas, modalContent);
                }
                
              }, 2000); // Esperar 2 segundos para que se complete la impresión
              
            } catch (error) {
              console.error("[PDF-FINAL] ❌ Error en impresión:", error);
              
              // Fallback: intentar imprimir desde la ventana principal
              try {
                console.log("[PDF-FINAL] 🔧 Intentando fallback...");
                printWindow.focus();
                printWindow.print();
                console.log("[PDF-FINAL] ✅ Impresión iniciada via fallback");
                
                // Restaurar el modal también en el fallback
                setTimeout(() => {
                  console.log("[PDF-FINAL] 🔧 Restaurando modal después de fallback...");
                  
                  // Restaurar el contenido original
                  modalContent.innerHTML = originalContent;
                  
                  // Re-renderizar el PDF en el modal restaurado
                  const restoredCanvas = modalContent.querySelector('#pdf-canvas');
                  if (restoredCanvas && currentPDF) {
                    console.log("[PDF-FINAL] 🔧 Re-renderizando PDF en modal restaurado...");
                    renderPage(currentPDF, 1, restoredCanvas, modalContent);
                  }
                  
                }, 2000);
                
              } catch (fallbackError) {
                console.error("[PDF-FINAL] ❌ Fallback también falló:", fallbackError);
                // Mostrar mensaje al usuario
                alert('Impresión iniciada. Si no se abre la ventana de impresora, ve a la pestaña de impresión y presiona Ctrl+P.');
                
                // Restaurar el modal en caso de error también
                setTimeout(() => {
                  console.log("[PDF-FINAL] 🔧 Restaurando modal después de error...");
                  
                  // Restaurar el contenido original
                  modalContent.innerHTML = originalContent;
                  
                  // Re-renderizar el PDF en el modal restaurado
                  const restoredCanvas = modalContent.querySelector('#pdf-canvas');
                  if (restoredCanvas && currentPDF) {
                    console.log("[PDF-FINAL] 🔧 Re-renderizando PDF en modal restaurado...");
                    renderPage(currentPDF, 1, restoredCanvas, modalContent);
                  }
                  
                }, 2000);
              }
            }
          }
        };
      
      // Iniciar renderizado
      renderAllPages();
    };
    
  } catch (error) {
    console.log("[PDF-FINAL] ⚠️ Error agregando controles:", error.message);
  }
}

// Función para cargar PDF de S3 y mostrarlo con PDF.js
function loadS3PDFWithJS(s3Url, modalContent, pdfTitle) {
  console.log("[PDF-FINAL] 🚀 Iniciando descarga de PDF desde S3:", s3Url);
  
  // Crear canvas para el PDF
  const container = modalContent.querySelector('#pdf-viewer-container');
  const canvas = document.createElement('canvas');
  canvas.id = 'pdf-canvas';
  canvas.style.cssText = 'width: 100%; height: 600px; border: 2px solid #007bff; border-radius: 8px; background-color: #ffffff;';
  
  // Limpiar contenedor y agregar canvas
  container.innerHTML = '';
  container.appendChild(canvas);
  
  // Cargar PDF.js si no está disponible
  if (typeof pdfjsLib === 'undefined') {
    console.log("[PDF-FINAL] 📥 PDF.js no disponible, cargando desde CDN...");
    
    const pdfScript = document.createElement('script');
    pdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
    pdfScript.onload = function() {
      console.log("[PDF-FINAL] ✅ PDF.js cargado desde CDN");
      
      if (pdfjsLib.GlobalWorkerOptions) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        console.log("[PDF-FINAL] 🔧 Worker de PDF.js configurado");
      }
      
      // Ahora renderizar el PDF
      renderS3PDF(s3Url, canvas, modalContent, pdfTitle, container);
    };
    
    document.head.appendChild(pdfScript);
  } else {
    console.log("[PDF-FINAL] ✅ PDF.js ya disponible");
    renderS3PDF(s3Url, canvas, modalContent, pdfTitle, container);
  }
}

// Función para renderizar PDF de S3
function renderS3PDF(s3Url, canvas, modalContent, pdfTitle, container) {
  console.log("[PDF-FINAL] 🎨 Iniciando renderizado de PDF desde S3:", s3Url);
  
  // Configurar canvas
  const ctx = canvas.getContext('2d');
  canvas.style.display = 'block';
  
           // SOLUCIÓN CORS: Usar proxy backend para evitar CORS
         // Convertir URL S3 a ruta proxy local
         const proxyUrl = s3Url.replace(
           'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
           '/admin/s3/'
         );
         
         console.log("[PDF-FINAL] 🔧 URL S3 convertida a proxy:", proxyUrl);
         
         fetch(proxyUrl, {
           method: 'GET',
           headers: {
             'Accept': 'application/pdf'
           }
         })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    console.log("[PDF-FINAL] ✅ Fetch exitoso desde S3, convirtiendo a arrayBuffer");
    return response.arrayBuffer();
  })
  .then(arrayBuffer => {
    console.log("[PDF-FINAL] ✅ ArrayBuffer creado desde S3, tamaño:", arrayBuffer.byteLength);
    
    // Cargar PDF desde arrayBuffer
    return pdfjsLib.getDocument({data: arrayBuffer}).promise;
  })
  .then(function (pdf) {
    console.log("[PDF-FINAL] ✅ PDF de S3 cargado, páginas:", pdf.numPages);
    
    // Guardar PDF en variable global para navegación
    window.currentPDF = pdf;
    
    // Renderizar primera página
    return renderPage(pdf, 1, canvas, canvas.parentElement);
  })
  .catch(function (error) {
    console.error("[PDF-FINAL] ❌ Error cargando PDF desde S3:", error);
    
    // INTENTAR FALLBACK ROBUSTO para PDFs problemáticos
    console.log("[PDF-FINAL] 🔧 Intentando fallback para PDF problemático...");
    
    try {
      // Mostrar opciones de fallback mejoradas
      container.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-exclamation-triangle fa-4x text-warning mb-3"></i>
          <h5>PDF Requiere Fallback</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${pdfTitle || 'PDF'}<br>
            <strong>Error:</strong> ${error.message}<br>
            <strong>URL S3:</strong> ${s3Url}
          </p>
          
          <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <strong>El PDF se descargó correctamente pero PDF.js no puede procesarlo.</strong><br>
            <em>Usando método alternativo para visualización...</em>
          </div>
          
          <div class="btn-group mt-3" role="group">
            <button type="button" class="btn btn-primary" onclick="openPDFInNewTab('${s3Url}')">
              <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
            </button>
            <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${s3Url}', '${pdfTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>
            <button type="button" class="btn btn-outline-info" onclick="retryPDFLoad('${s3Url}', '${pdfTitle}', container)">
              <i class="fas fa-redo"></i> Reintentar
            </button>
          </div>
        </div>
      `;
      
      console.log("[PDF-FINAL] ✅ Fallback configurado para PDF problemático");
      
    } catch (fallbackError) {
      console.error("[PDF-FINAL] ❌ Error en fallback:", fallbackError);
      
      // Fallback final: solo mostrar error básico
      container.innerHTML = `
        <div class="text-center p-4">
          <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
          <h5>Error Fatal del PDF</h5>
          <p class="text-muted mb-4">
            <strong>Archivo:</strong> ${pdfTitle || 'PDF'}<br>
            <strong>Error:</strong> ${error.message}
          </p>
          
          <div class="btn-group mt-3" role="group">
            <a href="${s3Url}" target="_blank" class="btn btn-primary">
              <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
            </a>
            <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${s3Url}', '${pdfTitle}')">
              <i class="fas fa-download"></i> Descargar
            </button>
          </div>
        </div>
      `;
    }
  });
}

// Función para reintentar carga de PDF
function retryPDFLoad(s3Url, pdfTitle, container) {
  console.log("[PDF-FINAL] 🔄 Reintentando carga de PDF:", s3Url);
  
  try {
    // Mostrar indicador de reintento
    container.innerHTML = `
      <div class="text-center p-4">
        <div class="spinner-border text-primary mb-3" role="status">
          <span class="visually-hidden">Reintentando...</span>
        </div>
        <h5>Reintentando Carga del PDF</h5>
        <p class="text-muted">Intentando cargar nuevamente desde S3...</p>
      </div>
    `;
    
    // Esperar un momento y reintentar
    setTimeout(() => {
      console.log("[PDF-FINAL] 🔄 Iniciando reintento de carga...");
      
      // Llamar a la función de carga S3 nuevamente
      if (typeof loadS3PDFWithJS === 'function') {
        loadS3PDFWithJS(s3Url, pdfTitle, container);
      } else {
        console.error("[PDF-FINAL] ❌ Función loadS3PDFWithJS no disponible");
        container.innerHTML = `
          <div class="text-center p-4">
            <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
            <h5>Error en Reintento</h5>
            <p class="text-muted">No se pudo reintentar la carga del PDF.</p>
            <div class="btn-group mt-3" role="group">
              <a href="${s3Url}" target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
              </a>
              <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${s3Url}', '${pdfTitle}')">
                <i class="fas fa-download"></i> Descargar
              </button>
            </div>
          </div>
        `;
      }
    }, 2000); // Esperar 2 segundos antes de reintentar
    
  } catch (error) {
    console.error("[PDF-FINAL] ❌ Error en reintento:", error);
    
    // Mostrar error de reintento
    container.innerHTML = `
      <div class="text-center p-4">
        <i class="fas fa-exclamation-triangle fa-4x text-danger mb-3"></i>
        <h5>Error en Reintento</h5>
        <p class="text-muted">No se pudo reintentar la carga del PDF.</p>
        <div class="btn-group mt-3" role="group">
          <a href="${s3Url}" target="_blank" class="btn btn-primary">
            <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
          </a>
          <button type="button" class="btn btn-outline-primary" onclick="downloadS3File('${s3Url}', '${pdfTitle}')">
            <i class="fas fa-download"></i> Descargar
          </button>
        </div>
      </div>
    `;
  }
}

// Función para mostrar multimedia en modal
function showMultimediaModal(multimediaSrc, multimediaTitle) {
  console.log("[MODAL-FINAL] 🎬 showMultimediaModal llamado con:", { multimediaSrc, multimediaTitle });
  
  // Usar modal Bootstrap
  const modalElement = document.getElementById('multimediaModal');
  const modalContent = document.getElementById('multimediaContent');
  const modalTitle = document.getElementById('multimediaModalLabel');
  
  if (!modalElement || !modalContent || !modalTitle) {
    console.error("[MODAL-FINAL] ❌ Elementos del modal multimedia no encontrados:", {
      modalElement: !!modalElement,
      modalContent: !!modalContent,
      modalTitle: !!modalTitle
    });
    return;
  }
  
  // Configurar título
  modalTitle.textContent = multimediaTitle || 'Multimedia';
  
  // Determinar tipo de archivo
  const fileExtension = multimediaSrc.split('.').pop()?.toLowerCase();
  let mediaHTML = '';
  
  if (['mp4', 'webm', 'avi', 'mov'].includes(fileExtension)) {
    // Video
    mediaHTML = `
      <video controls class="img-fluid" style="max-width: 100%; height: auto;">
        <source src="${multimediaSrc}" type="video/${fileExtension}">
        Tu navegador no soporta el elemento de video.
      </video>
    `;
  } else if (['mp3', 'wav', 'ogg', 'aac'].includes(fileExtension)) {
    // Audio
    mediaHTML = `
      <audio controls class="img-fluid" style="width: 100%;">
        <source src="${multimediaSrc}" type="audio/${fileExtension}">
        Tu navegador no soporta el elemento de audio.
      </audio>
    `;
  } else {
    // Otros tipos - mostrar como enlace
    mediaHTML = `
      <div class="text-center">
        <i class="fas fa-file-video fa-4x text-primary mb-3"></i>
        <h5>Archivo Multimedia</h5>
        <p class="text-muted">Tipo de archivo: ${fileExtension || 'Desconocido'}</p>
        <a href="${multimediaSrc}" target="_blank" class="btn btn-primary">
          <i class="fas fa-external-link-alt"></i> Abrir en Nueva Pestaña
        </a>
      </div>
    `;
  }
  
  // Configurar contenido del modal
  modalContent.innerHTML = mediaHTML;
  
  // Mostrar modal
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  
  console.log("[MODAL-FINAL] ✅ Modal multimedia mostrado correctamente");
}

// Función para mostrar imágenes en modal CORREGIDA
function showImageModal(imageSrc, imageTitle) {
  console.log("[MODAL-FINAL] 🖼️ showImageModal llamado con:", { imageSrc, imageTitle });
  
  // Buscar elementos del modal según la estructura HTML real
  const modalElement = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  const modalTitle = document.getElementById('imageModalLabel');
  
  if (!modalElement || !modalImage || !modalTitle) {
    console.error("[MODAL-FINAL] ❌ Elementos del modal de imagen no encontrados:", {
      modalElement: !!modalElement,
      modalImage: !!modalImage,
      modalTitle: !!modalTitle
    });
    return;
  }
  
  // Configurar título
  modalTitle.textContent = imageTitle || 'Imagen';
  
  // Configurar imagen con manejo de errores
  modalImage.src = imageSrc;
  modalImage.alt = imageTitle || 'Imagen';
  modalImage.onerror = function() {
    console.log("[MODAL-FINAL] ⚠️ Error cargando imagen, usando fallback");
    this.src = '/static/img/image-error-placeholder.png'; // Fallback si existe
    this.alt = 'Error cargando imagen';
  };
  
  // Mostrar modal
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
  
  console.log("[MODAL-FINAL] ✅ Modal de imagen mostrado correctamente");
}

// Función para descargar multimedia
function downloadMultimedia() {
  console.log("[MODAL-FINAL] 🔧 Función de descarga multimedia llamada");
  
  try {
    // Obtener el contenido del modal multimedia
    const modalContent = document.getElementById('multimediaContent');
    if (!modalContent) {
      console.error("[MODAL-FINAL] ❌ No hay contenido multimedia para descargar");
      alert('No hay contenido multimedia para descargar');
      return;
    }
    
    // Buscar elementos de video o audio
    const videoElement = modalContent.querySelector('video source');
    const audioElement = modalContent.querySelector('audio source');
    
    let mediaSrc = '';
    let mediaTitle = '';
    
    if (videoElement) {
      mediaSrc = videoElement.src;
      mediaTitle = 'video';
    } else if (audioElement) {
      mediaSrc = audioElement.src;
      mediaTitle = 'audio';
    } else {
      // Buscar enlace si no hay elementos multimedia
      const linkElement = modalContent.querySelector('a');
      if (linkElement) {
        mediaSrc = linkElement.href;
        mediaTitle = 'multimedia';
      }
    }
    
    if (!mediaSrc) {
      console.error("[MODAL-FINAL] ❌ No se encontró fuente multimedia");
      alert('No se puede determinar la fuente multimedia');
      return;
    }
    
    console.log("[MODAL-FINAL] 🔧 Descargando multimedia:", mediaSrc);
    
    // Crear enlace temporal y hacer clic
    const link = document.createElement('a');
    link.href = mediaSrc;
    link.download = mediaTitle;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log("[MODAL-FINAL] ✅ Descarga de multimedia iniciada");
    
  } catch (error) {
    console.error("[MODAL-FINAL] ❌ Error descargando multimedia:", error);
    alert('Error al descargar la multimedia: ' + error.message);
  }
}

// Función para descargar imágenes CORREGIDA
function downloadImage() {
  console.log("[MODAL-FINAL] 🔧 Función de descarga de imagen llamada");
  
  try {
    // Obtener la imagen del modal
    const modalImage = document.getElementById('modalImage');
    if (!modalImage || !modalImage.src) {
      console.error("[MODAL-FINAL] ❌ No hay imagen para descargar");
      alert('No hay imagen para descargar');
      return;
    }
    
    const imageSrc = modalImage.src;
    const imageTitle = modalImage.alt || 'imagen';
    
    console.log("[MODAL-FINAL] 🔧 Descargando imagen:", imageSrc);
    
    // Crear enlace temporal y hacer clic
    const link = document.createElement('a');
    link.href = imageSrc;
    link.download = imageTitle;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log("[MODAL-FINAL] ✅ Descarga de imagen iniciada");
    
  } catch (error) {
    console.error("[MODAL-FINAL] ❌ Error descargando imagen:", error);
    alert('Error al descargar la imagen: ' + error.message);
  }
}

// Funciones de control para Markdown
function toggleMarkdownTheme() {
  const markdownContent = document.getElementById('markdown-content');
  if (!markdownContent) return;
  
  const currentTheme = markdownContent.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  markdownContent.setAttribute('data-theme', newTheme);
  
  if (newTheme === 'dark') {
    markdownContent.style.backgroundColor = '#1a1a1a';
    markdownContent.style.color = '#ffffff';
  } else {
    markdownContent.style.backgroundColor = '#ffffff';
    markdownContent.style.color = '#333333';
  }
  
  console.log(`[MARKDOWN-PERFECT] ✅ Tema cambiado a: ${newTheme}`);
}

function toggleMarkdownFontSize() {
  const markdownContent = document.getElementById('markdown-content');
  if (!markdownContent) return;
  
  const currentSize = markdownContent.getAttribute('data-font-size') || 'medium';
  const sizes = { 'small': '0.9em', 'medium': '1em', 'large': '1.2em', 'xlarge': '1.4em' };
  const sizeNames = Object.keys(sizes);
  const currentIndex = sizeNames.indexOf(currentSize);
  const nextIndex = (currentIndex + 1) % sizeNames.length;
  const newSize = sizeNames[nextIndex];
  
  markdownContent.setAttribute('data-font-size', newSize);
  markdownContent.style.fontSize = sizes[newSize];
  
  console.log(`[MARKDOWN-PERFECT] ✅ Tamaño de fuente cambiado a: ${newSize}`);
}

function toggleMarkdownLineNumbers() {
  const markdownContent = document.getElementById('markdown-content');
  if (!markdownContent) return;
  
  const hasLineNumbers = markdownContent.classList.contains('line-numbers');
  
  if (hasLineNumbers) {
    markdownContent.classList.remove('line-numbers');
    console.log("[MARKDOWN-PERFECT] ✅ Números de línea desactivados");
  } else {
    markdownContent.classList.add('line-numbers');
    console.log("[MARKDOWN-PERFECT] ✅ Números de línea activados");
  }
}

// Función para descargar archivos Markdown
function downloadMarkdownFile(fileUrl, fileName) {
  console.log("[MARKDOWN-PERFECT] 🔧 Descargando archivo Markdown:", fileUrl);
  
  try {
    // Determinar si es archivo S3 o local
    const isS3File = fileUrl.includes('s3.amazonaws.com') || fileUrl.includes('edf-catalogo-tablas.s3');
    
    if (isS3File) {
      // Archivo S3 - usar proxy backend
      const proxyUrl = fileUrl.replace(
        'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/',
        '/admin/s3/'
      );
      
      console.log("[MARKDOWN-PERFECT] 🔧 URL S3 convertida a proxy para descarga:", proxyUrl);
      
      // Crear enlace temporal y hacer clic
      const link = document.createElement('a');
      link.href = proxyUrl;
      link.download = fileName || 'documento.md';
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log("[MARKDOWN-PERFECT] ✅ Descarga iniciada para archivo S3");
      
    } else {
      // Archivo local - descarga directa
      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = fileName || 'documento.md';
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log("[MARKDOWN-PERFECT] ✅ Descarga iniciada para archivo local");
    }
    
  } catch (error) {
    console.error("[MARKDOWN-PERFECT] ❌ Error descargando archivo Markdown:", error);
    alert('Error al descargar el archivo: ' + error.message);
  }
}

// Función para exportar Markdown a PDF
function exportMarkdownToPDF(fileName) {
  console.log("[MARKDOWN-PERFECT] 🔧 Exportando Markdown a PDF:", fileName);
  
  try {
    const markdownContent = document.getElementById('markdown-content');
    if (!markdownContent) {
      alert('No hay contenido Markdown para exportar');
      return;
    }
    
    // Crear ventana de impresión con contenido Markdown
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    printWindow.document.write(`
      <html>
        <head>
          <title>${fileName || 'Documento Markdown'} - PDF</title>
          <style>
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              line-height: 1.6; 
              color: #333; 
              margin: 40px;
              max-width: 800px;
              margin-left: auto;
              margin-right: auto;
            }
            h1, h2, h3, h4, h5, h6 { 
              margin-top: 1.5em; 
              margin-bottom: 0.5em; 
              font-weight: 600; 
              line-height: 1.25; 
            }
            h1 { font-size: 2em; border-bottom: 2px solid #eaecef; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
            h3 { font-size: 1.25em; }
            p { margin-bottom: 1em; }
            ul, ol { margin-bottom: 1em; padding-left: 2em; }
            li { margin-bottom: 0.5em; }
            blockquote { margin: 1em 0; padding: 0 1em; color: #6a737d; border-left: 4px solid #dfe2e5; background-color: #f6f8fa; }
            code { background-color: #f6f8fa; padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace; }
            pre { background-color: #f6f8fa; padding: 1em; border-radius: 6px; overflow-x: auto; border: 1px solid #e1e4e8; }
            pre code { background-color: transparent; padding: 0; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #dfe2e5; padding: 0.5em; text-align: left; }
            th { background-color: #f6f8fa; font-weight: 600; }
            img { max-width: 100%; height: auto; }
            hr { border: none; border-top: 1px solid #eaecef; margin: 2em 0; }
            @media print {
              body { margin: 20px; }
              h1, h2, h3 { page-break-after: avoid; }
              pre, blockquote { page-break-inside: avoid; }
            }
          </style>
        </head>
        <body>
          ${markdownContent.innerHTML}
        </body>
      </html>
    `);
    
    printWindow.document.close();
    
    // Esperar a que se renderice y luego imprimir
    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
      console.log("[MARKDOWN-PERFECT] ✅ Exportación a PDF iniciada");
    }, 1000);
    
  } catch (error) {
    console.error("[MARKDOWN-PERFECT] ❌ Error exportando a PDF:", error);
    alert('Error al exportar a PDF: ' + error.message);
  }
}

// Función para manejar errores de imagen
function handleImageError(img) {
  // VERIFICACIÓN DE SEGURIDAD: Comprobar que img sea válido
  if (!img || typeof img !== 'object' || !img.src) {
    console.log("[MODAL-FINAL] ⚠️ handleImageError llamado con parámetro inválido:", img);
    return;
  }
  
  console.log("[MODAL-FINAL] 🔧 handleImageError llamado para:", img.src);
  
  try {
    // Reemplazar imagen rota con placeholder
    img.onerror = null; // Prevenir bucle infinito
    img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iI2FkYjVjZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlbiBubyBkaXNwb25pYmxlPC90ZXh0Pjwvc3ZnPg==';
    img.alt = 'Imagen no disponible';
    
    console.log("[MODAL-FINAL] ✅ Imagen reemplazada con placeholder");
  } catch (error) {
    console.log("[MODAL-FINAL] ⚠️ Error en handleImageError:", error.message);
  }
}

// Exportar funciones adicionales
window.showMarkdownInModal = showMarkdownInModal;
window.showTextInModal = showTextInModal;
window.showDocumentModal = showDocumentModal;
window.showImageModal = showImageModal; // Exportar modal de imágenes
window.showMultimediaModal = showMultimediaModal; // Exportar modal multimedia
window.handleImageError = handleImageError; // Exportar para uso global
window.retryPDFLoad = retryPDFLoad; // Exportar función de reintento

// Exportar funciones de Markdown
window.toggleMarkdownTheme = toggleMarkdownTheme;
window.toggleMarkdownFontSize = toggleMarkdownFontSize;
window.toggleMarkdownLineNumbers = toggleMarkdownLineNumbers;
window.downloadMarkdownFile = downloadMarkdownFile;
window.exportMarkdownToPDF = exportMarkdownToPDF;

console.log(
  "[MODAL-FINAL] ✅ Todas las funciones de modal cargadas correctamente - VERSION: 2025-01-03-23:30"
);
