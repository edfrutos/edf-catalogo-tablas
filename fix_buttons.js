// Solución para botones que no responden - Forzar asignación de eventos
$(document).ready(function() {
    console.log("🔧 Aplicando corrección para botones de backup...");
    
    // Esperar a que la página se cargue completamente
    setTimeout(function() {
        
        // 1. CORREGIR BOTÓN DE BACKUP
        const backupBtn = $("#backupBtn");
        if (backupBtn.length > 0) {
            console.log("✅ Encontrado botón backup, aplicando corrección...");
            
            // Remover cualquier evento previo que pueda estar causando conflictos
            backupBtn.off("click");
            
            // Asignar evento nuevo y funcional
            backupBtn.on("click", function() {
                console.log("✅ Click en backup detectado - ejecutando...");
                
                const btn = $(this);
                const originalText = btn.html();
                
                // Deshabilitar botón y mostrar estado de carga
                btn.prop("disabled", true).html(
                    "<span class='spinner-border spinner-border-sm' role='status' aria-hidden='true'></span> Generando backup..."
                );
                
                // Mostrar progreso
                $("#backupResult").html(`
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i> Creando backup de la base de datos...
                    </div>
                `);
                
                // Ejecutar llamada AJAX
                $.ajax({
                    url: "/maintenance/api/backup",
                    method: "POST",
                    xhrFields: { withCredentials: true },
                    success: function(response) {
                        console.log("✅ Backup exitoso:", response);
                        
                        if (response.status === "success" && response.download_url) {
                            const successMsg = `
                                <div class="alert alert-success">
                                    <i class="bi bi-check-circle"></i> 
                                    <strong>Backup creado exitosamente</strong><br>
                                    <small>
                                        • Archivo: ${response.filename || "backup.json.gz"}<br>
                                        • Tamaño: ${response.size ? (response.size / 1024).toFixed(2) + ' KB' : 'N/A'}<br>
                                        • Documentos: ${response.total_documents || "N/A"}<br>
                                        • Iniciando descarga automática...
                                    </small>
                                </div>
                            `;
                            $("#backupResult").html(successMsg);
                            
                            // Iniciar descarga
                            setTimeout(() => {
                                window.location.href = response.download_url;
                            }, 1000);
                            
                        } else {
                            $("#backupResult").html(`
                                <div class="alert alert-warning">
                                    <i class="bi bi-exclamation-triangle"></i> 
                                    Backup completado pero sin descarga automática
                                </div>
                            `);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("❌ Error en backup:", status, error, xhr.responseText);
                        
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
                    complete: function() {
                        // Restaurar botón
                        btn.prop("disabled", false).html(originalText);
                    }
                });
            });
            
            console.log("✅ Evento de backup corregido y asignado");
        }
        
        // 2. CORREGIR BOTÓN DE GOOGLE DRIVE
        const driveBtn = $("#restoreDriveBtn");
        if (driveBtn.length > 0) {
            console.log("✅ Encontrado botón Google Drive, verificando modal...");
            
            // Verificar si el modal existe
            const modalId = driveBtn.attr('data-bs-target') || '#restoreDriveModal';
            let modal = $(modalId);
            
            if (modal.length === 0) {
                console.log("⚠️ Modal no encontrado, creando modal básico...");
                
                // Crear modal si no existe
                const modalHtml = `
                <div class="modal fade" id="restoreDriveModal" tabindex="-1" aria-labelledby="restoreDriveModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="restoreDriveModalLabel">
                                    <i class="bi bi-google"></i> Restaurar desde Google Drive
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h6>Backups disponibles en Google Drive</h6>
                                    <button class="btn btn-outline-primary btn-sm" id="refreshDriveBackupsBtn">
                                        <i class="bi bi-arrow-clockwise"></i> Actualizar
                                    </button>
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-bordered" id="driveBackupsTable">
                                        <thead>
                                            <tr>
                                                <th>Archivo</th>
                                                <th>Tamaño</th>
                                                <th>Fecha</th>
                                                <th>Acción</th>
                                            </tr>
                                        </thead>
                                        <tbody id="driveBackupsTableBody">
                                            <tr>
                                                <td colspan="4" class="text-center">
                                                    <div class="spinner-border spinner-border-sm" role="status">
                                                        <span class="visually-hidden">Cargando...</span>
                                                    </div>
                                                    Cargando backups...
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                
                $('body').append(modalHtml);
                modal = $('#restoreDriveModal');
                console.log("✅ Modal de Google Drive creado");
            }
            
            // Asegurar que el botón tiene los atributos correctos
            driveBtn.attr({
                'data-bs-toggle': 'modal',
                'data-bs-target': '#restoreDriveModal'
            });
            
            console.log("✅ Botón de Google Drive corregido");
        }
        
        console.log("🎉 Corrección de botones completada");
        
    }, 1000); // Esperar 1 segundo para asegurar que todo esté cargado
});

// Mensaje de confirmación
console.log("🔧 Script de corrección de botones cargado - se ejecutará automáticamente");
