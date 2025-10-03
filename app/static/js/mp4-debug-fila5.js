// DEBUG ESPECÍFICO PARA FILA #5 - MP4 PROBLEM
console.log('🔍 MP4 Debug cargado específicamente para fila #5');

function debugMP4Fila5() {
    console.log('🎬 === DEBUG MP4 FILA #5 ===');
    
    // Verificar si window.catalogData existe
    if (!window.catalogData) {
        console.warn('⚠️ window.catalogData no existe aún. Reintentando en 2 segundos...');
        setTimeout(debugMP4Fila5, 2000);
        return;
    }
    
    if (!window.catalogData.rows || !Array.isArray(window.catalogData.rows)) {
        console.error('❌ window.catalogData.rows no existe o no es array');
        return;
    }
    
    // Verificar fila #5 (índice 4)
    const row5 = window.catalogData.rows[4];
    if (!row5) {
        console.error('❌ Fila #5 no existe (índice 4)');
        return;
    }
    
    console.log('✅ Fila #5 encontrada:', row5);
    
    // Verificar campo Multimedia
    const multimedia = row5.Multimedia;
    console.log('🎥 Campo Multimedia en fila #5:', {
        valor: multimedia,
        tipo: typeof multimedia,
        esString: typeof multimedia === 'string',
        esArray: Array.isArray(multimedia),
        esNull: multimedia === null,
        esUndefined: multimedia === undefined,
        length: multimedia ? multimedia.length : 'N/A'
    });
    
    // Si es string, verificar contenido
    if (typeof multimedia === 'string') {
        console.log('📝 Análisis de string:', {
            empiezaConHttp: multimedia.startsWith('http'),
            empiezaConHttps: multimedia.startsWith('https'),
            contieneS3: multimedia.includes('s3.'),
            contieneMP4: multimedia.toLowerCase().includes('.mp4'),
            extension: multimedia.substring(multimedia.lastIndexOf('.')),
            url_completa: multimedia
        });
        
        // Verificar detección de extensión
        const isMP4 = multimedia.toLowerCase().endsWith('.mp4');
        const isVideo = multimedia.toLowerCase().endsWith(('.mp4', '.avi', '.mov', '.wmv'));
        
        console.log('🎬 Detección de video:', {
            esMP4: isMP4,
            esVideo: isVideo,
            extensionDetectada: multimedia.toLowerCase().substring(multimedia.toLowerCase().lastIndexOf('.'))
        });
        
        // Verificar si la URL es accesible
        console.log('🌐 Probando accesibilidad de URL...');
        const img = new Image();
        img.onload = () => console.log('✅ URL es accesible como imagen');
        img.onerror = () => console.log('❌ URL no es accesible como imagen (normal para video)');
        img.src = multimedia;
    }
    
    // Verificar elemento DOM de la fila #5
    const domRow = document.querySelector('#fila-5');
    console.log('🏗️ Elemento DOM fila #5:', domRow);
    
    if (domRow) {
        const multimediaCell = domRow.children[window.catalogData.headers.indexOf('Multimedia') + 1];
        console.log('📱 Celda Multimedia DOM:', multimediaCell);
        console.log('📱 HTML de celda:', multimediaCell ? multimediaCell.innerHTML : 'NO ENCONTRADA');
    }
}

// Función para forzar re-render del multimedia en fila #5
function forceRenderMP4Fila5() {
    console.log('🔄 Forzando re-render de MP4 en fila #5...');
    
    const row5 = window.catalogData.rows[4];
    if (!row5 || !row5.Multimedia) {
        console.error('❌ No hay datos para re-render');
        return;
    }
    
    const multimedia = row5.Multimedia;
    const domRow = document.querySelector('#fila-5');
    
    if (domRow && typeof multimedia === 'string') {
        const multimediaIndex = window.catalogData.headers.indexOf('Multimedia') + 1;
        const multimediaCell = domRow.children[multimediaIndex];
        
        if (multimediaCell && multimedia.toLowerCase().endsWith('.mp4')) {
            console.log('🎬 Re-creando elemento video para MP4...');
            
            multimediaCell.innerHTML = `
                <div class="multimedia-preview">
                    <div class="video-thumbnail-container" style="position: relative; display: inline-block;">
                        <video 
                            src="${multimedia}" 
                            style="width: 80px; height: 60px; object-fit: cover; border-radius: 4px; cursor: pointer;"
                            onclick="showMultimediaModal('${multimedia}', '${multimedia.split('/').pop()}'); return false;"
                            onmouseover="this.style.opacity='0.8'"
                            onmouseout="this.style.opacity='1'"
                            preload="metadata">
                        </video>
                        <div class="play-button-overlay" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.7); color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; pointer-events: none;">
                            <i class="fas fa-play" style="font-size: 10px;"></i>
                        </div>
                    </div>
                </div>
            `;
            
            console.log('✅ Elemento video re-creado');
        }
    }
}

// Función de debug con reintentos inteligentes
function debugMP4Fila5WithRetry(maxRetries = 3, currentRetry = 0) {
    if (currentRetry >= maxRetries) {
        console.warn('⚠️ window.catalogData no disponible después de ' + maxRetries + ' intentos - página sin datos de catálogo');
        return;
    }
    
    if (!window.catalogData) {
        console.log(`🔄 Intento ${currentRetry + 1}/${maxRetries}: esperando window.catalogData...`);
        // Aumentar el tiempo de espera gradualmente
        const waitTime = 500 + (currentRetry * 500);
        setTimeout(() => debugMP4Fila5WithRetry(maxRetries, currentRetry + 1), waitTime);
        return;
    }
    
    // Si llegamos aquí, window.catalogData existe
    console.log('✅ window.catalogData encontrado, ejecutando debug...');
    debugMP4Fila5();
}

// Auto-ejecutar el debug cuando se carga la página (solo si estamos en una página de catálogo)
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en una página que debería tener catalogData
    const isRelevantPage = window.location.pathname.includes('/catalogs/') || 
                          window.location.pathname.includes('/ver_tabla/') ||
                          document.querySelector('[data-catalog-id]') ||
                          document.querySelector('.catalog-container') ||
                          document.querySelector('#catalog-data');
    
    if (isRelevantPage) {
        console.log('🔍 Página de catálogo detectada, iniciando debug MP4...');
        // Primer intento inmediato
        setTimeout(debugMP4Fila5WithRetry, 500);
    } else {
        console.log('📄 No es página de catálogo, omitiendo debug MP4 fila #5');
    }
});

// Hacer funciones globales para uso en consola
window.debugMP4Fila5 = debugMP4Fila5;
window.forceRenderMP4Fila5 = forceRenderMP4Fila5;
window.debugMP4Fila5WithRetry = debugMP4Fila5WithRetry;

// console.log('🎬 Debug MP4 Fila #5 listo. Usa debugMP4Fila5() y forceRenderMP4Fila5()');