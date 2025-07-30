/* 
Debug script para identificar problemas con los botones de backup 
Pega este código en la consola del navegador cuando estés en la página del dashboard
*/

console.log("=== DEBUG BOTONES DE BACKUP ===");

// Verificar si jQuery está cargado
if (typeof $ === 'undefined') {
    console.error("❌ jQuery no está cargado");
} else {
    console.log("✅ jQuery está cargado:", $.fn.jquery);
}

// Verificar si los botones existen
const backupBtn = $("#backupBtn");
const driveBtn = $("#restoreDriveBtn");

console.log("Botón backup encontrado:", backupBtn.length > 0 ? "✅" : "❌", backupBtn.length);
console.log("Botón drive encontrado:", driveBtn.length > 0 ? "✅" : "❌", driveBtn.length);

if (backupBtn.length > 0) {
    console.log("Eventos asignados al botón backup:", $._data(backupBtn[0], "events"));
}

if (driveBtn.length > 0) {
    console.log("Eventos asignados al botón drive:", $._data(driveBtn[0], "events"));
}

// Test manual de click
function testBackupClick() {
    console.log("🔧 Ejecutando test manual de backup...");
    
    $.ajax({
        url: "/maintenance/api/backup",
        method: "POST",
        xhrFields: { withCredentials: true },
        beforeSend: function(xhr) {
            console.log("📤 Enviando petición AJAX a:", "/maintenance/api/backup");
        },
        success: function(response) {
            console.log("✅ Respuesta exitosa:", response);
        },
        error: function(xhr, status, error) {
            console.error("❌ Error en petición:", {
                status: status,
                error: error,
                statusCode: xhr.status,
                responseText: xhr.responseText
            });
        }
    });
}

// Test de autenticación
function testAuth() {
    console.log("🔧 Verificando autenticación...");
    
    $.ajax({
        url: "/maintenance/dashboard",
        method: "GET",
        xhrFields: { withCredentials: true },
        success: function(response) {
            console.log("✅ Autenticación OK - acceso al dashboard permitido");
        },
        error: function(xhr, status, error) {
            console.error("❌ Error de autenticación:", {
                status: status,
                error: error,
                statusCode: xhr.status
            });
            
            if (xhr.status === 401) {
                console.log("💡 Solución: Necesitas hacer login primero");
            } else if (xhr.status === 403) {
                console.log("💡 Solución: Necesitas permisos de administrador");
            }
        }
    });
}

// Ejecutar tests automáticamente
console.log("\n🔧 Ejecutando tests automáticos...");
testAuth();

console.log("\n💡 Comandos disponibles:");
console.log("• testBackupClick() - Probar backup manualmente");
console.log("• testAuth() - Verificar autenticación");
console.log("• $(\"#backupBtn\").click() - Simular click en botón backup");

// Asignar funciones al objeto window para acceso global
window.testBackupClick = testBackupClick;
window.testAuth = testAuth;
