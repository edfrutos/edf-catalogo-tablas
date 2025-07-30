// Script de diagnóstico mejorado para verificar elementos del dashboard
// Versión optimizada con mejores funcionalidades y rendimiento

/* global Blob, URL, MutationObserver */

console.log("=== DIAGNÓSTICO DASHBOARD INICIADO (VERSIÓN MEJORADA) ===");

// Configuración del diagnóstico
const DIAGNOSTICO_CONFIG = {
    autoEjecutar: true,
    intervaloActualizacion: 5000, // 5 segundos
    mostrarEnConsola: true,
    mostrarEnPagina: true,
    elementos: {
        "#restoreDriveBtn": "Botón Restaurar Google Drive",
        "#restoreDriveModal": "Modal Google Drive",
        "#backupBtn": "Botón Backup",
        "#restoreBtn": "Botón Restaurar",
        "#backupSection": "Sección Backup",
        ".backup-section": "Sección Backup (clase)",
        "[data-bs-target='#restoreDriveModal']": "Trigger Modal Drive",
        "#driveBackupsLoading": "Indicador carga Drive",
        "#driveBackupsList": "Lista backups Drive",
        "#systemStatusCard": "Tarjeta estado sistema",
        "#memoriaUsage": "Indicador memoria",
        "#refreshDriveBackupsBtn": "Botón actualizar Drive"
    },
    funcionesGlobales: [
        "initializeFoundElements",
        "waitForButtons", 
        "showRestoreDriveModal",
        "createAndUploadBackup",
        "openDriveFolder",
        "loadSystemStatus",
        "updateSystemStatusUI",
        "ejecutarDiagnostico"
    ]
};

// Estado del diagnóstico
let diagnosticoState = {
    ultimaEjecucion: null,
    resultados: {},
    intervalId: null,
    panelVisible: false
};

// Función principal de verificación mejorada
function verificarElementosDashboard() {
    console.log("🔍 Verificando elementos del dashboard (versión mejorada)...");
    
    const resultados = {
        elementos: {},
        estructura: {},
        eventos: {},
        funciones: {},
        timestamp: new Date().toISOString(),
        resumen: {
            elementosEncontrados: 0,
            elementosVisibles: 0,
            funcionesDisponibles: 0,
            errores: []
        }
    };
    
    // Verificar elementos con descripciones mejoradas
    Object.keys(DIAGNOSTICO_CONFIG.elementos).forEach(selector => {
        try {
            const elemento = $(selector);
            const encontrado = elemento.length > 0;
            const visible = encontrado ? elemento.is(":visible") : false;
            const descripcion = DIAGNOSTICO_CONFIG.elementos[selector];
            
            resultados.elementos[selector] = {
                descripcion: descripcion,
                encontrado: encontrado,
                cantidad: elemento.length,
                visible: visible,
                atributos: encontrado ? {
                    id: elemento.attr("id") || "N/A",
                    clases: elemento.attr("class") || "N/A",
                    texto: elemento.text().substring(0, 50) + (elemento.text().length > 50 ? "..." : "")
                } : null
            };
            
            if (encontrado) resultados.resumen.elementosEncontrados++;
            if (visible) resultados.resumen.elementosVisibles++;
            
            if (DIAGNOSTICO_CONFIG.mostrarEnConsola) {
                console.log(`${selector} (${descripcion}):`, {
                    encontrado: encontrado ? "✅" : "❌",
                    visible: visible ? "✅" : "❌",
                    cantidad: elemento.length
                });
            }
        } catch (error) {
            resultados.resumen.errores.push(`Error verificando ${selector}: ${error.message}`);
            console.error(`Error verificando ${selector}:`, error);
        }
    });
    
    // Verificar estructura del DOM mejorada
    resultados.estructura = {
        totalElementos: $("*").length,
        totalBotones: $("button").length,
        totalModales: $(".modal").length,
        elementosBackup: $("[id*='backup']").length,
        elementosRestore: $("[id*='restore']").length,
        elementosDrive: $("[id*='drive']").length,
        elementosConEventos: 0
    };
    
    // Verificar eventos mejorado
    try {
        const restoreDriveBtn = $("#restoreDriveBtn");
        if (restoreDriveBtn.length > 0) {
            const eventos = $._data(restoreDriveBtn[0], "events");
            resultados.eventos.restoreDriveBtn = eventos || "Sin eventos";
            if (eventos) resultados.estructura.elementosConEventos++;
        }
    } catch (e) {
        resultados.resumen.errores.push(`Error verificando eventos: ${e.message}`);
    }
    
    // Verificar funciones globales mejorado
    DIAGNOSTICO_CONFIG.funcionesGlobales.forEach(func => {
        const disponible = typeof window[func] === "function";
        resultados.funciones[func] = disponible;
        if (disponible) resultados.resumen.funcionesDisponibles++;
        
        if (DIAGNOSTICO_CONFIG.mostrarEnConsola) {
            console.log(`${func}: ${disponible ? "✅" : "❌"}`);
        }
    });
    
    // Verificaciones adicionales de salud del sistema
    resultados.saludSistema = verificarSaludSistema();
    
    diagnosticoState.resultados = resultados;
    diagnosticoState.ultimaEjecucion = new Date();
    
    if (DIAGNOSTICO_CONFIG.mostrarEnConsola) {
        console.log("📊 Resumen del diagnóstico:", resultados.resumen);
        if (resultados.resumen.errores.length > 0) {
            console.warn("⚠️ Errores encontrados:", resultados.resumen.errores);
        }
    }
    
    return resultados;
}

// Nueva función para verificar salud del sistema
function verificarSaludSistema() {
    const salud = {
        jqueryDisponible: typeof $ !== "undefined",
        bootstrapDisponible: typeof bootstrap !== "undefined",
        datatablesCargado: typeof $.fn.DataTable !== "undefined",
        consolaFuncional: typeof console !== "undefined",
        localStorageDisponible: typeof localStorage !== "undefined",
        sessionStorageDisponible: typeof sessionStorage !== "undefined"
    };
    
    salud.puntuacion = Object.values(salud).filter(Boolean).length;
    salud.total = Object.keys(salud).length - 2; // Excluir puntuacion y total
    
    return salud;
}

// Función mejorada para mostrar resultados en la página
function mostrarResultadosEnPagina() {
    if (!DIAGNOSTICO_CONFIG.mostrarEnPagina) return;
    
    const resultados = diagnosticoState.resultados;
    if (!resultados) return;
    
    // Crear o actualizar div de resultados
    let resultadosDiv = $("#diagnostico-resultados");
    if (resultadosDiv.length === 0) {
        resultadosDiv = $(`<div id="diagnostico-resultados" style="
            position: fixed; 
            top: 10px; 
            right: 10px; 
            background: white; 
            border: 2px solid #007bff; 
            border-radius: 8px; 
            padding: 15px; 
            max-width: 450px; 
            max-height: 80vh;
            overflow-y: auto;
            z-index: 9999; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        "></div>`);
        $("body").append(resultadosDiv);
    }
    
    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h5 style="color: #007bff; margin: 0;">🔍 Diagnóstico Dashboard</h5>
            <div>
                <button id="minimizar-diagnostico" style="margin-right: 5px; padding: 2px 6px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">−</button>
                <button id="cerrar-diagnostico" style="padding: 2px 6px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">×</button>
            </div>
        </div>
    `;
    
    // Resumen ejecutivo
    const resumen = resultados.resumen;
    const saludSistema = resultados.saludSistema;
    html += `
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 12px;">
            <strong>📈 Resumen:</strong><br>
            • Elementos: ${resumen.elementosEncontrados}/${Object.keys(DIAGNOSTICO_CONFIG.elementos).length} encontrados, ${resumen.elementosVisibles} visibles<br>
            • Funciones: ${resumen.funcionesDisponibles}/${DIAGNOSTICO_CONFIG.funcionesGlobales.length} disponibles<br>
            • Salud sistema: ${saludSistema.puntuacion}/${saludSistema.total} ✅<br>
            • Última actualización: ${new Date(resultados.timestamp).toLocaleTimeString()}
        </div>
    `;
    
    // Errores si los hay
    if (resumen.errores.length > 0) {
        html += `
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; border-radius: 4px; margin-bottom: 10px; font-size: 11px;">
                <strong>⚠️ Advertencias:</strong><br>
                ${resumen.errores.map(error => `• ${error}`).join("<br>")}
            </div>
        `;
    }
    
    // Detalles de elementos (colapsable)
    html += `
        <div id="detalles-elementos" style="display: none;">
            <h6 style="color: #495057; margin: 10px 0 5px 0; font-size: 13px;">📋 Elementos verificados:</h6>
            <div style="font-size: 11px; line-height: 1.3; max-height: 200px; overflow-y: auto;">
    `;
    
    Object.keys(resultados.elementos).forEach(selector => {
        const elemento = resultados.elementos[selector];
        const icono = elemento.encontrado ? (elemento.visible ? "✅" : "👁️") : "❌";
        const estado = elemento.encontrado ? (elemento.visible ? "visible" : "oculto") : "no encontrado";
        html += `<div style="margin-bottom: 3px;"><strong>${elemento.descripcion}:</strong> ${icono} (${estado})</div>`;
    });
    
    html += "</div></div>";
    
    // Botones de acción
    html += `
        <div style="margin-top: 15px; display: flex; gap: 5px; flex-wrap: wrap;">
            <button id="toggle-detalles" style="padding: 4px 8px; background: #17a2b8; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">Ver detalles</button>
            <button id="actualizar-diagnostico" style="padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">Actualizar</button>
            <button id="exportar-diagnostico" style="padding: 4px 8px; background: #ffc107; color: black; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">Exportar</button>
            <button id="toggle-auto-refresh" style="padding: 4px 8px; background: ${diagnosticoState.intervalId ? "#dc3545" : "#6f42c1"}; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">
                ${diagnosticoState.intervalId ? "Parar auto" : "Auto refresh"}
            </button>
        </div>
    `;
    
    resultadosDiv.html(html);
    diagnosticoState.panelVisible = true;
    
    // Event listeners mejorados
    configurarEventListeners();
}

// Configurar event listeners
function configurarEventListeners() {
    // Cerrar panel
    $("#cerrar-diagnostico").off("click").on("click", function() {
        $("#diagnostico-resultados").remove();
        diagnosticoState.panelVisible = false;
        if (diagnosticoState.intervalId) {
            clearInterval(diagnosticoState.intervalId);
            diagnosticoState.intervalId = null;
        }
    });
    
    // Minimizar panel
    $("#minimizar-diagnostico").off("click").on("click", function() {
        const detalles = $("#detalles-elementos");
        const botones = $(this).parent().parent().find("div").last();
        if (detalles.is(":visible") || botones.is(":visible")) {
            detalles.hide();
            botones.hide();
            $(this).text("+");
        } else {
            botones.show();
            $(this).text("−");
        }
    });
    
    // Toggle detalles
    $("#toggle-detalles").off("click").on("click", function() {
        const detalles = $("#detalles-elementos");
        if (detalles.is(":visible")) {
            detalles.hide();
            $(this).text("Ocultar detalles");
        } else {
            detalles.show();
            $(this).text("Ver detalles");
        }
    });
    
    // Actualizar diagnóstico
    $("#actualizar-diagnostico").off("click").on("click", function() {
        ejecutarDiagnostico();
    });
    
    // Exportar diagnóstico
    $("#exportar-diagnostico").off("click").on("click", function() {
        exportarDiagnostico();
    });
    
    // Toggle auto refresh
    $("#toggle-auto-refresh").off("click").on("click", function() {
        toggleAutoRefresh();
    });
}

// Nueva función para exportar diagnóstico
function exportarDiagnostico() {
    if (!diagnosticoState.resultados) {
        alert("No hay resultados de diagnóstico para exportar");
        return;
    }
    
    const datos = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        diagnostico: diagnosticoState.resultados
    };
    
    const blob = new Blob([JSON.stringify(datos, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diagnostico_dashboard_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log("📁 Diagnóstico exportado exitosamente");
}

// Nueva función para toggle auto refresh
function toggleAutoRefresh() {
    if (diagnosticoState.intervalId) {
        clearInterval(diagnosticoState.intervalId);
        diagnosticoState.intervalId = null;
        console.log("⏹️ Auto-refresh desactivado");
    } else {
        diagnosticoState.intervalId = setInterval(() => {
            if (diagnosticoState.panelVisible) {
                verificarElementosDashboard();
                mostrarResultadosEnPagina();
            }
        }, DIAGNOSTICO_CONFIG.intervaloActualizacion);
        console.log(`🔄 Auto-refresh activado (cada ${DIAGNOSTICO_CONFIG.intervaloActualizacion/1000}s)`);
    }
    
    // Actualizar botón
    const boton = $("#toggle-auto-refresh");
    if (diagnosticoState.intervalId) {
        boton.css("background", "#dc3545").text("Parar auto");
    } else {
        boton.css("background", "#6f42c1").text("Auto refresh");
    }
}

// Función principal mejorada
function ejecutarDiagnostico() {
    console.log("🚀 Ejecutando diagnóstico completo...");
    const resultados = verificarElementosDashboard();
    if (DIAGNOSTICO_CONFIG.mostrarEnPagina) {
        mostrarResultadosEnPagina();
    }
    return resultados;
}

// Inicialización mejorada
$(document).ready(function() {
    console.log("📋 DOM listo, inicializando diagnóstico mejorado...");
    
    // Esperar un poco para que se carguen todos los elementos
    setTimeout(() => {
        if (DIAGNOSTICO_CONFIG.autoEjecutar) {
            ejecutarDiagnostico();
        }
    }, 1000);
    
    // Detectar cambios en el DOM
    if (typeof MutationObserver !== "undefined") {
        const observer = new MutationObserver(function(mutations) {
            let shouldUpdate = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
                    // Verificar si se agregaron elementos relevantes
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType === 1) { // Element node
                            const element = $(node);
                            if (element.is("button") || element.find("button").length > 0 || 
                                element.is(".modal") || element.find(".modal").length > 0) {
                                shouldUpdate = true;
                                break;
                            }
                        }
                    }
                }
            });
            
            if (shouldUpdate && diagnosticoState.panelVisible) {
                console.log("🔄 Cambios detectados en el DOM, actualizando diagnóstico...");
                setTimeout(ejecutarDiagnostico, 500);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log("👁️ Observer de DOM configurado");
    }
});

// Funciones globales mejoradas
window.ejecutarDiagnostico = ejecutarDiagnostico;
window.diagnosticoConfig = DIAGNOSTICO_CONFIG;
window.diagnosticoState = diagnosticoState;

// Función para configuración rápida
window.configurarDiagnostico = function(opciones) {
    Object.assign(DIAGNOSTICO_CONFIG, opciones);
    console.log("⚙️ Configuración actualizada:", DIAGNOSTICO_CONFIG);
};

// Función para obtener estado actual
window.obtenerEstadoDiagnostico = function() {
    return {
        config: DIAGNOSTICO_CONFIG,
        state: diagnosticoState,
        ultimosResultados: diagnosticoState.resultados
    };
};

console.log("✅ Script de diagnóstico mejorado cargado completamente");
console.log("🎯 Funciones disponibles: ejecutarDiagnostico(), configurarDiagnostico(opciones), obtenerEstadoDiagnostico()");
console.log("=== FIN DIAGNÓSTICO DASHBOARD MEJORADO ===");