/*
 * Arrastrar y soltar archivos desde Finder (solo edición de tienda).
 *
 * En los formularios de añadir y editar fila reparte los archivos soltados entre los
 * campos de archivo que ya existen (imágenes, multimedia, documentos) según el atributo
 * ``accept`` de cada uno. NO envía nada: el usuario revisa y pulsa «Guardar», así que el
 * guardado sigue pasando por la misma ruta de siempre.
 *
 * Fuera de esos formularios solo evita que WKWebView abra el archivo soltado dentro de la
 * ventana (sustituiría la interfaz de la app) y avisa de cómo adjuntar.
 */
(function () {
  "use strict";
  if (window.__tablatecaArrastrar) return;
  window.__tablatecaArrastrar = true;

  var TOAST_ID = "tt-aviso-arrastrar";
  var OVERLAY_ID = "tt-zona-arrastrar";
  var contador = 0;
  var temporizador = null;

  // ---------------------------------------------------------------- utilidades
  function traeArchivos(evento) {
    var dt = evento.dataTransfer;
    if (!dt || !dt.types) return false;
    return Array.prototype.indexOf.call(dt.types, "Files") !== -1;
  }

  function coincide(accept, archivo) {
    if (!accept) return true;
    var nombre = (archivo.name || "").toLowerCase();
    var tipo = (archivo.type || "").toLowerCase();
    return accept.split(",").some(function (ficha) {
      ficha = ficha.trim().toLowerCase();
      if (!ficha) return false;
      if (ficha.charAt(0) === ".") return nombre.slice(-ficha.length) === ficha;
      if (ficha.slice(-2) === "/*") return tipo.indexOf(ficha.slice(0, -1)) === 0;
      return tipo === ficha;
    });
  }

  function esCampoDeAdjuntos(input) {
    var nombre = input.getAttribute("name") || "";
    if (input.disabled || nombre.indexOf("miniatura") === 0) return false;
    return nombre === "images" || /_file(_\d+)?$/.test(nombre);
  }

  function camposDeAdjuntos() {
    var todos = document.querySelectorAll('form input[type="file"]');
    var campos = Array.prototype.filter.call(todos, esCampoDeAdjuntos);
    // Las imágenes van primero al campo «images»; el resto, en el orden de la página.
    return campos.sort(function (a, b) {
      return (b.name === "images") - (a.name === "images");
    });
  }

  function cabe(input) {
    return input.multiple || !input.files || input.files.length === 0;
  }

  function colocar(archivo, campos) {
    for (var i = 0; i < campos.length; i++) {
      var campo = campos[i];
      if (!coincide(campo.getAttribute("accept"), archivo) || !cabe(campo)) continue;
      var lote = new DataTransfer();
      Array.prototype.forEach.call(campo.files || [], function (f) { lote.items.add(f); });
      lote.items.add(archivo);
      campo.files = lote.files;
      campo.dispatchEvent(new Event("change", { bubbles: true }));
      return campo;
    }
    return null;
  }

  // ------------------------------------------------------------------------ UI
  function superposicion() {
    var el = document.getElementById(OVERLAY_ID);
    if (el) return el;
    el = document.createElement("div");
    el.id = OVERLAY_ID;
    el.setAttribute("aria-hidden", "true");
    el.style.cssText =
      "position:fixed;inset:0;z-index:20000;display:none;align-items:center;justify-content:center;" +
      "background:rgba(13,110,253,.18);border:4px dashed rgba(13,110,253,.8);" +
      "font:600 1.4rem -apple-system,system-ui,sans-serif;color:#0b5ed7;pointer-events:none;";
    el.textContent = "Suelta los archivos para adjuntarlos";
    document.body.appendChild(el);
    return el;
  }

  function mostrarZona(visible) {
    if (!visible) {
      var existente = document.getElementById(OVERLAY_ID);
      if (existente) existente.style.display = "none";
      return;
    }
    superposicion().style.display = "flex";
  }

  function avisar(texto, tipo) {
    var el = document.getElementById(TOAST_ID);
    if (!el) {
      el = document.createElement("div");
      el.id = TOAST_ID;
      el.setAttribute("role", "status");
      el.style.cssText = "position:fixed;left:50%;bottom:1.5rem;transform:translateX(-50%);z-index:20001;max-width:90vw;";
      document.body.appendChild(el);
    }
    el.className = "alert alert-" + tipo + " shadow";
    el.textContent = texto;
    el.style.display = "block";
    clearTimeout(temporizador);
    temporizador = setTimeout(function () { el.style.display = "none"; }, 9000);
  }

  // ------------------------------------------------------------------ eventos
  function alEntrar(evento) {
    if (!traeArchivos(evento)) return;
    evento.preventDefault();
    contador++;
    if (camposDeAdjuntos().length) mostrarZona(true);
  }

  function alSalir(evento) {
    if (!traeArchivos(evento)) return;
    contador = Math.max(0, contador - 1);
    if (contador === 0) mostrarZona(false);
  }

  function alPasarPor(evento) {
    if (!traeArchivos(evento)) return;
    evento.preventDefault();
    if (evento.dataTransfer) evento.dataTransfer.dropEffect = "copy";
  }

  function alSoltar(evento) {
    if (!traeArchivos(evento)) return;
    evento.preventDefault();
    contador = 0;
    mostrarZona(false);

    var archivos = Array.prototype.slice.call(evento.dataTransfer.files || []);
    if (!archivos.length) return;
    var campos = camposDeAdjuntos();
    if (!campos.length) {
      avisar("Para adjuntar archivos, abre «Añadir fila» o «Editar» en una fila y arrástralos allí.", "info");
      return;
    }

    var puestos = 0;
    var rechazados = [];
    archivos.forEach(function (archivo) {
      if (colocar(archivo, campos)) puestos++; else rechazados.push(archivo.name);
    });

    if (puestos && !rechazados.length) {
      avisar(puestos + (puestos === 1 ? " archivo preparado" : " archivos preparados") +
        ". Pulsa «Guardar» para confirmarlos.", "success");
    } else if (puestos) {
      avisar(puestos + " preparado(s). No se han podido colocar: " + rechazados.join(", ") + ".", "warning");
    } else {
      avisar("Este formulario no admite ese tipo de archivo: " + rechazados.join(", ") + ".", "warning");
    }
  }

  function iniciar() {
    document.addEventListener("dragenter", alEntrar);
    document.addEventListener("dragleave", alSalir);
    document.addEventListener("dragover", alPasarPor);
    document.addEventListener("drop", alSoltar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
