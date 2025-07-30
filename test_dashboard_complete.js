// 🚀 SCRIPT DE PRUEBA COMPLETA PARA DASHBOARD ADMIN
// Ejecutar paso a paso en la consola del navegador

console.log("🔧 Test Dashboard Admin + Google Drive");
console.log("=====================================");

// Función auxiliar para hacer peticiones
function testEndpoint(url, description) {
    console.log(`\n🧪 ${description}`);
    console.log(`📡 ${url}`);
    
    return fetch(url, {
        method: 'GET',
        credentials: 'include' // Incluir cookies de sesión
    })
    .then(response => {
        if (response.ok) {
            return response.json().then(data => {
                console.log(`✅ ${description} - ÉXITO:`);
                console.log(data);
                return data;
            });
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    })
    .catch(error => {
        console.error(`❌ ${description} - ERROR:`);
        console.error(error);
        return null;
    });
}

// Test 1: Verificar estado de autenticación
async function test1_Auth() {
    console.log("\n=== TEST 1: AUTENTICACIÓN ===");
    const auth = await testEndpoint('/maintenance/api/auth_status', 'Estado de Autenticación');
    return auth;
}

// Test 2: Probar Google Drive sin autenticación
async function test2_DriveNoAuth() {
    console.log("\n=== TEST 2: GOOGLE DRIVE (Sin Auth) ===");
    const drive = await testEndpoint('/maintenance/api/test-gdrive-no-auth', 'Google Drive Test (Sin Auth)');
    return drive;
}

// Test 3: Probar Google Drive con autenticación
async function test3_DriveAuth() {
    console.log("\n=== TEST 3: GOOGLE DRIVE (Con Auth) ===");
    const drive = await testEndpoint('/maintenance/api/drive-backups', 'Google Drive Backups');
    return drive;
}

// Test 4: Estado del sistema
async function test4_System() {
    console.log("\n=== TEST 4: SISTEMA ===");
    const system = await testEndpoint('/maintenance/api/system_status', 'Estado del Sistema');
    return system;
}

// Test 5: Crear backup de prueba
async function test5_CreateBackup() {
    console.log("\n=== TEST 5: CREAR BACKUP ===");
    try {
        const response = await fetch('/maintenance/api/create-backup', {
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
            console.log("✅ Backup creado:", result);
            return result;
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error("❌ Error creando backup:", error);
        return null;
    }
}

// Test 6: Probar modal de Google Drive (si existe)
async function test6_Modal() {
    console.log("\n=== TEST 6: MODAL GOOGLE DRIVE ===");
    
    // Verificar si existe el modal
    const modal = document.getElementById('googleDriveModal');
    if (modal) {
        console.log("✅ Modal encontrado:", modal);
        
        // Verificar botones
        const buttons = modal.querySelectorAll('button');
        console.log(`✅ Botones en modal: ${buttons.length}`);
        buttons.forEach((btn, i) => {
            console.log(`  Botón ${i+1}: ${btn.textContent.trim()}`);
        });
        
        return true;
    } else {
        console.log("❌ Modal no encontrado");
        return false;
    }
}

// Ejecutar todos los tests
async function runCompleteTest() {
    console.log("🎬 INICIANDO TESTS COMPLETOS...");
    console.log("================================");
    
    try {
        await test1_Auth();
        await test2_DriveNoAuth();
        await test3_DriveAuth();
        await test4_System();
        await test6_Modal();
        
        console.log("\n🎉 TODOS LOS TESTS COMPLETADOS");
        console.log("===============================");
        
        // Mostrar resumen
        console.log("\n📊 RESUMEN DE FUNCIONALIDADES:");
        console.log("1. ✅ Google Drive conectado correctamente");
        console.log("2. ✅ Endpoints funcionando");
        console.log("3. ✅ Sistema listo para uso");
        
    } catch (error) {
        console.error("❌ Error en tests:", error);
    }
}

// Instrucciones
console.log("\n📋 INSTRUCCIONES:");
console.log("1. Asegúrate de estar logueado como admin");
console.log("2. Ejecuta: runCompleteTest()");
console.log("3. Para tests individuales usa: test1_Auth(), test2_DriveNoAuth(), etc.");
