/**
 * Scripts Tools Manager - Interfaz para gestionar y ejecutar scripts y herramientas
 * 
 * Este módulo proporciona funcionalidad para listar, filtrar, ejecutar y descargar
 * scripts y herramientas del sistema.
 * 
 * ATENCIÓN: jQuery debe estar cargado antes de este script para evitar errores de '$ is not defined'.
 */

// Esperar a que jQuery esté disponible y luego inicializar
(function(window) {
  // Función para verificar si jQuery está cargado
  function jQueryCheck(callback) {
    if (window.jQuery) {
      callback(window.jQuery);
    } else {
      window.setTimeout(function() { jQueryCheck(callback); }, 100);
    }
  }

  // Inicializar cuando jQuery esté disponible
  jQueryCheck(function($) {
    // Estado de la aplicación - variables locales al scope
    var scriptTools = {
      allFiles: {scripts: [], tests: [], tools: []},
      currentDir: "scripts",
      currentPage: 1,
      perPage: 20,
      currentFileType: "",
      isLastPage: false,
      isLoading: false
    };

    /**
     * Formatea un tamaño en bytes a una representación legible (B, KB, MB)
     * @param {number} size - Tamaño en bytes
     * @return {string} Tamaño formateado
     */
    function formatSize(size) {
      if (size === null || size === undefined) return "";
      if (size < 1024) return size + " B";
      if (size < 1024*1024) return (size/1024).toFixed(1) + " KB";
      return (size/1024/1024).toFixed(1) + " MB";
    }

    /**
     * Escapa caracteres HTML para prevenir XSS
     * @param {string} text - Texto a escapar
     * @return {string} Texto escapado
     */
    function escapeHtml(text) {
      if (!text) return "";
      // Usar una implementación más directa en lugar de crear elementos DOM
      return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
    /**
     * Renderiza la tabla de archivos con filtrado y paginación
     * @param {string} dir - Directorio actual (scripts, tests, tools)
     */
    function renderTable(dir) {
      const search = $("#searchInput").val() ? $("#searchInput").val().toLowerCase() : "";
      const tbody = $("#filesTable tbody");
      
      // Limpiar tabla y mostrar indicador de carga si es necesario
      tbody.empty();
      
      if (scriptTools.isLoading) {
        tbody.append("<tr><td colspan=\"6\" class=\"text-center\"><div class=\"spinner-border spinner-border-sm\" role=\"status\"></div> Cargando...</td></tr>");
        return;
      }
      
      // Filtrar y renderizar archivos
      let count = 0;
      const files = scriptTools.allFiles[dir] || [];
      
      if (files.length === 0) {
        tbody.append("<tr><td colspan=\"6\" class=\"text-center\">No se encontraron archivos</td></tr>");
        return;
      }
      
      files.forEach(f => {
        // Filtrar por búsqueda
        if (search && !(
          f.name.toLowerCase().includes(search) || 
          (f.description && f.description.toLowerCase().includes(search))
        )) return;
        
        // Preparar botones de acción según tipo de archivo
        const type = f.is_dir ? "Directorio" : "Archivo";
        const buttons = createActionButtons(f);
        
        // Añadir fila a la tabla
        tbody.append(`
          <tr>
            <td>${escapeHtml(f.name)}</td>
            <td>${type}</td>
            <td>${f.size !== null ? formatSize(f.size) : ""}</td>
            <td>${escapeHtml(f.mtime || "")}</td>
            <td>${escapeHtml(f.description || "")}</td>
            <td>${buttons}</td>
          </tr>
        `);
        count++;
      });
      
      // Actualizar información de paginación
      scriptTools.isLastPage = count < scriptTools.perPage;
      updatePaginationState();
      
      // Si no hay resultados con el filtro actual
      if (count === 0 && search) {
        tbody.append("<tr><td colspan=\"6\" class=\"text-center\">No se encontraron coincidencias para la búsqueda</td></tr>");
      }
    }
  
    /**
     * Crea los botones de acción para un archivo
     * @param {Object} file - Información del archivo
     * @return {string} HTML con los botones de acción
     */
    function createActionButtons(file) {
      let runBtn = "";
      let argsBtn = "";
      let downloadBtn = "";
      
      // Botones para scripts ejecutables
      if (!file.is_dir && (file.name.endsWith(".py") || file.name.endsWith(".sh"))) {
        const fileType = file.name.endsWith(".sh") ? "sh" : "py";
        const safePath = escapeHtml(file.rel_path);
        
        runBtn = `<button class="btn btn-sm btn-outline-primary run-script-btn me-1" 
                  data-path="${safePath}" data-type="${fileType}">Ejecutar</button>`;
        argsBtn = `<button class="btn btn-sm btn-outline-secondary run-args-btn me-1" 
                  data-path="${safePath}" data-type="${fileType}">Args</button>`;
      }
      
      // Botón de descarga para todos los archivos (no directorios)
      if (!file.is_dir) {
        downloadBtn = `<a class="btn btn-sm btn-outline-success" 
                      href="/admin/scripts-tools-api/download?rel_path=${encodeURIComponent(file.rel_path)}" 
                      title="Descargar" download><i class="bi bi-download"></i></a>`;
      }
      
      return runBtn + argsBtn + downloadBtn;
    }

    /**
     * Actualiza el estado visual de los botones de paginación
     */
    function updatePaginationState() {
      // Actualizar texto de página
      $("#pageInfo").text("Página " + scriptTools.currentPage + (scriptTools.isLastPage ? " (última)" : ""));
      
      // Habilitar/deshabilitar botones según estado
      $("#prevPageBtn").prop("disabled", scriptTools.currentPage <= 1);
      $("#nextPageBtn").prop("disabled", scriptTools.isLastPage);
    }
    /**
     * Carga los archivos desde el servidor con manejo de errores
     */
    function loadFiles() {
      // Mostrar estado de carga
      scriptTools.isLoading = true;
      renderTable(scriptTools.currentDir);
      
      // Preparar parámetros de la petición
      const params = {
        page: scriptTools.currentPage,
        per_page: scriptTools.perPage,
        filetype: scriptTools.currentFileType
      };
      
      // Realizar petición AJAX con manejo de errores
      $.ajax({
        url: "/admin/scripts-tools-api/list",
        method: "GET",
        data: params,
        dataType: "json",
        success: function(data) {
          scriptTools.allFiles = data;
          scriptTools.isLoading = false;
          renderTable(scriptTools.currentDir);
        },
        error: function(xhr, status, error) {
          scriptTools.isLoading = false;
          const errorMsg = xhr.responseJSON && xhr.responseJSON.error 
            ? xhr.responseJSON.error 
            : "Error al cargar la lista de archivos";
          
          // Mostrar error en la tabla
          const tbody = $("#filesTable tbody");
          tbody.empty();
          tbody.append(`<tr><td colspan="6" class="text-center text-danger">
            <i class="bi bi-exclamation-triangle"></i> ${errorMsg}
          </td></tr>`);
          
          console.error("Error cargando archivos:", error);
        }
      });
    }
    
    // Event Listeners
    // ===============
    
    // Cambio de pestaña (scripts, tests, tools)
    $("#scriptsTabs .nav-link").click(function(e) {
      e.preventDefault();
      $("#scriptsTabs .nav-link").removeClass("active");
      $(this).addClass("active");
      scriptTools.currentDir = $(this).data("dir");
      scriptTools.currentPage = 1;
      loadFiles();
    });
    
    // Filtro de búsqueda
    $("#searchInput").on("input", function() {
      renderTable(scriptTools.currentDir);
    });
    
    // Filtro por tipo de archivo
    $("#fileTypeFilter").on("change", function() {
      scriptTools.currentFileType = $(this).val();
      scriptTools.currentPage = 1;
      loadFiles();
    });
    
    // Navegación de páginas
    $("#prevPageBtn").click(function() {
      if (scriptTools.currentPage > 1) { 
        scriptTools.currentPage--; 
        loadFiles(); 
      }
    });
    
    $("#nextPageBtn").click(function() {
      if (!scriptTools.isLastPage) {
        scriptTools.currentPage++; 
        loadFiles();
      }
    });

    // Iniciar cuando el DOM esté listo
    $(function() {
      loadFiles();
    });
  });
})(window);
