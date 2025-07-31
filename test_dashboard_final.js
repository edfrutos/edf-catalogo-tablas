// 🔧 SCRIPT DE PRUEBA FINAL - DASHBOARD ADMIN + GOOGLE DRIVE
// Ejecutar en la consola del navegador después de loguearse

console.log("🚀 INICIANDO SCRIPT DE PRUEBA FINAL");
console.log("==================================");

// Configuración
const BASE_URL = window.location.origin;
console.log(`🌐 Base URL: ${BASE_URL}`);

// Función para probar endpoints
async function testEndpoint(endpoint, description) {
    console.log(`\n🧪 ${description}`);
    console.log(`📡 ${BASE_URL}${endpoint}`);
    
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ ${description} - ÉXITO:`);
            console.log(data);
            return data;
        } else {
            console.error(`❌ ${description} - ERROR HTTP ${response.status}`);
            const errorText = await response.text();
            console.error(`Respuesta: ${errorText.substring(0, 200)}...`);
            return null;
        }
    } catch (error) {
        console.error(`❌ ${description} - ERROR:`);
        console.error(error);
        return null;
    }
}

// Test de Google Drive
async function testGoogleDrive() {
    console.log("\n=== PRUEBAS DE GOOGLE DRIVE ===");
    
    // Test 1: Sin autenticación (endpoint público)
    const noAuth = await testEndpoint('/maintenance/api/test-gdrive-no-auth', 'Google Drive Sin Auth');
    
    // Test 2: Con autenticación
    const withAuth = await testEndpoint('/maintenance/api/drive-backups', 'Google Drive Con Auth');
    
    // Test 3: Test básico
    const basicTest = await testEndpoint('/maintenance/api/test-gdrive', 'Google Drive Test Básico');
    
    return { noAuth, withAuth, basicTest };
}

// Test de autenticación
async function testAuth() {
    console.log("\n=== PRUEBAS DE AUTENTICACIÓN ===");
    const auth = await testEndpoint('/maintenance/api/auth_status', 'Estado de Autenticación');
    return auth;
}

// Test de sistema
async function testSystem() {
    console.log("\n=== PRUEBAS DE SISTEMA ===");
    const system = await testEndpoint('/maintenance/api/system_status', 'Estado del Sistema');
    return system;
}

// Test de modal (verificar elementos DOM)
function testModal() {
    console.log("\n=== PRUEBA DE MODAL GOOGLE DRIVE ===");
    
    const modal = document.getElementById('googleDriveModal');
    if (modal) {
        console.log("✅ Modal Google Drive encontrado");
        
        const buttons = modal.querySelectorAll('button');
        console.log(`✅ Botones en modal: ${buttons.length}`);
        
        buttons.forEach((btn, i) => {
            const text = btn.textContent.trim();
            if (text) {
                console.log(`  ${i+1}. "${text}"`);
            }
        });
        
        return true;
    } else {
        console.log("❌ Modal Google Drive no encontrado");
        return false;
    }
}

// Test de botones principales del dashboard
function testDashboardButtons() {
    console.log("\n=== PRUEBA DE BOTONES DASHBOARD ===");
    
    const buttons = [
        { id: 'backupBtn', name: 'Botón Backup' },
        { id: 'restoreDriveBtn', name: 'Botón Restore Drive' },
        { class: 'run-task', name: 'Botones Ejecutar Ahora' }
    ];
    
    let found = 0;
    
    buttons.forEach(btn => {
        let elements;
        if (btn.id) {
            elements = document.getElementById(btn.id) ? [document.getElementById(btn.id)] : [];
        } else {
            elements = document.querySelectorAll(`.${btn.class}`);
        }
        
        if (elements.length > 0) {
            console.log(`✅ ${btn.name}: ${elements.length} encontrado(s)`);
            found++;
        } else {
            console.log(`❌ ${btn.name}: No encontrado`);
        }
    });
    
    return found;
}

// Crear backup de prueba
async function testCreateBackup() {
    console.log("\n=== PRUEBA CREAR BACKUP ===");
    
    try {
        const response = await fetch(`${BASE_URL}/maintenance/api/create-backup`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                backup_type: 'catalog',
                format: 'json'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("✅ Backup creado exitosamente:");
            console.log(result);
            return result;
        } else {
            console.error(`❌ Error HTTP ${response.status}`);
            const errorText = await response.text();
            console.error(`Respuesta: ${errorText.substring(0, 200)}...`);
            return null;
        }
    } catch (error) {
        console.error("❌ Error creando backup:", error);
        return null;
    }
}

// Test completo
async function runCompleteTest() {
    console.log("🎬 EJECUTANDO BATERÍA COMPLETA DE TESTS");
    console.log("=======================================");
    
    try {
        // 1. Test de autenticación
        const auth = await testAuth();
        
        // 2. Test de Google Drive
        const drive = await testGoogleDrive();
        
        // 3. Test de sistema
        const system = await testSystem();
        
        // 4. Test de modal
        const modal = testModal();
        
        // 5. Test de botones
        const buttons = testDashboardButtons();
        
        // Resumen
        console.log("\n🎉 RESUMEN DE TESTS COMPLETADOS");
        console.log("================================");
        console.log(`✅ Autenticación: ${auth ? 'OK' : 'ERROR'}`);
        console.log(`✅ Google Drive: ${drive.noAuth ? 'OK' : 'ERROR'}`);
        console.log(`✅ Sistema: ${system ? 'OK' : 'ERROR'}`);
        console.log(`✅ Modal: ${modal ? 'OK' : 'ERROR'}`);
        console.log(`✅ Botones: ${buttons > 0 ? 'OK' : 'ERROR'}`);
        
        // Test opcional de creación de backup
        if (auth && auth.is_authenticated) {
            console.log("\n🔧 Usuario autenticado, probando crear backup...");
            const backup = await testCreateBackup();
            console.log(`✅ Crear Backup: ${backup ? 'OK' : 'ERROR'}`);
        }
        
        console.log("\n🏁 TESTS COMPLETADOS EXITOSAMENTE");
        
    } catch (error) {
        console.error("❌ Error en tests:", error);
    }
}

// Instrucciones de uso
console.log("\n📋 INSTRUCCIONES DE USO:");
console.log("========================");
console.log("1. Asegúrate de estar logueado en el dashboard admin");
console.log("2. Ejecuta: runCompleteTest()");
console.log("3. Para tests individuales:");
console.log("   - testAuth()");
console.log("   - testGoogleDrive()");
console.log("   - testSystem()");
console.log("   - testModal()");
console.log("   - testDashboardButtons()");
console.log("   - testCreateBackup()");
console.log("\n🚀 ¡Listo para usar!");
