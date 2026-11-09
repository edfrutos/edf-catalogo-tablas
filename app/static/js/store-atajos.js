/*
 * Atajos de teclado y vista previa con la barra espaciadora (solo edición de tienda).
 *
 *   ⌘N   nueva fila (en la vista de una tabla)
 *   ⌘F   enfocar la búsqueda de la tabla
 *   ⌘B   menú de copias de seguridad (o ir al panel si no está en pantalla)
 *   ⌘,   Ajustes
 *   ↑ ↓  seleccionar fila de la tabla
 *   Espacio  vista previa del primer adjunto de la fila seleccionada
 *
 * Reutiliza los visores que ya existen (showImageModal, showMultimediaModal,
 * showDocumentModal): no añade ninguna ruta ni dependencia.
 */
(function () {
  "use strict";
  if (window.__tablatecaAtajos) return;
  window.__tablatecaAtajos = true;

  var CLASE_SELECCION = "fila-seleccionada-tt";
  var seleccionada = null;

  function inyectarEstilo() {
    var estilo = document.createElement("style");
    estilo.textContent =
      "tr." + CLASE_SELECCION + " > td { background-color: rgba(13,110,253,.12) !important; }" +
      "tr." + CLASE_SELECCION + " { outline: 2px solid rgba(13,110,253,.55); outline-offset: -2px; }";
    document.head.appendChild(estilo);
  }

  function esCampoEditable(el) {
    if (!el) return false;
    if (el.isContentEditable) return true;
    var tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
  }

  function hayModalAbierto() {
    return !!document.querySelector(".modal.show");
  }

  function filasVisibles() {
    var filas = document.querySelectorAll("#tablaFilas tbody tr");
    return Array.prototype.filter.call(filas, function (fila) {
      return fila.getClientRects().length > 0;
    });
  }

  function seleccionar(fila) {
    if (seleccionada) seleccionada.classList.remove(CLASE_SELECCION);
    seleccionada = fila || null;
    if (seleccionada) {
      seleccionada.classList.add(CLASE_SELECCION);
      if (seleccionada.scrollIntoView) seleccionada.scrollIntoView({ block: "nearest" });
    }
  }

  function moverSeleccion(delta) {
    var filas = filasVisibles();
    if (!filas.length) return false;
    var i = seleccionada ? filas.indexOf(seleccionada) : -1;
    if (i === -1) {
      i = delta > 0 ? 0 : filas.length - 1;
    } else {
      i = Math.min(filas.length - 1, Math.max(0, i + delta));
    }
    seleccionar(filas[i]);
    return true;
  }

  function disparadorVistaPrevia(fila) {
    var candidatos = fila.querySelectorAll("[onclick]");
    for (var i = 0; i < candidatos.length; i++) {
      var codigo = candidatos[i].getAttribute("onclick") || "";
      if (/show(Image|Multimedia|Document)Modal\s*\(/.test(codigo)) return candidatos[i];
    }
    return null;
  }

  function vistaPrevia() {
    if (!seleccionada || !document.body.contains(seleccionada)) return false;
    var disparador = disparadorVistaPrevia(seleccionada);
    if (!disparador) return false;
    disparador.click();
    return true;
  }

  function ir(url) {
    window.location.href = url;
  }

  function atajoConComando(tecla) {
    switch (tecla) {
      case "n":
        var nueva = document.querySelector('a[href*="/add-row/"], a[href*="agregar_fila"]');
        if (!nueva) return false;
        ir(nueva.getAttribute("href"));
        return true;
      case "f":
        var buscador = document.getElementById("searchInput");
        if (!buscador) return false;
        buscador.focus();
        buscador.select();
        return true;
      case "b":
        var menuCopias = document.getElementById("backupDropdown");
        if (menuCopias) {
          menuCopias.click();
        } else {
          ir("/admin/dashboard");
        }
        return true;
      case ",":
        ir("/ajustes");
        return true;
      default:
        return false;
    }
  }

  function alPulsarTecla(evento) {
    if (evento.defaultPrevented || evento.isComposing) return;

    if (evento.metaKey && !evento.ctrlKey && !evento.altKey && !evento.shiftKey) {
      if (hayModalAbierto()) return;
      if (atajoConComando(String(evento.key).toLowerCase())) evento.preventDefault();
      return;
    }

    if (evento.metaKey || evento.ctrlKey || evento.altKey) return;
    if (esCampoEditable(evento.target) || hayModalAbierto()) return;

    if (evento.key === "ArrowDown" && moverSeleccion(1)) {
      evento.preventDefault();
    } else if (evento.key === "ArrowUp" && moverSeleccion(-1)) {
      evento.preventDefault();
    } else if ((evento.key === " " || evento.code === "Space") && vistaPrevia()) {
      evento.preventDefault();
    }
  }

  function alHacerClic(evento) {
    var fila = evento.target.closest ? evento.target.closest("#tablaFilas tbody tr") : null;
    if (fila) seleccionar(fila);
  }

  function iniciar() {
    inyectarEstilo();
    document.addEventListener("keydown", alPulsarTecla);
    document.addEventListener("click", alHacerClic);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }

  // Acciones del menú nativo «Archivo»: el launcher las invoca por nombre y ejecutan
  // exactamente lo mismo que el atajo de teclado correspondiente.
  var ACCIONES_MENU = { "nueva-fila": "n", buscar: "f", copias: "b", ajustes: "," };
  window.tablatecaAccion = function (nombre) {
    var tecla = Object.prototype.hasOwnProperty.call(ACCIONES_MENU, nombre) ? ACCIONES_MENU[nombre] : null;
    return tecla ? atajoConComando(tecla) : false;
  };

  // Expuesto solo para pruebas.
  window.__tablatecaAtajosTest = { seleccionar: seleccionar, vistaPrevia: vistaPrevia, filasVisibles: filasVisibles };
})();
