// DEBUG ESPECÍFICO PARA PROBLEMAS DE MODAL Y MULTIMEDIA
console.log("🔧 MULTIMEDIA-DEBUG: Iniciando debug específico...");

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔧 MULTIMEDIA-DEBUG: DOM cargado");
    
    // Función de debug para verificar datos de la fila
    window.debugRow = function(rowNumber) {
        const row = document.querySelector(`#fila-${rowNumber}`);
        if (!row) {
            console.log(`❌ Fila ${rowNumber} no encontrada`);
            return;
        }
        
        console.log(`🔍 DEBUGGING FILA ${rowNumber}:`);
        
        // Buscar columna multimedia
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, index) => {
            const content = cell.innerHTML.trim();
            if (content.includes('Multimedia') || content.includes('multimedia') || 
                content.includes('.mp4') || content.includes('.jpg') || 
                content.includes('showMultimediaModal') || content.includes('showImageModal')) {
                
                console.log(`📂 Celda ${index} (posible multimedia):`, content);
            } else if (content.length > 50) {
                console.log(`📂 Celda ${index} (contenido largo):`, content.substring(0, 100) + '...');
            } else {
                console.log(`📂 Celda ${index}:`, content);
            }
        });
    };
    
    // Función para interceptar y debuggear llamadas a modal
    const originalShowImageModal = window.showImageModal;
    const originalShowMultimediaModal = window.showMultimediaModal;
    
    window.showImageModal = function(imageUrl, title, catalog) {
        console.log("🖼️ DEBUG showImageModal intercepted:");
        console.log("  - URL:", imageUrl);
        console.log("  - Title:", title);
        console.log("  - Catalog:", catalog);
        
        // Verificar si los elementos del modal existen
        const modal = document.getElementById('imageModal');
        const img = document.getElementById('modalImage');
        const titleEl = document.getElementById('imageModalLabel');
        
        console.log("🔍 Modal elements check:");
        console.log("  - imageModal exists:", !!modal);
        console.log("  - modalImage exists:", !!img);
        console.log("  - imageModalLabel exists:", !!titleEl);
        
        if (originalShowImageModal) {
            originalShowImageModal(imageUrl, title, catalog);
            
            // Verificar después de la llamada original
            setTimeout(() => {
                console.log("📊 POST-CALL CHECK:");
                console.log("  - Modal has 'show' class:", modal?.classList.contains('show'));
                console.log("  - Modal display style:", modal?.style.display);
                console.log("  - Image src:", img?.src);
                console.log("  - Title text:", titleEl?.textContent);
                
                // Si la imagen está vacía, intentar debug
                if (img && (!img.src || img.src === window.location.href)) {
                    console.log("❌ IMAGEN VACÍA DETECTADA - Forzando URL");
                    img.src = imageUrl;
                    img.onload = () => console.log("✅ Imagen cargada tras debug fix");
                    img.onerror = () => console.log("❌ Error cargando imagen tras debug fix");
                }
            }, 500);
        } else {
            console.log("❌ originalShowImageModal no disponible");
        }
    };
    
    window.showMultimediaModal = function(multimediaUrl, title, catalog) {
        console.log("🎬 DEBUG showMultimediaModal intercepted:");
        console.log("  - URL:", multimediaUrl);
        console.log("  - Title:", title);
        console.log("  - Catalog:", catalog);
        
        // Verificar elementos del modal
        const modal = document.getElementById('multimediaModal');
        const content = document.getElementById('multimediaContent');
        const titleEl = document.getElementById('multimediaModalLabel');
        
        console.log("🔍 Multimedia modal elements check:");
        console.log("  - multimediaModal exists:", !!modal);
        console.log("  - multimediaContent exists:", !!content);
        console.log("  - multimediaModalLabel exists:", !!titleEl);
        
        if (originalShowMultimediaModal) {
            originalShowMultimediaModal(multimediaUrl, title, catalog);
            
            // Verificar después de la llamada
            setTimeout(() => {
                console.log("📊 MULTIMEDIA POST-CALL CHECK:");
                console.log("  - Modal has 'show' class:", modal?.classList.contains('show'));
                console.log("  - Modal display style:", modal?.style.display);
                console.log("  - Content HTML length:", content?.innerHTML.length);
                console.log("  - Content preview:", content?.innerHTML.substring(0, 200));
                console.log("  - Title text:", titleEl?.textContent);
                
                // Si el contenido está vacío, forzar contenido manual
                if (content && content.innerHTML.trim().length === 0) {
                    console.log("❌ CONTENIDO VACÍO DETECTADO - Forzando contenido");
                    const extension = multimediaUrl.split('.').pop()?.toLowerCase();
                    if (['mp4', 'webm', 'avi', 'mov'].includes(extension)) {
                        content.innerHTML = `
                            <div class="text-center">
                                <h5>Video Debug</h5>
                                <video controls style="max-width: 100%; max-height: 400px;">
                                    <source src="${multimediaUrl}" type="video/${extension}">
                                    Tu navegador no soporta video.
                                </video>
                            </div>
                        `;
                        console.log("✅ Contenido de video forzado");
                    } else {
                        content.innerHTML = `
                            <div class="text-center">
                                <h5>Multimedia Debug</h5>
                                <p>URL: ${multimediaUrl}</p>
                                <a href="${multimediaUrl}" target="_blank" class="btn btn-primary">Abrir</a>
                            </div>
                        `;
                        console.log("✅ Contenido genérico forzado");
                    }
                }
            }, 500);
        } else {
            console.log("❌ originalShowMultimediaModal no disponible");
        }
    };
    
    // Debug automático de toda la tabla
    window.debugAllRows = function() {
        console.log("🔍 DEBUGGING TODAS LAS FILAS:");
        const rows = document.querySelectorAll('tr[id^="fila-"]');
        console.log(`Encontradas ${rows.length} filas`);
        
        rows.forEach((row, index) => {
            const rowNumber = index + 1;
            console.log(`\n--- FILA ${rowNumber} ---`);
            debugRow(rowNumber);
        });
    };
    
    // Función para buscar específicamente archivos multimedia en la tabla
    window.findMultimediaFiles = function() {
        console.log("🎬 BUSCANDO ARCHIVOS MULTIMEDIA:");
        
        const allText = document.body.textContent;
        const multimediaExtensions = ['.mp4', '.avi', '.mov', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.gif'];
        
        multimediaExtensions.forEach(ext => {
            if (allText.includes(ext)) {
                console.log(`✅ Encontrado: ${ext}`);
                
                // Buscar elementos específicos con esta extensión
                const elements = document.querySelectorAll(`*[onclick*="${ext}"], *[src*="${ext}"], *[href*="${ext}"]`);
                elements.forEach(el => {
                    console.log(`  - Elemento:`, el.tagName, el.onclick?.toString() || el.src || el.href);
                });
            }
        });
    };
    
    // Función para verificar qué archivos están en S3
    window.checkS3Files = function() {
        console.log("☁️ VERIFICANDO ARCHIVOS S3:");
        
        const s3Elements = document.querySelectorAll('*[src*="s3"], *[href*="s3"], *[onclick*="s3"]');
        s3Elements.forEach(el => {
            const url = el.src || el.href || (el.onclick?.toString().match(/['"`]([^'"`]*s3[^'"`]*)['"`]/) || [])[1];
            if (url) {
                console.log(`📁 S3 URL encontrada:`, url);
                
                // Verificar si es accesible
                fetch(url, { method: 'HEAD' }).then(response => {
                    console.log(`  - Status: ${response.status} (${response.ok ? 'OK' : 'ERROR'})`);
                }).catch(error => {
                    console.log(`  - Error: ${error.message}`);
                });
            }
        });
    };
    
    console.log("🔧 MULTIMEDIA-DEBUG: Funciones disponibles:");
    console.log("  - debugRow(5) - Debug fila específica");
    console.log("  - debugAllRows() - Debug todas las filas");
    console.log("  - findMultimediaFiles() - Buscar archivos multimedia");
    console.log("  - checkS3Files() - Verificar archivos S3");
});