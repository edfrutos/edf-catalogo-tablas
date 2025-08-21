// Dashboard.js - VERSIÓN COMPLETA CON ELIMINACIÓN AUTOMÁTICA
console.log("🔧 Dashboard.js cargado - VERSIÓN COMPLETA - Timestamp:", new Date().toISOString());

$(function () {
  console.log("🔧 Inicializando dashboard completo...");

  // Variables globales para Google Drive
  let allBackups = [];
  let selectedBackups = new Set();

  // Sistema de eliminación automática de alertas duplicadas
  function removeDuplicateAlerts() {
    const alerts = $('.alert');
    const seenMessages = new Set();

    alerts.each(function () {
      const message = $(this).text().trim();
      if (seenMessages.has(message)) {
        console.log(`🗑️ Eliminando alerta duplicada: ${message}`);
        $(this).remove();
      } else {
        seenMessages.add(message);
      }
    });
  }

  // Función ultra-simple para mostrar alertas
  function showAlert(message, type = "success") {
    console.log(`📢 showAlert: ${message}`);

    // Crear la alerta
    const alertId = `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const alert = `
      <div id="${alertId}" class="alert alert-${type} fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" onclick="$(this).closest('.alert').remove()" aria-label="Cerrar"></button>
      </div>
    `;

    $(".container").prepend(alert);

    // Eliminar duplicados inmediatamente
    removeDuplicateAlerts();

    // Auto-eliminar después de 5 segundos
    setTimeout(function () {
      $(`#${alertId}`).fadeOut(500, function () {
        $(this).remove();
      });
    }, 5000);
  }

  // Función para mostrar alertas en el modal de backups locales
  function showModalAlert(message, type = "success") {
    console.log(`📢 showModalAlert: ${message}`);

    // Crear la alerta
    const alertId = `modalAlert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const alert = `
      <div id="${alertId}" class="alert alert-${type} fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" onclick="$(this).closest('.alert').remove()" aria-label="Cerrar"></button>
      </div>
    `;

    // Añadir alerta al modal de backups locales
    $("#localBackupsModal .modal-body").prepend(alert);

    // Auto-eliminar después de 5 segundos
    setTimeout(function () {
      $(`#${alertId}`).fadeOut(500, function () {
        $(this).remove();
      });
    }, 5000);
  }

  // Función para mostrar ventanas emergentes de confirmación
  function showConfirmationModal(title, message, type = "info", autoClose = true) {
    const iconClass = {
      success: "bi-check-circle-fill text-success",
      error: "bi-exclamation-triangle-fill text-danger",
      warning: "bi-exclamation-triangle-fill text-warning",
      info: "bi-info-circle-fill text-info"
    }[type] || "bi-info-circle-fill text-info";

    const modalId = `confirmationModal_${Date.now()}`;

    const modalHtml = `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-${type === "success" ? "success" : type === "error" ? "danger" : type === "warning" ? "warning" : "info"} text-white">
            <h5 class="modal-title" id="${modalId}Label">
              <i class="${iconClass} me-2"></i>${title}
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            <p class="mb-0">${message}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="bi bi-x-circle"></i> Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

    // Añadir modal al DOM
    $("body").append(modalHtml);

    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();

    // Auto-cerrar después de 5 segundos si está habilitado
    if (autoClose) {
      setTimeout(() => {
        modal.hide();
      }, 5000);
    }

    // Limpiar modal del DOM cuando se cierre
    document.getElementById(modalId).addEventListener("hidden.bs.modal", function () {
      $(this).remove();
    });
  }

  // Función para mostrar confirmación modal que devuelve una promesa
  function showConfirmDialog(title, message, type = "warning") {
    const modalId = `confirmDialog_${Date.now()}`;

    const modalHtml = `
      <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header bg-${type === "danger" ? "danger" : "warning"} text-white">
              <h5 class="modal-title" id="${modalId}Label">
                <i class="bi bi-question-circle me-2"></i>${title}
              </h5>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
            <div class="modal-body">
              <p class="mb-0">${message}</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cancelar
              </button>
              <button type="button" class="btn btn-${type === "danger" ? "danger" : "warning"}" id="confirmAction">
                <i class="bi bi-check-circle"></i> Confirmar
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    $("body").append(modalHtml);
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();

    return new Promise((resolve) => {
      $(`#${modalId} #confirmAction`).on("click", function () {
        modal.hide();
        $(`#${modalId}`).remove();
        resolve(true);
      });

      $(`#${modalId}`).on("hidden.bs.modal", function () {
        $(`#${modalId}`).remove();
        resolve(false);
      });
    });
  }

  // Función ultra-simple para ejecutar tareas
  window.runTask = function runTask(task) {
    console.log(`🔧 runTask: ${task}`);

    const btn = $(`.run-task[data-task="${task}"]`);

    // Si el botón ya está deshabilitado, ignorar
    if (btn.prop('disabled')) {
      console.log("⚠️ Botón ya deshabilitado, ignorando");
      return;
    }

    const originalText = btn.html();

    btn.prop("disabled", true)
      .html("<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span> Ejecutando...");

    const formData = new FormData();
    formData.append("task", task);

    $.ajax({
      url: "/admin/api/run_task",
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log("✅ Tarea ejecutada:", response);
        const now = new Date().toLocaleString();
        showAlert(`Tarea "${task}" ejecutada correctamente (${now})`, "success");

        // Actualizar timestamp
        const cellId = getTaskCellId(task);
        if (cellId) {
          $(`#${cellId}`).html(`<small class="text-success">${now}</small>`);
        }
      },
      error: function (xhr, status, error) {
        const msg = xhr.responseJSON?.message || `Error al ejecutar la tarea: ${error}`;
        showAlert(msg, "danger");
      },
      complete: function () {
        btn.html(originalText).prop("disabled", false);
      }
    });
  };

  // Función auxiliar
  function getTaskCellId(task) {
    switch (task) {
      case "cleanup": return "lastCleanupRun";
      case "mongo": return "lastMongoCheck";
      case "disk": return "lastDiskCheck";
      default: return "";
    }
  }

  // ============================================
  // EVENTOS DE BACKUP
  // ============================================
  function initializeBackupEvents() {
    console.log("✅ Inicializando eventos de backup...");

    $("#backupBtn")
      .off("click")
      .on("click", function () {
        console.log("✅ Click detectado en botón backup - abriendo modal de opciones");
        console.log("🔍 Modal element exists:", $('#backupOptionsModal').length);
        console.log("🔍 Bootstrap modal available:", typeof $.fn.modal);
        
        if ($('#backupOptionsModal').length === 0) {
          console.error("❌ Modal #backupOptionsModal no encontrado en el DOM");
          alert("Error: Modal de opciones no encontrado. Refrescar la página.");
          return;
        }
        
        try {
          $('#backupOptionsModal').modal('show');
          console.log("✅ Modal show() ejecutado");
        } catch (error) {
          console.error("❌ Error al mostrar modal:", error);
          alert("Error al abrir modal: " + error.message);
        }
      });
  }

  // Función para inicializar eventos de backup options modal
  window.initializeBackupModalEvents = function() {
    console.log("✅ Inicializando eventos del modal de opciones de backup...");
    
    // Manejadores para los botones del modal de backup
    $(document).on("click", "#createBackupLocalBtn", function () {
      console.log("✅ Backup Local seleccionado");
      $('#backupOptionsModal').modal('hide');
      executeLocalBackup();
    });
    
    $(document).on("click", "#createBackupDriveBtn", function () {
      console.log("✅ Backup Google Drive seleccionado");
      $('#backupOptionsModal').modal('hide');
      executeGoogleDriveBackup();
    });
  }

  // ============================================
  // FUNCIONES DE BACKUP
  // ============================================
  
  function executeLocalBackup() {
    console.log("🗂️ Iniciando backup local...");
    
    // Mostrar estado de carga
    $("#backupResult").html(`
      <div class="alert alert-info">
        <i class="bi bi-folder-plus"></i> Creando backup local de la base de datos...
        <div class="spinner-border spinner-border-sm ms-2" role="status">
          <span class="visually-hidden">Cargando...</span>
        </div>
      </div>
    `);

    $.ajax({
      url: "/admin/maintenance/backup-local",
      method: "POST",
      xhrFields: { withCredentials: true },
      timeout: 120000, // 2 minutos
      success: function (response) {
        console.log("✅ Backup local completado:", response);
        
        if (response.status === "success") {
          const successMsg = `
            <div class="alert alert-success">
              <i class="bi bi-check-circle"></i>
              <strong>Backup local creado exitosamente</strong><br>
              <small>
                • Archivo: ${response.filename}<br>
                • Ubicación: ${response.file_path}<br>
                • Tamaño: ${(response.size / 1024).toFixed(2)} KB<br>
                • Documentos: ${response.total_documents}<br>
                • Colecciones: ${response.total_collections}<br>
                • Fecha: ${new Date().toLocaleString()}<br>
                <button class="btn btn-sm btn-outline-success mt-2" onclick="downloadBackup('${response.filename}')">
                  <i class="bi bi-download"></i> Descargar Backup
                </button>
              </small>
            </div>
          `;
          $("#backupResult").html(successMsg);
          showAlert("Backup local creado correctamente", "success");
          
          // Actualizar lista de backups locales si está visible
          if (typeof window.loadLocalBackups === "function") {
            setTimeout(() => window.loadLocalBackups(), 2000);
          }
        } else {
          throw new Error(response.error || "Error desconocido");
        }
      },
      error: function (xhr, status, error) {
        console.error("❌ Error en backup local:", xhr.status, xhr.statusText, error);
        const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error de conexión";
        $("#backupResult").html(`
          <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i>
            <strong>Error al crear backup local</strong><br>
            <small>${errorMsg}</small>
          </div>
        `);
        showAlert("Error al crear backup local: " + errorMsg, "danger");
      },
      complete: function () {
        // Auto-cerrar el resultado después de 15 segundos
        setTimeout(() => {
          $("#backupResult").fadeOut(500, function () {
            $(this).empty();
          });
        }, 15000);
      }
    });
  }

  function executeGoogleDriveBackup() {
    console.log("☁️ Iniciando backup en Google Drive...");
    
    // Mostrar estado de carga
    $("#backupResult").html(`
      <div class="alert alert-info">
        <i class="bi bi-google"></i> Creando backup y subiendo a Google Drive...
        <div class="spinner-border spinner-border-sm ms-2" role="status">
          <span class="visually-hidden">Cargando...</span>
        </div>
      </div>
    `);

    $.ajax({
      url: "/admin/maintenance/backup",
      method: "POST",
      xhrFields: { withCredentials: true },
      timeout: 180000, // 3 minutos para Google Drive
      success: function (response) {
        console.log("✅ Backup Google Drive completado:", response);
        
        if (response.status === "success" && response.uploaded_to_drive) {
          const successMsg = `
            <div class="alert alert-success">
              <i class="bi bi-check-circle"></i>
              <strong>Backup subido a Google Drive exitosamente</strong><br>
              <small>
                • <strong>Archivo:</strong> ${response.filename}<br>
                • <strong>Ubicación:</strong> Google Drive / ${response.drive_info.folder_name}<br>
                • <strong>Tamaño:</strong> ${(response.size / 1024).toFixed(2)} KB<br>
                • <strong>Documentos:</strong> ${response.total_documents}<br>
                • <strong>Colecciones:</strong> ${response.total_collections}<br>
                • <strong>Fecha:</strong> ${new Date().toLocaleString()}<br>
                • <strong>ID Drive:</strong> ${response.drive_info.file_id}<br>
                <div class="mt-3">
                  <a href="${response.drive_info.web_view_url}" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-google"></i> Ver en Google Drive
                  </a>
                  <button class="btn btn-sm btn-outline-success ms-2" onclick="downloadBackup('${response.filename}')">
                    <i class="bi bi-download"></i> Descargar Copia Local
                  </button>
                </div>
              </small>
            </div>
          `;
          $("#backupResult").html(successMsg);
          showAlert("Backup subido a Google Drive correctamente", "success");
          
          // Actualizar listas de backups
          if (typeof window.loadDriveBackups === "function") {
            setTimeout(() => window.loadDriveBackups(), 2000);
          }
          if (typeof window.loadLocalBackups === "function") {
            setTimeout(() => window.loadLocalBackups(), 2000);
          }
          
        } else if (response.status === "warning" && !response.uploaded_to_drive) {
          const warningMsg = `
            <div class="alert alert-warning">
              <i class="bi bi-exclamation-triangle"></i>
              <strong>Backup creado pero no subido a Google Drive</strong><br>
              <small>
                • <strong>Motivo:</strong> ${response.message}<br>
                • <strong>Archivo:</strong> ${response.filename}<br>
                • <strong>Ubicación:</strong> Servidor local (/backups/)<br>
                • <strong>Tamaño:</strong> ${(response.size / 1024).toFixed(2)} KB<br>
                • <strong>Documentos:</strong> ${response.total_documents}<br>
                • <strong>Colecciones:</strong> ${response.total_collections}<br>
                • <strong>Fecha:</strong> ${new Date().toLocaleString()}<br>
                <div class="mt-3">
                  <button class="btn btn-sm btn-outline-success" onclick="downloadBackup('${response.filename}')">
                    <i class="bi bi-download"></i> Descargar Backup Local
                  </button>
                </div>
              </small>
            </div>
          `;
          $("#backupResult").html(warningMsg);
          showAlert("Backup creado localmente, pero no se pudo subir a Google Drive", "warning");
          
        } else {
          throw new Error(response.error || "Error desconocido");
        }
      },
      error: function (xhr, status, error) {
        console.error("❌ Error en backup Google Drive:", xhr.status, xhr.statusText, error);
        const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error de conexión";
        $("#backupResult").html(`
          <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i>
            <strong>Error al crear backup en Google Drive</strong><br>
            <small>${errorMsg}</small>
          </div>
        `);
        showAlert("Error al crear backup en Google Drive: " + errorMsg, "danger");
      },
      complete: function () {
        // Auto-cerrar el resultado después de 15 segundos
        setTimeout(() => {
          $("#backupResult").fadeOut(500, function () {
            $(this).empty();
          });
        }, 15000);
      }
    });
  }

  // Función para descargar backup
  window.downloadBackup = function(filename) {
    console.log("📥 Descargando backup:", filename);
    window.open(`/admin/maintenance/download-backup/${encodeURIComponent(filename)}`, '_blank');
  }

  // Función legacy (mantener por compatibilidad pero no usar)
  function initializeBackupEventsLegacy() {
    console.log("⚠️ Función legacy - no debería ejecutarse");
    
    $("#backupBtn")
      .off("click")
      .on("click", function () {
        console.log("❌ LEGACY: Este código no debería ejecutarse");

        $("#backupResult").html(`
          <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> Creando backup de la base de datos...
          </div>
        `);

        $.ajax({
          url: "/admin/maintenance/backup",
          method: "POST",
          xhrFields: { withCredentials: true },
          timeout: 60000,
          success: function (response) {
            if (response.status === "success" && response.uploaded_to_drive) {
              const successMsg = `
      <div class="alert alert-success">
        <i class="bi bi-check-circle"></i>
        <strong>Backup subido a Google Drive exitosamente</strong><br>
        <small>
          • Archivo: ${response.filename}<br>
          • Tamaño: ${(response.size / 1024).toFixed(2)} KB<br>
          • Documentos: ${response.total_documents}<br>
          • Colecciones: ${response.total_collections}<br>
          • Carpeta: ${response.drive_info.folder_name}<br>
          <a href="${response.drive_info.web_view_url}" target="_blank" class="btn btn-sm btn-outline-primary mt-2">
            <i class="bi bi-google"></i> Ver en Google Drive
          </a>
        </small>
      </div>
    `;
              $("#backupResult").html(successMsg);
              showAlert("Backup subido a Google Drive correctamente", "success");

              // Actualizar lista de backups de Google Drive si está visible
              if (typeof window.loadDriveBackups === "function") {
                setTimeout(() => window.loadDriveBackups(), 2000);
              }

              // Auto-cerrar el resultado después de 10 segundos
              setTimeout(() => {
                $("#backupResult").fadeOut(500, function () {
                  $(this).empty();
                });
              }, 10000);

            } else if (response.status === "warning" && !response.uploaded_to_drive) {
              const warningMsg = `
      <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle"></i>
        <strong>Backup creado con advertencias</strong><br>
        <small>
          ${response.message}<br>
          <a href="${response.download_url}" class="btn btn-sm btn-outline-primary mt-2">
            <i class="bi bi-download"></i> Descargar Backup Local
          </a>
        </small>
      </div>
    `;
              $("#backupResult").html(warningMsg);
              showAlert("Backup creado pero no subido a Google Drive", "warning");

              // Auto-cerrar el resultado después de 10 segundos
              setTimeout(() => {
                $("#backupResult").fadeOut(500, function () {
                  $(this).empty();
                });
              }, 10000);

            } else {
              $("#backupResult").html(`
      <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle"></i>
        Backup completado con advertencias
      </div>
    `);

              // Auto-cerrar el resultado después de 10 segundos
              setTimeout(() => {
                $("#backupResult").fadeOut(500, function () {
                  $(this).empty();
                });
              }, 10000);
            }
          },
          error: function (xhr) {
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.message : xhr.statusText;
            $("#backupResult").html(`
              <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Error al crear backup</strong><br>
                <small>${errorMsg}</small>
              </div>
            `);
            showAlert("Error al generar backup: " + errorMsg, "danger");

            // Auto-cerrar el resultado después de 10 segundos
            setTimeout(() => {
              $("#backupResult").fadeOut(500, function () {
                $(this).empty();
              });
            }, 10000);
          },
          complete: function () {
            btn.prop("disabled", false).html(originalText);
          }
        });
      });
  }

  // ============================================
  // EVENTOS DE GOOGLE DRIVE
  // ============================================
  window.initializeGoogleDriveEvents = function () {
    console.log("✅ Inicializando eventos de Google Drive...");

    $("#restoreDriveModal").off("show.bs.modal").on("show.bs.modal", function () {
      console.log("🔵 [EVENT] show.bs.modal - Modal va a abrirse");
    });

    $("#restoreDriveModal").off("shown.bs.modal").on("shown.bs.modal", function () {
      console.log("✅ [EVENT] shown.bs.modal - Modal abierto exitosamente");
      loadDriveBackups();
    });

    // ✅ PRESERVADO: El botón principal sigue funcionando
    $("#restoreDriveBtn").off("click").on("click", function () {
      console.log("🔵 [EVENT] Botón Google Drive clickeado");
      loadDriveBackups();
    });

    // ✅ CORREGIDO: Solo cambio el selector del botón actualizar
    $("#refreshDriveBackups").off("click").on("click", function () {
      console.log("🔄 Actualizando lista de backups...");
      loadDriveBackups();
    });

    // Actualizar función de restauración con ventana emergente
    $(document).off("click", ".restore-drive-backup").on("click", ".restore-drive-backup", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const fileId = $(this).data("id");
      const filename = $(this).data("filename");
      const btn = $(this);
      const originalText = btn.html();

      // Verificar si el botón ya está procesando
      if (btn.prop("disabled")) {
        return false;
      }

      if (!confirm(`¿Estás seguro de que quieres restaurar el backup "${filename}"?\n\nEsta acción sobrescribirá los datos actuales.`)) {
        return false;
      }

      btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Restaurando...");

      $.ajax({
        url: `/admin/maintenance/drive/restore/${fileId}`,
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ filename: filename }),
        xhrFields: { withCredentials: true },
        success: function (response) {
          if (response.status === "success" || response.success) {
            showConfirmationModal(
              "Restauración Completada",
              `El backup "${filename}" se ha restaurado correctamente. Los datos han sido actualizados.`,
              "success"
            );
          } else {
            showConfirmationModal(
              "Error en Restauración",
              `No se pudo restaurar el backup "${filename}". ${response.message || "Error desconocido"}.`,
              "error"
            );
          }
        },
        error: function (xhr) {
          showConfirmationModal(
            "Error en Restauración",
            `Error al restaurar el backup "${filename}": ${xhr.responseJSON?.message || xhr.statusText}`,
            "error"
          );
        },
        complete: function () {
          btn.prop("disabled", false).html(originalText);
        }
      });

      return false;
    });

    $(document).off("click", ".download-drive-backup").on("click", ".download-drive-backup", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const filename = $(this).data("filename");
      const downloadUrl = $(this).data("download-url");
      const btn = $(this);
      const originalText = btn.html();

      if (btn.prop("disabled")) {
        return false;
      }

      btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Descargando...");

      // Crear enlace temporal para descarga
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setTimeout(() => {
        btn.prop("disabled", false).html(originalText);
        showAlert(`Descarga iniciada: ${filename}`, "success");
      }, 1000);

      return false;
    });

    $(document).off("click", ".delete-drive-backup").on("click", ".delete-drive-backup", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const fileId = $(this).data("id");
      const filename = $(this).data("filename");
      const btn = $(this);
      const originalText = btn.html();

      if (btn.prop("disabled")) {
        return false;
      }

      if (!confirm(`¿Estás seguro de que quieres eliminar el backup "${filename}"?\n\nEsta acción no se puede deshacer.`)) {
        return false;
      }

      btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Eliminando...");

      $.ajax({
        url: `/admin/maintenance/drive/delete/${fileId}`,
        method: "DELETE",
        xhrFields: { withCredentials: true },
        success: function (response) {
          if (response.status === "success" || response.success) {
            showAlert(`Backup "${filename}" eliminado correctamente`, "success");
            loadDriveBackups(); // Recargar lista
          } else {
            showAlert(`Error al eliminar backup: ${response.message || "Error desconocido"}`, "danger");
          }
        },
        error: function (xhr) {
          showAlert(`Error al eliminar backup: ${xhr.responseJSON?.message || xhr.statusText}`, "danger");
        },
        complete: function () {
          btn.prop("disabled", false).html(originalText);
        }
      });

      return false;
    });

    // Eventos de paginación y controles
    $("#backupsPerPage").off("change").on("change", function () {
      backupsPerPage = parseInt($(this).val());
      currentPage = 1;
      displayBackupsWithPagination();
    });

    $("#selectAllBackups").off("change").on("change", function () {
      const isChecked = $(this).prop("checked");
      $(".backup-checkbox:not(:disabled)").prop("checked", isChecked);

      if (isChecked) {
        $(".backup-checkbox:not(:disabled)").each(function () {
          selectedBackups.add($(this).data("backup-id"));
        });
      } else {
        selectedBackups.clear();
      }

      updateDeleteButton();
    });

    $(document).off("change", ".backup-checkbox").on("change", ".backup-checkbox", function () {
      const backupId = $(this).data("backup-id");
      if ($(this).prop("checked")) {
        selectedBackups.add(backupId);
      } else {
        selectedBackups.delete(backupId);
      }
      updateDeleteButton();
    });

    $("#deleteSelectedBackups").off("click").on("click", function () {
      if (selectedBackups.size === 0) {
        showAlert("No hay backups seleccionados para eliminar", "warning");
        return;
      }

      if (!confirm(`¿Estás seguro de que quieres eliminar ${selectedBackups.size} backup(s)?\n\nEsta acción no se puede deshacer.`)) {
        return;
      }

      const btn = $(this);
      const originalText = btn.html();
      btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Eliminando...");

      const deletePromises = Array.from(selectedBackups).map(backupId =>
        $.ajax({
          url: `/admin/maintenance/drive/delete/${backupId}`,
          method: "DELETE",
          xhrFields: { withCredentials: true }
        })
      );

      Promise.all(deletePromises)
        .then(() => {
          showAlert(`${selectedBackups.size} backup(s) eliminado(s) correctamente`, "success");
          selectedBackups.clear();
          loadDriveBackups();
        })
        .catch((error) => {
          showAlert("Error al eliminar algunos backups", "danger");
        })
        .finally(() => {
          btn.prop("disabled", false).html(originalText);
        });
    });
  };

  // Función para cargar backups de Google Drive
  window.loadDriveBackups = function () {
    console.log("🔄 Cargando backups de Google Drive...");

    $("#driveBackupsLoading").show();
    $("#driveBackupsContent").hide();
    $("#driveBackupsEmpty").hide();
    $("#driveBackupsError").hide();
    $("#driveBackupsTableBody").empty();

    $.ajax({
      url: "/admin/maintenance/drive/backups",
      method: "GET",
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log("📥 Respuesta de backups recibida:", response);
        $("#driveBackupsLoading").hide();

        if (response.success && response.backups && response.backups.length > 0) {
          allBackups = response.backups;
          displayDriveBackups(response.backups);
          $("#driveBackupsContent").show();
        } else {
          $("#driveBackupsEmpty").show();
          $("#driveBackupsCount").text("0 respaldos");
        }
      },
      error: function (xhr, status, error) {
        console.error("❌ Error cargando backups:", xhr.status, xhr.statusText, error);
        $("#driveBackupsLoading").hide();
        $("#driveBackupsError").show();
        $("#driveBackupsErrorMessage").text(`Error: ${xhr.statusText || "Error de conexión"}`);
      }
    });
  };

  // Función para mostrar backups de Google Drive
  function displayDriveBackups(backups) {
    $("#driveBackupsTableBody").empty();

    backups.forEach(function (backup) {
      const sizeDisplay = backup.file_size ? `${(backup.file_size / (1024 * 1024)).toFixed(2)} MB` : "N/A";
      const uploadDate = backup.uploaded_at ? new Date(backup.uploaded_at).toLocaleString() : "N/A";
      const filename = backup.filename || "backup";
      const isSelected = selectedBackups.has(backup._id);
      const isPlaceholder = backup.is_placeholder || false;

      let actionButtons;
      if (isPlaceholder) {
        // Mostrar botones deshabilitados para placeholders
        actionButtons = `
          <div class="btn-group" role="group">
            <button class="btn btn-sm btn-secondary" disabled title="Google Drive no configurado">
              <i class="bi bi-gear"></i> Configurar
            </button>
            <small class="text-muted d-block mt-1">
              ${backup.error_message || "Configura las credenciales de Google Drive"}
            </small>
          </div>
        `;
      } else {
        // Generar URL de descarga directa de Google Drive
        const downloadUrl = `https://drive.google.com/uc?export=download&id=${backup._id}`;
        const viewUrl = `https://drive.google.com/file/d/${backup._id}/view`;

        actionButtons = `
          <div class="btn-group" role="group">
            <button class="btn btn-sm btn-primary download-drive-backup"
                    data-id="${backup._id}"
                    data-filename="${backup.filename}"
                    data-download-url="${downloadUrl}"
                    title="Descargar backup">
              <i class="bi bi-download"></i> Descargar
            </button>
            <button class="btn btn-sm btn-success restore-drive-backup"
                    data-id="${backup._id}"
                    data-filename="${backup.filename}"
                    title="Restaurar backup">
              <i class="bi bi-arrow-counterclockwise"></i> Restaurar
            </button>
            <button class="btn btn-sm btn-danger delete-drive-backup"
                    data-id="${backup._id}"
                    data-filename="${backup.filename}"
                    title="Eliminar backup">
              <i class="bi bi-trash"></i> Eliminar
            </button>
            <a href="${viewUrl}"
               class="btn btn-sm btn-info"
               target="_blank"
               title="Ver en Google Drive">
              <i class="bi bi-google"></i> Ver
            </a>
          </div>
        `;
      }

      const row = `
        <tr data-backup-id="${backup._id}" ${isPlaceholder ? "class=\"table-warning\"" : ""}>
          <td>
            <input type="checkbox" class="form-check-input backup-checkbox"
                   data-backup-id="${backup._id}" ${isSelected ? "checked" : ""}
                   ${isPlaceholder ? "disabled" : ""}>
          </td>
          <td>
            <i class="bi ${isPlaceholder ? "bi-exclamation-triangle text-warning" : "bi-file-earmark-zip text-primary"}"></i>
            ${filename}
          </td>
          <td>${sizeDisplay}</td>
          <td>${uploadDate}</td>
          <td>${backup.user || "N/A"}</td>
          <td>${actionButtons}</td>
        </tr>
      `;

      $("#driveBackupsTableBody").append(row);
    });

    $("#driveBackupsCount").text(`${backups.length} respaldo${backups.length !== 1 ? 's' : ''}`);

    // Inicializar funcionalidad de selección múltiple
    initializeDriveBackupsSelection();
    updateSelectAllState();

    // Inicializar DataTable para ordenamiento y paginación
    if ($.fn.DataTable) {
      if ($.fn.DataTable.isDataTable('#driveBackupsTable')) {
        $('#driveBackupsTable').DataTable().destroy();
      }

      $('#driveBackupsTable').DataTable({
        "order": [[3, "desc"]], // Ordenar por fecha descendente por defecto
        "pageLength": 25,
        "language": {
          "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
        },
        "columnDefs": [
          { "orderable": false, "targets": [0, 5] }, // Checkbox y acciones no ordenables
          { "type": "num", "targets": 2 } // Tamaño como número
        ]
      });
    }
  }

  // Función para manejar selección múltiple en Google Drive
  function initializeDriveBackupsSelection() {
    // Event listener para el checkbox "Seleccionar todos" en el header
    $(document).off("change", "#selectAllHeader").on("change", "#selectAllHeader", function() {
      const isChecked = $(this).prop("checked");
      $(".backup-checkbox:not(:disabled)").prop("checked", isChecked);
      
      if (isChecked) {
        $(".backup-checkbox:not(:disabled)").each(function() {
          selectedBackups.add($(this).data("backup-id"));
        });
      } else {
        selectedBackups.clear();
      }
      
      updateDeleteButton();
      updateSelectAllState();
    });

    // Event listener para checkboxes individuales
    $(document).off("change", ".backup-checkbox").on("change", ".backup-checkbox", function() {
      const backupId = $(this).data("backup-id");
      if ($(this).prop("checked")) {
        selectedBackups.add(backupId);
      } else {
        selectedBackups.delete(backupId);
      }
      
      updateDeleteButton();
      updateSelectAllState();
    });
  }

  // Función para actualizar el estado del checkbox "Seleccionar todos"
  function updateSelectAllState() {
    const totalCheckboxes = $(".backup-checkbox:not(:disabled)").length;
    const checkedCheckboxes = $(".backup-checkbox:checked").length;
    
    $("#selectAllHeader").prop("checked", totalCheckboxes > 0 && totalCheckboxes === checkedCheckboxes);
    $("#selectAllHeader").prop("indeterminate", checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes);
    $("#selectAllBackups").prop("checked", totalCheckboxes > 0 && totalCheckboxes === checkedCheckboxes);
    $("#selectAllBackups").prop("indeterminate", checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes);
  }



  // Función para actualizar botón de eliminar seleccionados
  function updateDeleteButton() {
    const selectedCount = selectedBackups.size;
    const btn = $("#deleteSelectedBackups");
    const countSpan = $("#selectedCount");

    // Actualizar contador de seleccionados
    if (countSpan.length > 0) {
      countSpan.text(`${selectedCount} seleccionado${selectedCount !== 1 ? 's' : ''}`);
    }

    if (selectedCount > 0) {
      btn.prop("disabled", false).html(`<i class="bi bi-trash"></i> Eliminar ${selectedCount} seleccionado${selectedCount !== 1 ? 's' : ''}`);
    } else {
      btn.prop("disabled", true).html(`<i class="bi bi-trash"></i> Eliminar seleccionados`);
    }
  }



  // Botón de actualizar backups de Google Drive
  $("#refreshDriveBackups").off("click").on("click", function () {
    loadDriveBackups();
  });

  // Evento cuando se abre el modal de Google Drive
  $("#restoreDriveModal").off("shown.bs.modal").on("shown.bs.modal", function () {
    console.log("🔧 Modal de Google Drive abierto, inicializando...");
    // Cargar backups si no se han cargado aún
    if (allBackups.length === 0) {
      loadDriveBackups();
    }
  });

  // Inicializar botones de tareas
  function initializeTaskButtons() {
    console.log("🔧 Inicializando botones de tareas...");

    $(".run-task").each(function (index) {
      const btn = $(this);
      const task = btn.data("task");

      console.log(`🔧 Botón ${index + 1}: data-task="${task}"`);

      // Remover eventos existentes y agregar nuevo
      btn.off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (task) {
          console.log(`🚀 Ejecutando tarea: ${task}`);
          window.runTask(task);
        }
      });
    });
  }

  // Inicializar otros eventos
  function initializeOtherEvents() {
    console.log("🔧 Inicializando otros eventos...");

    // Botón exportar CSV
    $("#exportSystemStatusBtn").off("click").on("click", function (e) {
      e.preventDefault();
      console.log("📊 Exportando estado del sistema...");

      const btn = $(this);
      const originalText = btn.html();

      btn.prop("disabled", true)
        .html("<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span> Exportando...");

      $.ajax({
        url: "/admin/maintenance/export/csv",
        method: "POST",
        xhrFields: { withCredentials: true },
        success: function (response, status, xhr) {
          // Crear enlace temporal para descarga
          const blob = new Blob([response], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;

          // Obtener nombre del archivo del header Content-Disposition
          const contentDisposition = xhr.getResponseHeader('Content-Disposition');
          let filename = 'system_status.csv';
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
              filename = filenameMatch[1].replace(/['"]/g, '');
            }
          }

          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);

          showAlert("Archivo CSV exportado correctamente", "success");
        },
        error: function (xhr, status, error) {
          const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : "Error al exportar CSV";
          showAlert(`Error al exportar CSV: ${errorMsg}`, "danger");
        },
        complete: function () {
          btn.prop("disabled", false).html(originalText);
        }
      });
    });

    // Botón restaurar
    $("#restoreBtn").off("click").on("click", function (e) {
      e.preventDefault();
      $("#restoreFileInput").click();
    });

    // Manejo de archivo de restauración
    $("#restoreFileInput").off("change").on("change", function (e) {
      const file = e.target.files[0];
      if (!file) return;

      if (!file.name.toLowerCase().endsWith(".json") && !file.name.toLowerCase().endsWith(".gz")) {
        showAlert("Tipo de archivo inválido. Seleccione un archivo .json o .gz", "danger");
        return;
      }

      showAlert("Iniciando restauración desde archivo local...", "info");
    });

    // Modal de backups locales
    $("#localBackupsModal").off("show.bs.modal").on("show.bs.modal", function () {
      console.log("🔵 Modal de backups locales abriéndose - SIMPLIFICADO");
      // Cargar backups inmediatamente
      loadLocalBackups();
    });

    // Botón actualizar backups locales
    $("#refreshLocalBackups").off("click").on("click", function () {
      console.log("🔄 Actualizando lista de backups locales...");
      loadLocalBackups();
    });
  }

  // Función para cargar backups locales
  function loadLocalBackups() {
    console.log("🔄 Cargando backups locales... - SIMPLIFICADO");
    console.log("🔍 Elementos del modal:", {
      loading: $("#localBackupsLoading").length,
      content: $("#localBackupsContent").length,
      empty: $("#localBackupsEmpty").length,
      error: $("#localBackupsError").length,
      tableBody: $("#localBackupsTableBody").length
    });

    $("#localBackupsLoading").show();
    $("#localBackupsContent").hide();
    $("#localBackupsEmpty").hide();
    $("#localBackupsError").hide();
    $("#localBackupsTableBody").empty();

    $.ajax({
      url: "/admin/maintenance/local-backups",
      method: "GET",
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log("📥 Respuesta de backups locales recibida:", response);
        $("#localBackupsLoading").hide();

        if (response.success && response.backups && response.backups.length > 0) {
          displayLocalBackups(response.backups);
          $("#localBackupsContent").show();
          // Inicializar acciones masivas después de mostrar los backups
          initializeLocalBackupsMassiveActions();
        } else {
          $("#localBackupsEmpty").show();
          $("#localBackupsCount").text("0 backups");
        }
      },
      error: function (xhr, status, error) {
        console.error("❌ Error cargando backups locales:", xhr.status, xhr.statusText, error);
        $("#localBackupsLoading").hide();
        $("#localBackupsError").show();
        $("#localBackupsErrorMessage").text(`Error: ${xhr.statusText || "Error de conexión"}`);
      }
    });
  }

  // Función para mostrar backups locales
  function displayLocalBackups(backups) {
    $("#localBackupsTableBody").empty();

    backups.forEach(function (backup) {
      const sizeDisplay = backup.size_mb ? `${backup.size_mb} MB` : "N/A";
      const modifiedDate = backup.modified_at ? new Date(backup.modified_at).toLocaleString() : "N/A";

      const actionButtons = `
        <div class="btn-group" role="group">
          <button class="btn btn-sm btn-primary view-local-backup"
                  data-filename="${backup.filename}"
                  title="Ver detalles">
            <i class="bi bi-eye"></i> Ver
          </button>
          <button class="btn btn-sm btn-success upload-local-backup"
                  data-filename="${backup.filename}"
                  title="Subir a Google Drive">
            <i class="bi bi-cloud-upload"></i> Subir
          </button>
          <button class="btn btn-sm btn-danger delete-local-backup"
                  data-filename="${backup.filename}"
                  title="Eliminar backup">
            <i class="bi bi-trash"></i> Eliminar
          </button>
        </div>
      `;

      const row = `
        <tr data-backup-filename="${backup.filename}">
          <td>
            <input type="checkbox" class="form-check-input local-backup-checkbox" data-filename="${backup.filename}">
          </td>
          <td>
            <i class="bi bi-file-earmark-zip text-primary"></i>
            ${backup.filename}
          </td>
          <td>${sizeDisplay}</td>
          <td>${modifiedDate}</td>
          <td>${actionButtons}</td>
        </tr>
      `;

      $("#localBackupsTableBody").append(row);
    });

    $("#localBackupsCount").text(`${backups.length} backup${backups.length !== 1 ? 's' : ''}`);
    updateLocalBackupsSelectionUI();

    // Inicializar DataTable para ordenamiento
    if ($.fn.DataTable) {
      if ($.fn.DataTable.isDataTable('#localBackupsTable')) {
        $('#localBackupsTable').DataTable().destroy();
      }

      $('#localBackupsTable').DataTable({
        "order": [[3, "desc"]], // Ordenar por fecha descendente por defecto
        "pageLength": 25,
        "language": {
          "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
        },
        "columnDefs": [
          { "orderable": false, "targets": [0, 4] }, // Checkbox y acciones no ordenables
          { "type": "num", "targets": 2 } // Tamaño como número
        ]
      });
    }
  }

  // Función para actualizar UI de selección
  function updateLocalBackupsSelectionUI() {
    const totalCheckboxes = $(".local-backup-checkbox").length;
    const checkedCheckboxes = $(".local-backup-checkbox:checked").length;

    $("#selectedLocalBackupsCount").text(`${checkedCheckboxes} seleccionado${checkedCheckboxes !== 1 ? 's' : ''}`);

    // Habilitar/deshabilitar botones masivos
    $("#uploadSelectedLocalBackups, #deleteSelectedLocalBackups").prop("disabled", checkedCheckboxes === 0);

    // Actualizar checkbox "Seleccionar todos"
    const selectAllCheckbox = $("#selectAllLocalBackupsCheckbox");
    if (checkedCheckboxes === 0) {
      selectAllCheckbox.prop("indeterminate", false).prop("checked", false);
    } else if (checkedCheckboxes === totalCheckboxes) {
      selectAllCheckbox.prop("indeterminate", false).prop("checked", true);
    } else {
      selectAllCheckbox.prop("indeterminate", true);
    }
  }

  // Eventos para selección múltiple
  $(document).on("change", "#selectAllLocalBackupsCheckbox", function () {
    const isChecked = $(this).prop("checked");
    $(".local-backup-checkbox").prop("checked", isChecked);
    updateLocalBackupsSelectionUI();
  });

  $(document).on("change", ".local-backup-checkbox", function () {
    updateLocalBackupsSelectionUI();
  });

  // Botones de selección masiva
  $("#selectAllLocalBackups").on("click", function () {
    $(".local-backup-checkbox").prop("checked", true);
    updateLocalBackupsSelectionUI();
  });

  $("#deselectAllLocalBackups").on("click", function () {
    $(".local-backup-checkbox").prop("checked", false);
    updateLocalBackupsSelectionUI();
  });

  // Acciones masivas - Se registrarán cuando el modal se abra
  function initializeLocalBackupsMassiveActions() {
    console.log("🔧 Inicializando acciones masivas de backups locales...");

    // Verificar que los elementos existan antes de registrar eventos
    const uploadBtn = $("#uploadSelectedLocalBackups");
    const deleteBtn = $("#deleteSelectedLocalBackups");

    if (uploadBtn.length === 0) {
      console.warn("⚠️ Botón uploadSelectedLocalBackups no encontrado");
      return;
    }

    if (deleteBtn.length === 0) {
      console.warn("⚠️ Botón deleteSelectedLocalBackups no encontrado");
      return;
    }

    uploadBtn.off("click").on("click", async function () {
      console.log("☁️ Botón subir seleccionados clickeado");
      const selectedFiles = $(".local-backup-checkbox:checked").map(function () {
        return $(this).data("filename");
      }).get();

      if (selectedFiles.length === 0) {
        showAlert("No hay backups seleccionados", "warning");
        return;
      }

      const fileList = selectedFiles.join("\n• ");
      const confirmed = await showConfirmDialog(
        "Confirmar Subida Masiva",
        `¿Estás seguro de que quieres subir ${selectedFiles.length} backup${selectedFiles.length !== 1 ? 's' : ''} a Google Drive?\n\nArchivos seleccionados:\n• ${fileList}`,
        "warning"
      );

      if (!confirmed) {
        console.log("❌ Subida masiva cancelada por el usuario");
        return;
      }

      console.log("🚀 Iniciando subida masiva de backups...");
      uploadMultipleLocalBackups(selectedFiles);
    });

    deleteBtn.off("click").on("click", async function () {
      console.log("🗑️ Botón eliminar seleccionados clickeado");
      const selectedFiles = $(".local-backup-checkbox:checked").map(function () {
        return $(this).data("filename");
      }).get();

      if (selectedFiles.length === 0) {
        showAlert("No hay backups seleccionados", "warning");
        return;
      }

      const fileList = selectedFiles.join("\n• ");
      const confirmed = await showConfirmDialog(
        "Confirmar Eliminación Masiva",
        `¿Estás seguro de que quieres eliminar ${selectedFiles.length} backup${selectedFiles.length !== 1 ? 's' : ''}?\n\n⚠️ Esta acción no se puede deshacer.\n\nArchivos seleccionados:\n• ${fileList}`,
        "danger"
      );

      if (!confirmed) {
        console.log("❌ Eliminación masiva cancelada por el usuario");
        return;
      }

      console.log("🚀 Iniciando eliminación masiva de backups...");
      deleteMultipleLocalBackups(selectedFiles);
    });

    console.log("✅ Acciones masivas inicializadas correctamente");
  }

  // Función para subir múltiples backups
  function uploadMultipleLocalBackups(filenames) {
    const btn = $("#uploadSelectedLocalBackups");
    const originalText = btn.html();

    btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Subiendo...");

    let completed = 0;
    let successCount = 0;
    let errorCount = 0;
    const errors = [];

    filenames.forEach(function (filename) {
      $.ajax({
        url: `/admin/maintenance/local-backups/upload-to-drive/${filename}`,
        method: "POST",
        xhrFields: { withCredentials: true },
        success: function (response) {
          if (response.success) {
            successCount++;
          } else {
            errorCount++;
            errors.push(`${filename}: ${response.error}`);
          }
        },
        error: function (xhr) {
          errorCount++;
          const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error desconocido";
          errors.push(`${filename}: ${errorMsg}`);
        },
        complete: function () {
          completed++;
          if (completed === filenames.length) {
            btn.prop("disabled", false).html(originalText);

            if (errorCount === 0) {
              showModalAlert(`✅ ${successCount} backup${successCount !== 1 ? 's' : ''} subido${successCount !== 1 ? 's' : ''} correctamente a Google Drive`, "success");
            } else {
              const errorMsg = errors.join("\n");
              showModalAlert(`⚠️ Subida completada con errores:\n\n${errorMsg}`, "warning");
            }
          }
        }
      });
    });
  }

  // Función para eliminar múltiples backups
  function deleteMultipleLocalBackups(filenames) {
    const btn = $("#deleteSelectedLocalBackups");
    const originalText = btn.html();

    btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Eliminando...");

    let completed = 0;
    let successCount = 0;
    let errorCount = 0;
    const errors = [];

    filenames.forEach(function (filename) {
      $.ajax({
        url: `/admin/maintenance/local-backups/delete/${filename}`,
        method: "DELETE",
        xhrFields: { withCredentials: true },
        success: function (response) {
          if (response.success) {
            successCount++;
          } else {
            errorCount++;
            errors.push(`${filename}: ${response.error}`);
          }
        },
        error: function (xhr) {
          errorCount++;
          const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error desconocido";
          errors.push(`${filename}: ${errorMsg}`);
        },
        complete: function () {
          completed++;
          if (completed === filenames.length) {
            btn.prop("disabled", false).html(originalText);

            if (errorCount === 0) {
              showModalAlert(`✅ ${successCount} backup${successCount !== 1 ? 's' : ''} eliminado${successCount !== 1 ? 's' : ''} correctamente`, "success");
              loadLocalBackups(); // Recargar lista
            } else {
              const errorMsg = errors.join("\n");
              showModalAlert(`⚠️ Eliminación completada con errores:\n\n${errorMsg}`, "warning");
              loadLocalBackups(); // Recargar lista
            }
          }
        }
      });
    });
  }

  // Eventos para acciones individuales de backups locales
  $(document).on("click", ".view-local-backup", function (e) {
    e.preventDefault();
    e.stopPropagation();
    const filename = $(this).data("filename");
    console.log("🔍 Vista previa de backup:", filename);
    showLocalBackupPreview(filename);
  });

  $(document).on("click", ".upload-local-backup", async function (e) {
    e.preventDefault();
    e.stopPropagation();
    const filename = $(this).data("filename");
    console.log("☁️ Subiendo backup individual:", filename);

    const confirmed = await showConfirmDialog(
      "Confirmar Subida",
      `¿Estás seguro de que quieres subir el backup "${filename}" a Google Drive?`,
      "warning"
    );

    if (!confirmed) {
      console.log("❌ Subida cancelada por el usuario");
      return;
    }

    const btn = $(this);
    const originalText = btn.html();

    if (btn.prop("disabled")) {
      console.log("⚠️ Botón ya deshabilitado, saltando...");
      return;
    }

    console.log("🚀 Iniciando subida de backup individual...");
    btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Subiendo...");

    $.ajax({
      url: `/admin/maintenance/local-backups/upload-to-drive/${filename}`,
      method: "POST",
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log("✅ Respuesta de subida individual:", response);
        if (response.success) {
          showModalAlert(`✅ ${response.message}`, "success");
        } else {
          showModalAlert(`❌ Error al subir: ${response.error}`, "danger");
        }
      },
      error: function (xhr) {
        console.error("❌ Error en subida individual:", xhr);
        const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error desconocido";
        showModalAlert(`❌ Error al subir backup: ${errorMsg}`, "danger");
      },
      complete: function () {
        btn.prop("disabled", false).html(originalText);
      }
    });
  });

  $(document).on("click", ".delete-local-backup", async function (e) {
    e.preventDefault();
    e.stopPropagation();
    const filename = $(this).data("filename");
    console.log("🗑️ Eliminando backup individual:", filename);

    const confirmed = await showConfirmDialog(
      "Confirmar Eliminación",
      `¿Estás seguro de que quieres eliminar el backup "${filename}"?\n\n⚠️ Esta acción no se puede deshacer.`,
      "danger"
    );

    if (!confirmed) {
      console.log("❌ Eliminación cancelada por el usuario");
      return;
    }

    const btn = $(this);
    const originalText = btn.html();

    if (btn.prop("disabled")) {
      console.log("⚠️ Botón ya deshabilitado, saltando...");
      return;
    }

    console.log("🚀 Iniciando eliminación de backup individual...");
    btn.prop("disabled", true).html("<span class=\"spinner-border spinner-border-sm\"></span> Eliminando...");

    $.ajax({
      url: `/admin/maintenance/local-backups/delete/${filename}`,
      method: "DELETE",
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log("✅ Respuesta de eliminación individual:", response);
        if (response.success) {
          showModalAlert(`✅ ${response.message}`, "success");
          loadLocalBackups(); // Recargar lista
        } else {
          showModalAlert(`❌ Error al eliminar: ${response.error}`, "danger");
        }
      },
      error: function (xhr) {
        console.error("❌ Error en eliminación individual:", xhr);
        const errorMsg = xhr.responseJSON?.error || xhr.statusText || "Error desconocido";
        showModalAlert(`❌ Error al eliminar backup: ${errorMsg}`, "danger");
      },
      complete: function () {
        btn.prop("disabled", false).html(originalText);
      }
    });
  });

  // Función para mostrar vista previa de backup
  function showLocalBackupPreview(filename) {
    // Por ahora, mostrar información básica
    const row = $(`tr[data-backup-filename="${filename}"]`);
    const size = row.find("td:eq(2)").text();
    const date = row.find("td:eq(3)").text();

    const previewContent = `
      <div class="alert alert-info">
        <h6><i class="bi bi-file-earmark-zip"></i> ${filename}</h6>
        <p><strong>Tamaño:</strong> ${size}</p>
        <p><strong>Fecha de modificación:</strong> ${date}</p>
        <p><strong>Ubicación:</strong> Directorio local de backups</p>
        <hr>
        <p class="mb-0"><small>La vista previa completa del contenido del backup estará disponible en futuras versiones.</small></p>
      </div>
    `;

    // Crear modal temporal para la vista previa
    const modal = $(`
      <div class="modal fade" id="backupPreviewModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">
                <i class="bi bi-eye"></i> Vista Previa: ${filename}
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              ${previewContent}
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
            </div>
          </div>
        </div>
      </div>
    `);

    // Remover modal anterior si existe
    $("#backupPreviewModal").remove();

    // Agregar y mostrar el nuevo modal
    $("body").append(modal);
    const bsModal = new bootstrap.Modal(document.getElementById('backupPreviewModal'));
    bsModal.show();

    // Limpiar modal al cerrar
    $("#backupPreviewModal").off("hidden.bs.modal").on("hidden.bs.modal", function () {
      $(this).remove();
    });
  }

  // Función para cargar estado del sistema
  function loadSystemStatus() {
    $.ajax({
      url: "/admin/api/system_status",
      method: "GET",
      success: function (data) {
        if (data.system_status) {
          const system = data.system_status;

          // Actualizar memoria
          if (system.memory_usage) {
            const mem = system.memory_usage;
            $("#memoriaUsage").css("width", `${mem.percent || 0}%`).text(`${mem.percent || 0}%`);
            $("#memTotal").text(mem.total_gb || (mem.total_mb / 1024).toFixed(2));
            $("#memDisponible").text(mem.available_gb || (mem.available_mb / 1024).toFixed(2));
          }

          // Actualizar CPU
          if (system.cpu_usage !== undefined) {
            $("#cpuUsage").css("width", `${system.cpu_usage}%`).text(`${system.cpu_usage}%`);
          }

          // Actualizar detalles del sistema
          if (system.system_details) {
            const details = system.system_details;
            $("#so").text(details.os || "N/A");
            $("#arquitectura").text(details.arch || "N/A");
            $("#usuario").text(details.user || "N/A");
            $("#hora").text(new Date().toLocaleString());
          }
        }
      },
      error: function () {
        console.error("Error al cargar estado del sistema");
      }
    });
  }

  // Inicialización principal
  function initializeDashboard() {
    console.log("🔧 Inicializando dashboard completo...");

    // Inicializar todos los eventos
    initializeTaskButtons();
    initializeOtherEvents();
    initializeBackupEvents();
    window.initializeGoogleDriveEvents();

    // Cargar estado del sistema
    loadSystemStatus();

    // Actualizar estado del sistema cada 30 segundos
    setInterval(loadSystemStatus, 30000);

    // Eliminar duplicados cada 2 segundos como medida de seguridad
    setInterval(removeDuplicateAlerts, 2000);

    console.log("✅ Dashboard inicializado correctamente");
  }

  // Esperar a que los elementos estén disponibles
  function waitForElements() {
    const maxAttempts = 20;
    let attempts = 0;

    function checkElements() {
      attempts++;
      console.log(`🔍 Verificando elementos (${attempts}/${maxAttempts})...`);

      const runTaskButtons = $(".run-task");
      const backupBtn = $("#backupBtn");
      const exportBtn = $("#exportSystemStatusBtn");

      if (runTaskButtons.length > 0 || backupBtn.length > 0 || exportBtn.length > 0) {
        console.log("✅ Elementos encontrados, inicializando...");
        initializeDashboard();
        return;
      }

      if (attempts >= maxAttempts) {
        console.warn("⚠️ Timeout alcanzado, inicializando con elementos disponibles...");
        initializeDashboard();
        return;
      }

      setTimeout(checkElements, 500);
    }

    checkElements();
  }

  // Iniciar verificación de elementos
  waitForElements();
});