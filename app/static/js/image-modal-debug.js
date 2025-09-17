// DEBUG ESPECÍFICO PARA IMAGEN EN MODAL
console.log("🔧 IMAGE-MODAL-DEBUG: Iniciando...");

// Función para testear la imagen directamente
window.testImageLoad = function(imageUrl) {
    console.log("🖼️ TEST: Probando carga de imagen:", imageUrl);
    
    const testImg = new Image();
    testImg.onload = function() {
        console.log("✅ TEST: Imagen carga correctamente");
        console.log("  - Dimensiones:", this.naturalWidth + "x" + this.naturalHeight);
        console.log("  - URL final:", this.src);
    };
    testImg.onerror = function() {
        console.log("❌ TEST: Error cargando imagen");
        console.log("  - URL que falló:", this.src);
    };
    testImg.src = imageUrl;
    return testImg;
};

// Función para debuggear el modal de imagen específicamente
window.debugImageModal = function(imageUrl, title) {
    console.log("🔍 DEBUG MODAL: Iniciando debug para:", imageUrl);
    
    // 1. Verificar elementos del modal
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('modalImage');
    const titleEl = document.getElementById('imageModalLabel');
    
    console.log("🔍 Elementos del modal:");
    console.log("  - Modal element:", !!modal);
    console.log("  - Image element:", !!img);
    console.log("  - Title element:", !!titleEl);
    
    if (!modal || !img || !titleEl) {
        console.log("❌ Faltan elementos del modal");
        return;
    }
    
    // 2. Limpiar estado anterior
    img.src = '';
    img.onerror = null;
    img.onload = null;
    
    // 3. Configurar handlers de debug
    img.onerror = function() {
        console.log("❌ MODAL IMAGE ERROR:");
        console.log("  - URL que falló:", this.src);
        console.log("  - Error time:", new Date().toISOString());
    };
    
    img.onload = function() {
        console.log("✅ MODAL IMAGE SUCCESS:");
        console.log("  - URL cargada:", this.src);
        console.log("  - Dimensiones:", this.naturalWidth + "x" + this.naturalHeight);
        console.log("  - Load time:", new Date().toISOString());
    };
    
    // 4. Configurar título
    titleEl.textContent = title || 'Debug Image';
    
    // 5. Asignar URL
    console.log("📤 Asignando URL a imagen:", imageUrl);
    img.src = imageUrl;
    
    // 6. Mostrar modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    console.log("📋 Modal mostrado - observa los eventos de carga");
    
    // 7. Verificar después de un delay
    setTimeout(() => {
        console.log("🕐 ESTADO DESPUÉS DE 2s:");
        console.log("  - Image src:", img.src);
        console.log("  - Image complete:", img.complete);
        console.log("  - Image naturalWidth:", img.naturalWidth);
        console.log("  - Modal visible:", modal.classList.contains('show'));
        
        if (!img.complete || img.naturalWidth === 0) {
            console.log("⚠️ La imagen no cargó correctamente");
            // Intentar con URL directa
            const directUrl = '/admin/s3/b69cb2d8df5d428889e44c8e0063742c.jpg';
            console.log("🔄 Intentando con URL directa:", directUrl);
            img.src = directUrl;
        }
    }, 2000);
};

// Función para testear todas las URLs posibles
window.testAllImageUrls = function() {
    const baseFilename = 'b69cb2d8df5d428889e44c8e0063742c.jpg';
    const urls = [
        '/admin/s3/' + baseFilename,
        '/imagenes_subidas/' + baseFilename,
        '/static/uploads/' + baseFilename,
        'https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/' + baseFilename
    ];
    
    console.log("🧪 TESTANDO TODAS LAS URLs POSIBLES:");
    
    urls.forEach((url, index) => {
        console.log(`\n${index + 1}. Probando: ${url}`);
        setTimeout(() => {
            testImageLoad(url);
        }, index * 1000); // 1 segundo entre cada test
    });
};

// Función para forzar mostrar imagen en modal
window.forceShowImageInModal = function() {
    const imageUrl = '/admin/s3/b69cb2d8df5d428889e44c8e0063742c.jpg';
    const title = 'Test Image (Forced)';
    
    console.log("🚀 FORZANDO MOSTRAR IMAGEN EN MODAL");
    debugImageModal(imageUrl, title);
};

console.log("🔧 IMAGE-MODAL-DEBUG: Funciones disponibles:");
console.log("  - testImageLoad(url) - Probar carga de imagen");
console.log("  - debugImageModal(url, title) - Debug modal completo");
console.log("  - testAllImageUrls() - Probar todas las URLs");
console.log("  - forceShowImageInModal() - Mostrar imagen forzadamente");
console.log("\n💡 Usa: forceShowImageInModal() para probar directamente");