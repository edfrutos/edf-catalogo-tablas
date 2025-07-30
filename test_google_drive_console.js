// 🔧 SCRIPT DE PRUEBA PARA GOOGLE DRIVE DASHBOARD
// Copia y pega este código en la consola del navegador del dashboard

console.log("🚀 Iniciando script de prueba de Google Drive...");

// Función para hacer peticiones AJAX con mejor manejo de errores
function testAjax(endpoint, description) {
    console.log(`\n🧪 Probando: ${description}`);
    console.log(`📡 Endpoint: ${endpoint}`);
    
    return $.ajax({
        url: endpoint,
        method: 'GET',
        timeout: 30000
    }).done(function(response) {
        console.log(`✅ ${description} - ÉXITO:`);
        console.log(response);
        return response;
    }).fail(function(xhr, status, error) {
        console.error(`❌ ${description} - ERROR:`);
        console.error(`Status: ${xhr.status}`);
        console.error(`Error: ${error}`);
        console.error(`Response: ${xhr.responseText}`);
        return xhr;
    });
}

// Tests automáticos
async function runAllTests() {
    console.log("🎯 Ejecutando todos los tests...");
    
    try {
        // Test 1: Conexión básica
        await testAjax('/maintenance/api/test-gdrive', 'Test Conexión Google Drive');
        
        // Test 2: Listar backups (con autenticación)
        await testAjax('/maintenance/api/drive-backups', 'Listar Backups de Drive');
        
        // Test 3: Estado del sistema
        await testAjax('/maintenance/api/system_status', 'Estado del Sistema');
        
        // Test 4: Test sin autenticación (si existe)
        await testAjax('/maintenance/api/test-gdrive-no-auth', 'Test Sin Autenticación');
        
    } catch (error) {
        console.error("❌ Error en la secuencia de tests:", error);
    }
    
    console.log("🏁 Tests completados!");
}

// Función para probar el modal de Google Drive
function testGoogleDriveModal() {
    console.log("🪟 Probando modal de Google Drive...");
    
    // Simular click en el botón que abre el modal
    if ($("#restoreDriveBtn").length > 0) {
        console.log("📱 Simulando click en botón de restaurar Drive...");
        $("#restoreDriveBtn").click();
    } else {
        console.log("⚠️ Botón de restaurar Drive no encontrado");
    }
    
    // Verificar si el modal existe
    if ($("#googleDriveModal").length > 0) {
        console.log("✅ Modal de Google Drive encontrado");
        $("#googleDriveModal").modal('show');
    } else {
        console.log("❌ Modal de Google Drive no encontrado");
    }
}

// Función para probar la función de carga de backups directamente
function testLoadDriveBackups() {
    console.log("📁 Probando carga directa de backups...");
    
    if (typeof loadDriveBackups === 'function') {
        console.log("✅ Función loadDriveBackups encontrada, ejecutando...");
        loadDriveBackups();
    } else {
        console.log("❌ Función loadDriveBackups no encontrada");
        console.log("📋 Funciones disponibles en el scope:");
        console.log(Object.keys(window).filter(key => key.includes('Drive') || key.includes('backup')));
    }
}

// Auto-ejecutar
console.log("⚡ Ejecutando test automático en 2 segundos...");
setTimeout(runAllTests, 2000);

console.log("🔧 Script cargado. Funciones disponibles:");
console.log("- runAllTests() - Ejecutar todos los tests");
console.log("- testGoogleDriveModal() - Probar modal de Google Drive");
console.log("- testLoadDriveBackups() - Probar carga de backups");
console.log("- testAjax(endpoint, description) - Test de endpoint específico");
