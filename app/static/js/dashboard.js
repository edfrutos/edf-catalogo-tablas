// JavaScript del dashboard de mantenimiento extraído desde dashboard.html
// Asegúrate de revisar rutas AJAX si alguna debe cambiar

$(function () {
  // --- Helpers ---
  function getTaskCellId(task) {
    switch (task) {
      case "cleanup":
        return "lastCleanupRun";
      case "mongo":
        return "lastMongoCheck";
      case "disk":
        return "lastDiskCheck";
      default:
        return "";
    }
  }
  function getTaskName(task) {
    const tasks = {
      cleanup: "Limpieza de Logs",
      mongo: "Verificación MongoDB",
      disk: "Verificación Disco",
    };
    return tasks[task] || task;
  }
  function showError(title, message) {
    $("#cleanupAlert")
      .removeClass("alert-success")
      .addClass("alert-danger").html(`
        <h5><i class="bi bi-exclamation-triangle-fill"></i> ${title}</h5>
        <p class="mb-0">${message}</p>
      `);
  }
  function showAlert(message, type = "success") {
    const alert = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
      </div>
    `;
    $(".container").prepend(alert);
    setTimeout(function () {
      $(".alert").alert("close");
    }, 5000);
  }
  // =============================
  // 1. TAREAS DE MANTENIMIENTO
  // =============================
  function runTask(task) {
    const btn = $(`.run-task[data-task="${task}"]`);
    const originalText = btn.html();
    const cellId = getTaskCellId(task);
    btn
      .prop("disabled", true)
      .html(
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Ejecutando...'
      );
    if (cellId) {
      $(`#${cellId}`).text("Ejecutando...");
    }
    $.post("/admin/maintenance/api/run_task", { task: task })
      .done(function (response) {
        const now = new Date();
        if (cellId) {
          $(`#${cellId}`).text(now.toLocaleString());
        }
        $(`td:contains("${getTaskName(task)}")`)
          .next()
          .next()
          .find(".badge")
          .removeClass("bg-secondary bg-danger")
          .addClass("bg-success")
          .text("Completado");
        let customMsg = "";
        if (task === "mongo") {
          customMsg = `<strong>Verificación MongoDB completada exitosamente</strong> (${now.toLocaleString()})`;
        } else if (task === "disk") {
          customMsg = `<strong>Verificación Disco completada exitosamente</strong> (${now.toLocaleString()})`;
        } else {
          customMsg = `Tarea "${getTaskName(
            task
          )}" ejecutada correctamente (${now.toLocaleString()})`;
        }
        $("#taskResult")
          .html(
            `
          <div class="alert alert-success alert-dismissible fade show mt-3" role="alert">
            ${customMsg}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
          </div>
        `
          )
          .show();
        setTimeout(function () {
          $("#taskResult").fadeOut();
        }, 4000);
      })
      .fail(function (xhr) {
        let msg = "Error al ejecutar la tarea";
        if (xhr.responseJSON && xhr.responseJSON.message) {
          msg = xhr.responseJSON.message;
        }
        if (cellId) {
          $(`#${cellId}`).text("Error");
        }
        $(`td:contains("${getTaskName(task)}")`)
          .next()
          .next()
          .find(".badge")
          .removeClass("bg-success bg-secondary")
          .addClass("bg-danger")
          .text("Error");
        $("#taskResult")
          .html(
            `
          <div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
            ${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
          </div>
        `
          )
          .show();
        setTimeout(function () {
          $("#taskResult").fadeOut();
        }, 4000);
      })
      .always(function () {
        btn.html(originalText).prop("disabled", false);
      });
  }

  // =============================
  // 2. BACKUP Y RESTORE
  // =============================
  $("#backupBtn")
    .off("click")
    .on("click", function () {
      const btn = $(this);
      btn
        .prop("disabled", true)
        .html(
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generando...'
        );
      $.ajax({
        url: "/admin/maintenance/api/backup",
        method: "POST",
        success: function (response) {
          if (response.status === "success" && response.download_url) {
            showAlert(
              "Backup generado correctamente. Iniciando descarga...",
              "success"
            );
            window.location.href = response.download_url;
          } else if (response.download_url && response.status !== "success") {
            showAlert(
              "Backup generado pero con advertencia. Descargando...",
              "warning"
            );
            window.location.href = response.download_url;
          } else {
            showAlert(
              "Error al generar el backup: " +
                (response.message || JSON.stringify(response)),
              "danger"
            );
          }
        },
        error: function (xhr) {
          let msg = "Error al generar el backup: ";
          if (xhr.responseJSON && xhr.responseJSON.message)
            msg += xhr.responseJSON.message;
          else if (xhr.responseText) msg += xhr.responseText;
          else msg += xhr.statusText;
          showAlert(msg, "danger");
        },
        complete: function () {
          btn
            .prop("disabled", false)
            .html('<i class="bi bi-cloud-arrow-up"></i> Realizar Backup');
        },
      });
    });

  // Restore: input file oculto y subida AJAX
  if ($("#restoreFileInput").length === 0) {
    $("body").append(
      '<input type="file" id="restoreFileInput" style="display:none" accept=".gz,.json,.csv,.zip">'
    );
  }
  $("#restoreBtn")
    .off("click")
    .on("click", function () {
      $("#restoreFileInput").val("").click();
    });
  $(document)
    .off("change", "#restoreFileInput")
    .on("change", "#restoreFileInput", function () {
      const file = this.files[0];
      if (!file) return;
      const btn = $("#restoreBtn");
      btn
        .prop("disabled", true)
        .html(
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Restaurando...'
        );
      const formData = new FormData();
      formData.append("backup_file", file);
      $.ajax({
        url: "/admin/maintenance/api/restore",
        method: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
          if (response.status === "success") {
            showAlert("Restauración completada correctamente.", "success");
          } else {
            showAlert(
              "Error en la restauración: " +
                (response.message || "Error desconocido"),
              "danger"
            );
          }
        },
        error: function (xhr) {
          showAlert(
            "Error en la restauración: " +
              (xhr.responseJSON?.message || xhr.statusText),
            "danger"
          );
        },
        complete: function () {
          btn
            .prop("disabled", false)
            .html('<i class="bi bi-arrow-counterclockwise"></i> Restaurar Backup');
        },
      });
    });

  // Restore desde Google Drive
  if ($("#restoreDriveBtn").length === 0) {
    $("#restoreBtn").after(
      '<button class="btn btn-outline-success ms-2" id="restoreDriveBtn"><i class="bi bi-google-drive"></i> Google Drive</button>'
    );
  }
  if ($("#restoreDriveModal").length === 0) {
    $("body").append(`
      <div class="modal fade" id="restoreDriveModal" tabindex="-1" aria-labelledby="restoreDriveModalLabel" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="restoreDriveModalLabel">Restaurar desde Google Drive</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
            </div>
            <div class="modal-body">
              <label for="driveUrlInput">Pega la URL del archivo de backup en Google Drive:</label>
              <input type="url" class="form-control" id="driveUrlInput" placeholder="https://drive.google.com/file/d/.../view?usp=sharing">
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
              <button type="button" class="btn btn-success" id="confirmRestoreDriveBtn">Restaurar</button>
            </div>
          </div>
        </div>
      </div>
    `);
  }
  $("#restoreDriveBtn")
    .off("click")
    .on("click", function () {
      $("#driveUrlInput").val("");
      var modal = new bootstrap.Modal(
        document.getElementById("restoreDriveModal")
      );
      modal.show();
    });
  $("#confirmRestoreDriveBtn")
    .off("click")
    .on("click", function () {
      const url = $("#driveUrlInput").val();
      if (!url || !/^https:\/\/drive\.google\.com\//.test(url)) {
        showAlert("Introduce una URL válida de Google Drive.", "warning");
        return;
      }
      const btn = $("#restoreDriveBtn");
      btn
        .prop("disabled", true)
        .html(
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Restaurando...'
        );
      $.ajax({
        url: "/admin/maintenance/api/restore",
        method: "POST",
        data: { drive_url: url },
        success: function (response) {
          if (response.status === "success") {
            showAlert("Restauración desde Google Drive completada.", "success");
            var modalEl = document.getElementById("restoreDriveModal");
            if (modalEl) bootstrap.Modal.getInstance(modalEl).hide();
          } else {
            showAlert(
              "Error en la restauración: " +
                (response.message || "Error desconocido"),
              "danger"
            );
          }
        },
        error: function (xhr) {
          showAlert(
            "Error en la restauración: " +
              (xhr.responseJSON?.message || xhr.statusText),
            "danger"
          );
        },
        complete: function () {
          btn
            .prop("disabled", false)
            .html('<i class="bi bi-google-drive"></i> Google Drive');
        },
      });
    });

  // =============================
  // 3. LOGS: CARGA Y VISUALIZACIÓN
  // =============================
  function getLogFileName(logType) {
    const now = new Date();
    let logFile = "";
    switch (logType) {
      case "yesterday":
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        logFile = `maintenance_${yesterday
          .toISOString()
          .split("T")[0]
          .replace(/-/g, "")}.log`;
        break;
      case "week":
        logFile = "maintenance_week.log";
        break;
      case "today":
      default:
        logFile = `maintenance_${now
          .toISOString()
          .split("T")[0]
          .replace(/-/g, "")}.log`;
    }
    return logFile;
  }

  function loadLogs() {
    $.get("/admin/maintenance/api/list_logs", function (data) {
      const select = $("#logFileSelect");
      select.empty();
      if (data && Array.isArray(data.listado_archivos)) {
        if (data.listado_archivos.length === 0) {
          select.append('<option value="">(No hay archivos de log)</option>');
        } else {
          data.listado_archivos.forEach(function (file) {
            select.append(`<option value="${file}">${file}</option>`);
          });
        }
      }
    });
  }

  $("#logFileSelect").on("change", function () {
    const logFile = $(this).val();
    if (!logFile) {
      $("#logPreview").text("Por favor selecciona un archivo de log.");
      return;
    }
    $("#logPreview").text("Cargando registros...");
    $.get(
      `/admin/maintenance/logs/view?file=${encodeURIComponent(logFile)}`,
      function (data) {
        if (data && data.status === "success") {
          $("#logPreview").text(data.content || "El archivo de log está vacío");
        } else if (data && data.message) {
          $("#logPreview").text(
            `Error al cargar el archivo de log: ${data.message}`
          );
        } else {
          $("#logPreview").text(
            "Error desconocido al cargar el archivo de log."
          );
        }
      }
    ).fail(function () {
      $("#logPreview").text("No se pudo cargar el archivo de log");
    });
  });

  $("#refreshLogs").on("click", function () {
    loadLogs();
  });

  // Inicialización de logs al abrir el modal
  $("#logsModal").on("show.bs.modal", function () {
    loadLogs();
  });

  // =============================
  // 4. LIMPIEZA DE ARCHIVOS TEMPORALES
  // =============================
  $("#runCleanupBtn").on("click", function () {
    const btn = $(this);
    const originalText = btn.html();
    let days = $("#daysToKeep").val().trim();
    days = parseInt(days, 10);
    const useDateRange = $("#useDateRange").is(":checked");
    const startDate = $("#startDate").val();
    const endDate = $("#endDate").val();
    $("#cleanupAlert").removeClass("alert-success alert-danger").html("");
    let dataToSend = {};
    if (useDateRange) {
      if (!startDate || !endDate) {
        $("#cleanupAlert")
          .removeClass("alert-success")
          .addClass("alert-danger")
          .html(
            `<h5><i class="bi bi-exclamation-triangle-fill"></i> Debes indicar fecha/hora de inicio y fin.</h5>`
          );
        return;
      }
      dataToSend["start_datetime"] = startDate;
      dataToSend["end_datetime"] = endDate;
    } else {
      if (!days || isNaN(days) || days <= 0) {
        $("#cleanupAlert")
          .removeClass("alert-success")
          .addClass("alert-danger")
          .html(
            `<h5><i class="bi bi-exclamation-triangle-fill"></i> Debes indicar un número de días válido.</h5>`
          );
        return;
      }
      dataToSend["days"] = days;
    }
    btn
      .prop("disabled", true)
      .html(
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Ejecutando...'
      );
    $("#cleanupResult").hide();
    $.ajax({
      url: "/admin/maintenance/api/cleanup-temp",
      method: "POST",
      data: JSON.stringify(dataToSend),
      contentType: "application/json",
      success: function (response) {
        if (response.status === "success") {
          $("#cleanupAlert")
            .removeClass("alert-danger")
            .addClass("alert-success")
            .html(
              `<h5><i class="bi bi-check-circle-fill"></i> Limpieza completada exitosamente</h5><pre class="mt-2 mb-0">${
                response.output || "No hay salida"
              }</pre>`
            );
        } else {
          $("#cleanupAlert")
            .removeClass("alert-success")
            .addClass("alert-danger")
            .html(
              `<h5><i class="bi bi-exclamation-triangle-fill"></i> Error en la limpieza</h5><pre class="mt-2 mb-0">${
                response.message || "Error desconocido"
              }</pre>`
            );
        }
      },
      error: function (xhr) {
        $("#cleanupAlert")
          .removeClass("alert-success")
          .addClass("alert-danger")
          .html(
            `<h5><i class="bi bi-exclamation-triangle-fill"></i> Error de conexión</h5><pre class="mt-2 mb-0">${
              xhr.responseJSON?.message ||
              xhr.statusText ||
              "No se pudo conectar al servidor."
            }</pre>`
          );
      },
      complete: function () {
        btn.prop("disabled", false).html(originalText);
      },
    });
  });

  // =============================
  // 5. UX: Dropdowns y Scroll
  // =============================
  var serviciosDropdown = document.getElementById("serviciosDropdown");
  document
    .querySelectorAll('.dropdown-menu .dropdown-item[href^="#"]')
    .forEach(function (link) {
      link.addEventListener("click", function (e) {
        var target = document.querySelector(this.getAttribute("href"));
        if (target) {
          e.preventDefault();
          var y = target.getBoundingClientRect().top + window.pageYOffset - 60;
          window.scrollTo({ top: y, behavior: "smooth" });
          // Cierra solo el menú de servicios si corresponde
          if (
            serviciosDropdown &&
            this.closest(".dropdown-menu").previousElementSibling ===
              serviciosDropdown &&
            typeof bootstrap !== "undefined" &&
            bootstrap.Dropdown
          ) {
            var dropdown =
              bootstrap.Dropdown.getOrCreateInstance(serviciosDropdown);
            dropdown.hide();
          }
        }
      });
    });

  // =============================
  // 6. Inicialización de datepickers
  // =============================
  $("#startDate, #endDate").prop("disabled", false);
  if (window.flatpickr) {
    flatpickr("#startDate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      time_24hr: true,
    });
    flatpickr("#endDate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      time_24hr: true,
    });
  } else {
    $("#startDate, #endDate").attr("type", "datetime-local");
  }

  // =============================
  // 7. Inicialización de sistema al cargar la página
  // =============================
  // =============================
  // 8. TAREAS PROGRAMADAS
  // =============================
  function loadScheduledTasks() {
    $.get("/admin/maintenance/api/scheduled_tasks", function (data) {
      if (data && Array.isArray(data.tasks)) {
        data.tasks.forEach(function (task) {
          const row = $(
            `#scheduledTasks button[data-task="${task.id}"]`
          ).closest("tr");
          row
            .find(".badge")
            .removeClass("bg-secondary bg-success bg-danger")
            .addClass(
              task.estado === "OK"
                ? "bg-success"
                : task.estado === "ERROR"
                ? "bg-danger"
                : "bg-secondary"
            )
            .text(task.estado);
          row.find(".last-run").text(task.ultima_ejecucion || "-");
        });
      }
    });
  }

  // Añade tooltips a los botones (Bootstrap 5)
  $(document).ready(function () {
    $('[data-bs-toggle="tooltip"]').tooltip();
  });

  $("#scheduledTasks").on("click", ".run-task", function () {
    const btn = $(this);
    const task = btn.data("task");
    // Deshabilita todos los botones mientras se ejecuta una tarea
    $(".run-task").prop("disabled", true);
    btn.html(
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Ejecutando...'
    );
    const $alert = $("#taskResult");
    $alert.hide().attr("aria-live", "polite");
    $.post("/admin/maintenance/api/run_task", { task: task }, function (data) {
      // Restaura todos los botones
      $(".run-task")
        .prop("disabled", false)
        .html('<i class="bi bi-play"></i> Ejecutar Ahora');
      $alert
        .show()
        .removeClass("alert-success alert-danger")
        .addClass(data.status === "success" ? "alert-success" : "alert-danger")
        .html(
          `<strong>${data.status === "success" ? "Éxito" : "Error"}:</strong> ${
            data.message
          }`
        )
        .focus();
      loadScheduledTasks();
    }).fail(function (xhr) {
      let errorMsg = "<strong>Error:</strong> No se pudo ejecutar la tarea.";
      // Si la respuesta es JSON, intenta mostrar el mensaje real del backend
      try {
        const data = JSON.parse(xhr.responseText);
        if (data && data.message) {
          errorMsg = `<strong>Error:</strong> ${data.message}`;
        }
      } catch (e) {}
      console.error(
        "Error ejecutando tarea:",
        xhr.status,
        xhr.statusText,
        xhr.responseText
      );
      $(".run-task")
        .prop("disabled", false)
        .html('<i class="bi bi-play"></i> Ejecutar Ahora');
      $alert
        .show()
        .removeClass("alert-success")
        .addClass("alert-danger")
        .html(errorMsg)
        .focus();
    });
  });

  // Inicializa estados al cargar
  loadScheduledTasks();

// =============================
// 7. ESTADO DEL SISTEMA
// =============================
function loadSystemStatus() {
  $.get("/admin/maintenance/api/system_status", function (data) {
    if (data && data.status === "success") {
      var porcentaje =
        data.memoria && typeof data.memoria.porcentaje !== "undefined"
          ? parseFloat(data.memoria.porcentaje) || 0
          : 0;
      $("#memoriaUsage")
        .css("width", porcentaje + "%")
        .text(porcentaje + "%");
      $("#memTotal").text(data.memoria.total_gb);
      $("#memDisponible").text(data.memoria.disponible_gb);
      $("#so").text(data.so);
      $("#arquitectura").text(data.arquitectura);
      $("#usuario").text(data.usuario);
      $("#hora").text(data.hora);
    } else {
      $("#systemStatus").find("span,div.progress-bar").text("Error");
    }
  }).fail(function () {
    $("#systemStatus")
      .find("span,div.progress-bar")
      .text("Error de conexión");
  });
}

if (typeof loadSystemStatus === "function") {
  loadSystemStatus();
}

$("#exportSystemStatusBtn").click(function () {
  exportSystemStatus();
});

function exportSystemStatus() {
  // Recoge los valores actuales de la UI
  const data = [
    ["Campo", "Valor"],
    ["Uso de memoria (%)", $("#memoriaUsage").text()],
    ["Memoria total (GB)", $("#memTotal").text()],
    ["Memoria disponible (GB)", $("#memDisponible").text()],
    ["SO", $("#so").text()],
    ["Arquitectura", $("#arquitectura").text()],
    ["Usuario", $("#usuario").text()],
    ["Hora", $("#hora").text()],
  ];
  // Convierte a CSV
  const csvContent = data
    .map((row) =>
      row.map((cell) => '"' + cell.replaceAll('"', '""') + '"').join(",")
    )
    .join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "estado_sistema.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// --- Modal global para mostrar resultados de scripts/tests ---
window.showScriptResultModal = function (result, title = 'Resultado de Script/Test') {
  const modal = document.getElementById('scriptResultModal');
  const content = document.getElementById('scriptResultContent');
  const label = document.getElementById('scriptResultModalLabel');
  if (label) label.textContent = title;
  if (content) {
    content.textContent = result;
    // Colorear si es error
    if (/Error|Traceback|Exception|FAILED/.test(result)) {
      content.style.color = '#c0392b'; // rojo
      content.style.background = '#fff6f6';
    } else {
      content.style.color = '#212529'; // texto normal
      content.style.background = '#f8f9fa';
    }
    // Autoscroll al final
    setTimeout(() => {
      content.scrollTop = content.scrollHeight;
    }, 100);
  }
  // Mostrar modal usando Bootstrap 5
  if (modal) {
    const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
    bsModal.show();
  }
  // Handler para copiar resultado
  const copyBtn = document.getElementById('copyResultBtn');
  if (copyBtn) {
    copyBtn.onclick = function () {
      if (content) {
        navigator.clipboard.writeText(content.textContent);
        copyBtn.textContent = '¡Copiado!';
        setTimeout(() => {
          copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copiar resultado';
        }, 1200);
      }
    };
  }
};

void 0; // Satisface a los analizadores estrictos, no afecta ejecución

});
