
// SOLUCIÓN RÁPIDA - Pega esto en la consola del navegador:
(function() {
    const PROBLEMATIC_FILES = [
        'cf342a562c104122a5ca9241bf1ef896_oUcGqQXIG8InPCfTAIeSA2gneLBJnRIInz4jwY.MP4',
        'b1c79940ccb547d180b776aca15b1a40_como_usar_la_circular.MP4',
        'db2d78bfc1be4b6288330a3d895f6510_util_para_sierra_circular.MP4'
    ];
    
    // Limpiar localStorage
    Object.keys(localStorage).forEach(key => {
        const value = localStorage.getItem(key);
        if (value && PROBLEMATIC_FILES.some(file => value.includes(file))) {
            localStorage.removeItem(key);
            console.log('Removed from localStorage:', key);
        }
    });
    
    // Limpiar sessionStorage
    Object.keys(sessionStorage).forEach(key => {
        const value = sessionStorage.getItem(key);
        if (value && PROBLEMATIC_FILES.some(file => value.includes(file))) {
            sessionStorage.removeItem(key);
            console.log('Removed from sessionStorage:', key);
        }
    });
    
    // Limpiar catalogData
    if (window.catalogData && window.catalogData.rows) {
        window.catalogData.rows.forEach((row, index) => {
            Object.keys(row).forEach(key => {
                if (typeof row[key] === 'string' && PROBLEMATIC_FILES.some(file => row[key].includes(file))) {
                    row[key] = '';
                    console.log(`Cleaned row ${index + 1}, field ${key}`);
                }
            });
        });
    }
    
    console.log('✅ Problema MP4 solucionado. Recarga la página.');
    alert('Cache limpiado. Recarga la página.');
})();
