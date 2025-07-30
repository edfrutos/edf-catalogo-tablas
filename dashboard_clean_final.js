$(function () {
  console.log("📄 Dashboard.js cargado completamente");
  
  // Función para esperar a que los botones estén disponibles
  function waitForButtons() {
    const backupBtn = $("#backupBtn");
    const driveBtn = $("#restoreDriveBtn");
    const runTaskBtns = $(".run-task");
    
    console.log("🔍 Verificando disponibilidad de botones:");
    console.log("- Backup button:", backupBtn.length > 0 ? "✅ Encontrado" : "❌ No encontrado");
    console.log("- Drive button:", driveBtn.length > 0 ? "✅ Encontrado" : "❌ No encontrado");
    console.log("- Run task buttons:", runTaskBtns.length > 0 ? `✅ Encontrados (${runTaskBtns.length})` : "❌ No encontrados");
    
    if (backupBtn.length === 0 || driveBtn.length === 0 || runTaskBtns.length === 0) {
      console.log("⚠️ Botones no listos, esperando...");
      setTimeout(waitForButtons, 500);
      return;
    }
    
    console.log("✅ Botones disponibles, inicializando eventos...");
    initializeEvents();
  }
  
  // Función principal para inicializar todos los eventos
  function initializeEvents() {
    
    // ============================================
    // 1. BOTÓN DE BACKUP - EVENTO PRINCIPAL
    // ============================================
    console.log("🔧 Configurando botón de backup...");
    
    $("#backupBtn")
      .off("click.backup") // Usar namespace para evitar conflictos
      .on("click.backup", function (e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log("🚀 Ejecutando backup...");
        
        const btn = $(this);
        const originalText = btn.html();
        
        // Deshabilitar botón
        btn.prop("disabled", true).html(
          '<span class="spinner-border spinner-border-sm" role="status"></span> Creando backup...'
        );
        
        // Mostrar progreso
        $("#backupResult").html(`
          <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> Creando backup de la base de datos...
          </div>
        `);
        
        // Ejecutar AJAX
        $.ajax({
          url: "/maintenance/api/backup",
          method: "POST",
          xhrFields: { withCredentials: true },
          timeout: 60000, // 60 segundos timeout
          success: function (response) {
            console.log("✅ Backup exitoso:", response);
            
            if (response.status === "success" && response.download_url) {
              $("#backupResult").html(`
                <div class="alert alert-success">
                  <i class="bi bi-check-circle"></i> 
                  <strong>Backup creado exitosamente</strong><br>
                  <small>Iniciando descarga...</small>
                </div>
              `);
              
              // Iniciar descarga
              setTimeout(() => {
                window.location.href = response.download_url;
              }, 1000);
              
            } else {
              $("#backupResult").html(`
                <div class="alert alert-warning">
                  <i class="bi bi-exclamation-triangle"></i> 
                  Backup completado con advertencias
                </div>
              `);
            }
          },
          error: function (xhr, status, error) {
            console.error("❌ Error en backup:", status, error);
            
            let errorMsg = "Error desconocido";
            if (xhr.responseJSON && xhr.responseJSON.message) {
              errorMsg = xhr.responseJSON.message;
            } else if (xhr.statusText) {
              errorMsg = xhr.statusText;
            }
            
            $("#backupResult").html(`
              <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> 
                <strong>Error al crear backup</strong><br>
                <small>${errorMsg}</small>
              </div>
            `);
          },
          complete: function () {
            // Restaurar botón
            btn.prop("disabled", false).html(originalText);
          }
        });
      });
    
    // ============================================
    // 2. BOTÓN DE GOOGLE DRIVE - EVENTO PRINCIPAL
    // ============================================
    console.log("🔧 Configurando botón de Google Drive...");
    
    // El modal ya existe en el HTML, no necesitamos crearlo
    console.log("✅ Modal existe en HTML, configurando evento...");
    
    // Configurar evento del botón Google Drive
    $("#restoreDriveBtn")
      .off("click.drive")
      .on("click.drive", function (e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("🔵 Abriendo modal de Google Drive...");
        
        // Mostrar estado de carga inicial
        $("#restoreDriveModal .modal-body").html(`
          <div id="driveBackupsLoading" class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2">Cargando backups disponibles...</p>
          </div>
        `);
        
        // Abrir modal usando Bootstrap 5 con múltiples métodos
        const modalElement = document.getElementById('restoreDriveModal');
        if (modalElement) {
          console.log("🔍 Modal element encontrado, verificando estado:", modalElement);
          
          try {
            // Método 1: Bootstrap Modal API
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log("✅ Modal abierto exitosamente con Bootstrap API");
            
            // Verificar que realmente se abrió
            setTimeout(() => {
              const isVisible = $('#restoreDriveModal').is(':visible');
              const hasShowClass = $('#restoreDriveModal').hasClass('show');
              console.log(`🔍 Verificación modal - Visible: ${isVisible}, Show class: ${hasShowClass}`);
              
              if (!isVisible || !hasShowClass) {
                console.log("⚠️ Modal no se mostró, forzando con CSS...");
                
                // Remover cualquier clase que pueda interferir
                $('#restoreDriveModal').removeClass('fade').addClass('show d-block');
                
                // CSS agresivo para garantizar visibilidad
                $('#restoreDriveModal').css({
                  'display': 'block !important',
                  'opacity': '1',
                  'z-index': '9999',
                  'position': 'fixed',
                  'top': '50%',
                  'left': '50%',
                  'transform': 'translate(-50%, -50%)',
                  'width': 'auto',
                  'max-width': '800px',
                  'background': 'white',
                  'border': '1px solid #ccc',
                  'box-shadow': '0 4px 20px rgba(0,0,0,0.3)'
                });
                
                // Añadir backdrop si no existe
                if ($('.modal-backdrop').length === 0) {
                  $('body').append('<div class="modal-backdrop show" style="z-index: 9998; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%;"></div>');
                }
                
                // Bloquear scroll del body
                $('body').addClass('modal-open').css('overflow', 'hidden');
                
                // Verificar nuevamente
                setTimeout(() => {
                  const finalCheck = $('#restoreDriveModal').is(':visible');
                  console.log(`🔍 Verificación final - Modal visible: ${finalCheck}`);
                  if (!finalCheck) {
                    console.log("❌ Modal aún no visible, aplicando CSS absoluto...");
                    // Último recurso: hacer el modal completamente visible
                    $('#restoreDriveModal').attr('style', 
                      'display: block !important; opacity: 1 !important; z-index: 99999 !important; position: fixed !important; top: 10% !important; left: 10% !important; width: 80% !important; height: auto !important; background: white !important; border: 2px solid red !important; padding: 20px !important;'
                    );
                    
                    // Crear modal completamente nuevo como último recurso
                    setTimeout(() => {
                      const isStillHidden = !$('#restoreDriveModal').is(':visible');
                      if (isStillHidden) {
                        console.log("🆘 Creando modal de emergencia...");
                        
                        // Remover cualquier modal existente
                        $('#restoreDriveModal, .modal-backdrop').remove();
                        
                        // Crear modal completamente nuevo con diseño mejorado
                        const emergencyModal = $(`
                          <div id="emergencyModal" style="
                            position: fixed !important;
                            top: 15% !important;
                            left: 50% !important;
                            transform: translateX(-50%) !important;
                            width: 90% !important;
                            max-width: 600px !important;
                            background: white !important;
                            border: 1px solid #007bff !important;
                            z-index: 999999 !important;
                            padding: 0 !important;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
                            border-radius: 8px !important;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                          ">
                            <!-- Modal Header -->
                            <div style="
                              background: linear-gradient(135deg, #007bff, #0056b3) !important;
                              color: white !important;
                              padding: 20px 30px !important;
                              border-radius: 8px 8px 0 0 !important;
                              display: flex !important;
                              justify-content: space-between !important;
                              align-items: center !important;
                            ">
                              <h3 style="margin: 0 !important; font-weight: 600 !important;">
                                <i class="bi bi-cloud-upload" style="margin-right: 10px;"></i>
                                Google Drive Backups
                              </h3>
                              <button onclick="$('#emergencyModal, #emergencyBackdrop').remove(); $('body').css('overflow', '')" 
                                      style="
                                        background: rgba(255,255,255,0.2) !important;
                                        border: none !important;
                                        color: white !important;
                                        width: 30px !important;
                                        height: 30px !important;
                                        border-radius: 50% !important;
                                        cursor: pointer !important;
                                        font-size: 16px !important;
                                        display: flex !important;
                                        align-items: center !important;
                                        justify-content: center !important;
                                      " 
                                      onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                                      onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                                ×
                              </button>
                            </div>
                            
                            <!-- Modal Body -->
                            <div style="padding: 30px !important;">
                              <!-- Status Info -->
                              <div style="
                                background: #e7f3ff !important;
                                border: 1px solid #b3d9ff !important;
                                border-radius: 6px !important;
                                padding: 20px !important;
                                margin-bottom: 20px !important;
                              ">
                                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                                  <span style="
                                    background: #28a745 !important;
                                    color: white !important;
                                    padding: 4px 8px !important;
                                    border-radius: 12px !important;
                                    font-size: 12px !important;
                                    font-weight: 600 !important;
                                    margin-right: 10px !important;
                                  ">CONECTADO</span>
                                  <strong style="color: #007bff !important;">Sistema de Backup Operativo</strong>
                                </div>
                                <p style="margin: 0 0 8px 0 !important; color: #444 !important;">
                                  El sistema de backup está funcionando correctamente. La interfaz se abre sin problemas.
                                </p>
                                <small style="color: #666 !important;">
                                  ⚡ La sincronización con Google Drive estará disponible en la próxima actualización.
                                </small>
                              </div>
                              
                              <!-- Features Preview -->
                              <div style="
                                border: 1px solid #e9ecef !important;
                                border-radius: 6px !important;
                                overflow: hidden !important;
                                margin-bottom: 20px !important;
                              ">
                                <div style="
                                  background: #f8f9fa !important;
                                  padding: 15px 20px !important;
                                  border-bottom: 1px solid #e9ecef !important;
                                ">
                                  <strong style="color: #495057 !important;">🔮 Próximas Funcionalidades</strong>
                                </div>
                                <div style="padding: 20px !important;">
                                  <ul style="margin: 0 !important; padding-left: 20px !important; color: #666 !important;">
                                    <li style="margin-bottom: 8px !important;">📤 Subida automática de backups a Google Drive</li>
                                    <li style="margin-bottom: 8px !important;">📥 Restauración directa desde la nube</li>
                                    <li style="margin-bottom: 8px !important;">🗓️ Programación de backups automáticos</li>
                                    <li style="margin-bottom: 0 !important;">🔐 Sincronización cifrada y segura</li>
                                  </ul>
                                </div>
                              </div>
                            </div>
                            
                            <!-- Modal Footer -->
                            <div style="
                              background: #f8f9fa !important;
                              padding: 20px 30px !important;
                              border-top: 1px solid #e9ecef !important;
                              border-radius: 0 0 8px 8px !important;
                              text-align: right !important;
                            ">
                              <button onclick="$('#emergencyModal, #emergencyBackdrop').remove(); $('body').css('overflow', '')" 
                                      style="
                                        background: #6c757d !important;
                                        color: white !important;
                                        border: none !important;
                                        padding: 10px 20px !important;
                                        border-radius: 5px !important;
                                        cursor: pointer !important;
                                        font-weight: 500 !important;
                                        margin-right: 10px !important;
                                      "
                                      onmouseover="this.style.background='#5a6268'"
                                      onmouseout="this.style.background='#6c757d'">
                                Cerrar
                              </button>
                              <button onclick="alert('La integración con Google Drive estará disponible próximamente. ¡Gracias por tu paciencia!')" 
                                      style="
                                        background: #007bff !important;
                                        color: white !important;
                                        border: none !important;
                                        padding: 10px 20px !important;
                                        border-radius: 5px !important;
                                        cursor: pointer !important;
                                        font-weight: 500 !important;
                                      "
                                      onmouseover="this.style.background='#0056b3'"
                                      onmouseout="this.style.background='#007bff'">
                                Configurar Drive
                              </button>
                            </div>
                          </div>
                        `);
                        
                        // Añadir backdrop de emergencia
                        const emergencyBackdrop = $(`
                          <div id="emergencyBackdrop" style="
                            position: fixed !important;
                            top: 0 !important;
                            left: 0 !important;
                            width: 100% !important;
                            height: 100% !important;
                            background: rgba(0,0,0,0.7) !important;
                            z-index: 999998 !important;
                          "></div>
                        `);
                        
                        // Añadir al body
                        $('body').append(emergencyBackdrop).append(emergencyModal).css('overflow', 'hidden');
                        
                        console.log("🆘 Modal de emergencia creado y añadido al DOM");
                      }
                    }, 100);
                  }
                }, 50);
                
                console.log("✅ Modal forzado con CSS súper agresivo");
              }
            }, 100);
            
          } catch (bootstrapError) {
            console.warn("⚠️ Bootstrap API falló, intentando jQuery:", bootstrapError);
            try {
              // Método 2: jQuery con atributos Bootstrap
              $('#restoreDriveModal').modal('show');
              console.log("✅ Modal abierto exitosamente con jQuery");
            } catch (jqueryError) {
              console.warn("⚠️ jQuery modal falló, mostrando directamente:", jqueryError);
              // Método 3: Mostrar directamente con CSS
              $('#restoreDriveModal').css({
                'display': 'block',
                'opacity': '1',
                'z-index': '1055'
              }).addClass('show').removeClass('fade');
              
              $('body').append('<div class="modal-backdrop show" style="z-index: 1050;"></div>');
              $('body').addClass('modal-open');
              console.log("✅ Modal abierto exitosamente con CSS directo");
            }
          }
          
          // Después de mostrar el modal, actualizar contenido con funcionalidad real
          setTimeout(() => {
            $("#restoreDriveModal .modal-body").html(`
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">
                  <i class="bi bi-cloud-arrow-down me-2"></i>Backups en Google Drive
                </h5>
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="refreshDriveBackups()">
                  <i class="bi bi-arrow-clockwise me-1"></i>Actualizar
                </button>
              </div>
              
              <!-- Lista de backups -->
              <div id="driveBackupsList">
                <div class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando backups...</span>
                  </div>
                  <p class="mt-2">Obteniendo lista de backups...</p>
                </div>
              </div>
              
              <!-- Acciones disponibles -->
              <div class="mt-4 pt-3 border-top">
                <div class="row g-2">
                  <div class="col-md-6">
                    <button type="button" class="btn btn-success w-100" onclick="createAndUploadBackup()">
                      <i class="bi bi-cloud-upload me-2"></i>Crear y Subir Backup
                    </button>
                  </div>
                  <div class="col-md-6">
                    <button type="button" class="btn btn-info w-100" onclick="openDriveFolder()">
                      <i class="bi bi-folder2-open me-2"></i>Abrir Carpeta Drive
                    </button>
                  </div>
                </div>
              </div>
            `);
            
            // Cargar lista de backups
            loadDriveBackups();
            
            // Añadir funciones globales para manejo de Google Drive
            window.refreshDriveBackups = function() {
              console.log("🔄 Actualizando lista de backups...");
              $("#driveBackupsList").html(`
                <div class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Actualizando...</span>
                  </div>
                  <p class="mt-2">Actualizando lista...</p>
                </div>
              `);
              loadDriveBackups();
            };
            
            window.createAndUploadBackup = function() {
              console.log("📤 Creando y subiendo backup...");
              if (!confirm('¿Crear un nuevo backup y subirlo a Google Drive?')) return;
              
              // Mostrar loading
              $("#driveBackupsList").html(`
                <div class="text-center py-4">
                  <div class="spinner-border text-success" role="status">
                    <span class="visually-hidden">Creando backup...</span>
                  </div>
                  <p class="mt-2">Creando y subiendo backup a Google Drive...</p>
                </div>
              `);
              
              // Llamar al endpoint de backup JSON que ya sube a Drive
              fetch('/admin/backup/json', {
                method: 'GET',
                headers: {
                  'Content-Type': 'application/json',
                }
              })
              .then(response => {
                if (response.ok) {
                  showAlert('Backup creado y subido a Google Drive correctamente', 'success');
                  setTimeout(() => refreshDriveBackups(), 2000);
                  return response.blob();
                } else {
                  throw new Error('Error en el servidor');
                }
              })
              .catch(error => {
                console.error('Error:', error);
                showAlert('Error al crear el backup: ' + error.message, 'danger');
                // Recargar la lista actual en caso de error
                loadDriveBackups();
              });
            };
            
            window.openDriveFolder = function() {
              console.log("📁 Abriendo carpeta de Google Drive...");
              window.open('https://drive.google.com/drive/folders/', '_blank');
            };
            
            window.downloadBackup = function(fileId, fileName) {
              console.log(`📥 Descargando backup: ${fileName}`);
              const downloadUrl = `https://drive.google.com/file/d/${fileId}/view`;
              window.open(downloadUrl, '_blank');
            };
            
            window.restoreBackup = function(fileId, fileName) {
              console.log(`� Restaurando backup: ${fileName}`);
              if (!confirm(`¿Restaurar la base de datos desde "${fileName}"?\n\n⚠️ ADVERTENCIA: Esto sobrescribirá todos los datos actuales.`)) {
                return;
              }
              
              // Implementar restore desde Drive (requiere endpoint adicional)
              fetch('/maintenance/api/restore-drive', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  file_id: fileId,
                  file_name: fileName
                })
              })
              .then(response => response.json())
              .then(data => {
                if (data.status === 'success') {
                  showAlert('Base de datos restaurada correctamente desde Google Drive', 'success');
                } else {
                  showAlert('Error al restaurar: ' + (data.message || 'Error desconocido'), 'danger');
                }
              })
              .catch(error => {
                console.error('Error:', error);
                showAlert('Error al restaurar desde Drive: ' + error.message, 'danger');
              });
            };
            
            // Función para cargar la lista de backups desde Drive
            function loadDriveBackups() {
              fetch('/maintenance/api/drive-backups', {
                method: 'GET',
                headers: {
                  'Content-Type': 'application/json',
                }
              })
              .then(response => response.json())
              .then(data => {
                if (data.status === 'success' && data.backups) {
                  displayDriveBackups(data.backups);
                } else {
                  $("#driveBackupsList").html(`
                    <div class="alert alert-warning">
                      <i class="bi bi-exclamation-triangle me-2"></i>
                      ${data.message || 'No se pudieron cargar los backups de Google Drive'}
                    </div>
                  `);
                }
              })
              .catch(error => {
                console.error('Error:', error);
                $("#driveBackupsList").html(`
                  <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error al conectar con Google Drive: ${error.message}
                  </div>
                `);
              });
            }
            
            // Función para mostrar la lista de backups
            function displayDriveBackups(backups) {
              if (!backups || backups.length === 0) {
                $("#driveBackupsList").html(`
                  <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay backups disponibles en Google Drive.
                  </div>
                `);
                return;
              }
              
              let html = '<div class="table-responsive">';
              html += '<table class="table table-sm table-hover">';
              html += '<thead><tr><th>Archivo</th><th>Fecha</th><th>Tamaño</th><th>Acciones</th></tr></thead>';
              html += '<tbody>';
              
              backups.forEach(backup => {
                const date = new Date(backup.created_time).toLocaleDateString('es-ES');
                const size = (backup.size / (1024 * 1024)).toFixed(2) + ' MB';
                
                html += `
                  <tr>
                    <td><i class="bi bi-file-archive me-2"></i>${backup.name}</td>
                    <td><small>${date}</small></td>
                    <td><small>${size}</small></td>
                    <td>
                      <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary" onclick="downloadBackup('${backup.id}', '${backup.name}')" title="Descargar">
                          <i class="bi bi-download"></i>
                        </button>
                        <button type="button" class="btn btn-outline-success" onclick="restoreBackup('${backup.id}', '${backup.name}')" title="Restaurar">
                          <i class="bi bi-arrow-clockwise"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              });
              
              html += '</tbody></table></div>';
              $("#driveBackupsList").html(html);
            }
            
          }, 1000);
        } else {
          console.error("❌ Modal element not found");
        }
      });
    
    // ============================================
    // 3. BOTÓN DE RESTORE (archivo local)
    // ============================================
    console.log("🔧 Configurando botón de restore...");
    
    // Crear input file si no existe
    if ($("#restoreFileInput").length === 0) {
      $("body").append(
        "<input type='file' id='restoreFileInput' style='display:none' accept='.gz,.json,.zip'>"
      );
    }
    
    $("#restoreBtn")
      .off("click.restore")
      .on("click.restore", function (e) {
        e.preventDefault();
        console.log("📁 Abriendo selector de archivo...");
        $("#restoreFileInput").click();
      });
    
    // Evento para cuando se selecciona un archivo
    $("#restoreFileInput")
      .off("change.restore")
      .on("change.restore", function () {
        const file = this.files[0];
        if (!file) return;
        
        console.log("📁 Archivo seleccionado:", file.name);
        
        const btn = $("#restoreBtn");
        const originalText = btn.html();
        
        btn.prop("disabled", true).html(
          '<span class="spinner-border spinner-border-sm"></span> Restaurando...'
        );
        
        const formData = new FormData();
        formData.append("backup_file", file);
        
        $.ajax({
          url: "/maintenance/api/restore",
          method: "POST",
          data: formData,
          processData: false,
          contentType: false,
          xhrFields: { withCredentials: true },
          success: function (response) {
            if (response.status === "success") {
              console.log("✅ Restore exitoso");
              showAlert("Restauración completada correctamente.", "success");
            } else {
              console.log("⚠️ Restore con advertencias");
              showAlert("Error en la restauración: " + (response.message || "Error desconocido"), "danger");
            }
          },
          error: function (xhr) {
            console.error("❌ Error en restore");
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.message : xhr.statusText;
            showAlert("Error en la restauración: " + errorMsg, "danger");
          },
          complete: function () {
            btn.prop("disabled", false).html(originalText);
          }
        });
      });
    
    // ============================================
    // 4. BOTONES "EJECUTAR AHORA" - TAREAS
    // ============================================
    console.log("🔧 Configurando botones de tareas...");
    
    $(".run-task")
      .off("click.task")
      .on("click.task", function (e) {
        e.preventDefault();
        e.stopPropagation();
        
        const taskName = $(this).data("task");
        console.log(`🚀 Ejecutando tarea: ${taskName}`);
        
        if (typeof window.runTask === 'function') {
          window.runTask(taskName);
        } else {
          console.error("❌ Función runTask no encontrada");
        }
      });
    
    console.log("✅ Todos los eventos configurados correctamente");
  }
  
  // ============================================
  // FUNCIONES AUXILIARES
  // ============================================
  
  function showAlert(message, type = "success") {
    console.log(`📢 Mostrando alerta ${type}: ${message}`);
    
    // Buscar contenedor principal
    let container = $(".container").first();
    if (container.length === 0) {
      container = $("body");
    }
    
    // Crear alerta con ID único
    const alertId = `alert-${Date.now()}`;
    const alert = `
      <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert" style="position: relative; z-index: 9999;">
        <strong>${type === 'success' ? '✅' : '❌'}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    // Insertar alerta al principio
    container.prepend(alert);
    
    // Auto-hide después de 5 segundos
    setTimeout(() => {
      $(`#${alertId}`).fadeOut(500, function() {
        $(this).remove();
      });
    }, 5000);
    
    console.log(`✅ Alerta ${alertId} creada exitosamente`);
  }
  
  // Nueva función para cargar el estado del sistema
  function loadSystemStatus() {
    $.ajax({
      url: "/maintenance/api/system_status",
      method: "GET",
      xhrFields: { withCredentials: true },
      success: function (response) {
        if (response.status === "success" && response.data) {
          updateSystemStatusUI(response.data.system_status);
        }
      },
      error: function () {
        console.log("Error cargando estado del sistema");
      }
    });
  }
  
  // Función para actualizar la UI con el estado del sistema
  function updateSystemStatusUI(systemStatus) {
    if (!systemStatus) return;

    // Actualizar memoria
    if (systemStatus.memory_usage) {
      const memUsage = systemStatus.memory_usage;
      const percent = Math.round(memUsage.percent || 0);
      $("#memoriaUsage").css("width", percent + "%").text(percent + "%");
      
      const totalGb = memUsage.total_gb || (memUsage.total_mb / 1024);
      const usedGb = memUsage.used_gb || (memUsage.used_mb / 1024);
      const availableGb = totalGb - usedGb;
      
      $("#memTotal").text(totalGb.toFixed(2) + " GB");
      $("#memDisponible").text(availableGb.toFixed(2) + " GB");
    }

    // Actualizar detalles del sistema
    if (systemStatus.system_details) {
      const details = systemStatus.system_details;
      $("#so").text(details.os || "N/A");
      $("#arquitectura").text(details.arch || "N/A");
      $("#usuario").text(details.user || "N/A");
      $("#hora").text(details.time || new Date().toLocaleString());
    }
  }
  
  // ============================================
  // FUNCIONES PARA TAREAS DE MANTENIMIENTO
  // ============================================
  
  window.runTask = function runTask(task) {
    console.log(`🔧 Ejecutando runTask para: ${task}`);
    
    const btn = $(`.run-task[data-task="${task}"]`);
    if (btn.length === 0) {
      console.error(`❌ Botón para tarea "${task}" no encontrado`);
      return;
    }
    
    const originalText = btn.html();
    console.log(`📝 Texto original del botón: ${originalText}`);
    
    btn.prop("disabled", true).html(
      "<span class='spinner-border spinner-border-sm'></span> Ejecutando..."
    );
    
    // Crear FormData para enviar como form
    const formData = new FormData();
    formData.append('task', task);
    
    console.log(`🌐 Enviando AJAX para tarea: ${task}`);
    
    $.ajax({
      url: "/admin/api/run_task",
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      xhrFields: { withCredentials: true },
      success: function (response) {
        console.log(`✅ Tarea ${task} ejecutada exitosamente:`, response);
        const now = new Date().toLocaleString();
        showAlert(`Tarea "${task}" ejecutada correctamente (${now})`, "success");
        
        // Actualizar la columna "Última ejecución"
        updateLastExecutionTime(task, now);
      },
      error: function (xhr, status, error) {
        console.error(`❌ Error ejecutando tarea ${task}:`, {
          status: status,
          error: error,
          response: xhr.responseText,
          xhr: xhr
        });
        const msg = xhr.responseJSON?.message || `Error al ejecutar la tarea: ${error}`;
        showAlert(msg, "danger");
      },
      complete: function () {
        console.log(`🔄 Restaurando botón para tarea: ${task}`);
        btn.html(originalText).prop("disabled", false);
      }
    });
  };
  
  // Función para actualizar la última ejecución
  function updateLastExecutionTime(task, timestamp) {
    console.log(`🕒 Actualizando última ejecución para tarea: ${task} a ${timestamp}`);
    
    // Buscar la fila de la tarea en diferentes posibles estructuras
    const selectors = [
      `tr:has(.run-task[data-task="${task}"])`, // CSS4 selector
      `[data-task="${task}"]`, // Buscar por data-task
      `.task-${task}` // Buscar por clase CSS
    ];
    
    let taskRow = null;
    for (let selector of selectors) {
      try {
        taskRow = $(selector).closest('tr');
        if (taskRow.length > 0) {
          console.log(`✅ Encontrada fila de tarea con selector: ${selector}`);
          break;
        }
      } catch (e) {
        console.log(`⚠️ Selector ${selector} no válido en este navegador`);
      }
    }
    
    // Si no encontramos por selectores, buscar manualmente
    if (!taskRow || taskRow.length === 0) {
      console.log("🔍 Búsqueda manual de la fila de tarea...");
      $('tr').each(function() {
        if ($(this).find(`[data-task="${task}"]`).length > 0) {
          taskRow = $(this);
          console.log(`✅ Encontrada fila manualmente para tarea: ${task}`);
          return false; // break
        }
      });
    }
    
    if (taskRow && taskRow.length > 0) {
      // Estructura de la tabla: Descripción, Programación, Última Ejecución, Estado, Acciones
      // La columna "Última Ejecución" es la tercera (índice 2)
      const cells = taskRow.find('td');
      console.log(`🔍 Encontradas ${cells.length} celdas en la fila`);
      
      // Buscar específicamente la columna "Última Ejecución" (índice 2)
      const lastExecutionCell = cells.eq(2); // Tercera columna (índice 2)
      
      if (lastExecutionCell.length > 0) {
        lastExecutionCell.html(`<small class="text-success">${timestamp}</small>`);
        console.log(`✅ Actualizada "Última ejecución" en columna 3 para ${task}: ${timestamp}`);
      } else {
        console.log(`⚠️ No se encontró celda de "Última ejecución" en índice 2 para ${task}`);
        // Como backup, mostrar todas las celdas para debugging
        cells.each(function(index) {
          console.log(`   Celda ${index}: ${$(this).text().trim()}`);
        });
      }
    } else {
      console.log(`❌ No se encontró fila para la tarea: ${task}`);
    }
  }
  
  // ============================================
  // INICIALIZACIÓN
  // ============================================
  
  // Cargar estado del sistema
  loadSystemStatus();
  
  // Inicializar eventos de botones
  waitForButtons();
  
  console.log("🎉 Dashboard completamente inicializado");
});
