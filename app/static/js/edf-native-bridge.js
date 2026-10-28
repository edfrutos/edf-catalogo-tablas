/* edf-native-bridge.js - puente JS <-> pywebview: enlaces externos y descargas nativas */
(function () {
  'use strict';
  if (window.__edfBridgeLoaded) return;
  window.__edfBridgeLoaded = true;
  var MEDIA = ['/static/uploads/', '/admin/s3/', '/imagenes_subidas/', '/admin/backup/'];
  var BACKUP = /^\/admin\/backup\/(csv|json)$/;

  function api() { return window.pywebview && window.pywebview.api ? window.pywebview.api : null; }
  function toURL(u) { try { return new URL(u, window.location.href); } catch (e) { return null; } }
  function isMedia(u) {
    return !!u && u.origin === window.location.origin &&
      MEDIA.some(function (p) { return u.pathname.indexOf(p) === 0; });
  }
  function isExternal(u) {
    return !!u && /^https?:$/.test(u.protocol) && u.origin !== window.location.origin;
  }

  var S3 = '/admin/s3/';

  // Los archivos de /admin/s3/ exigen sesión: lo que se abre fuera de la ventana (Chrome)
  // o se descarga desde Python no la comparte, así que se pide antes una URL firmada.
  function withToken(u) {
    if (u.pathname.indexOf(S3) !== 0) return Promise.resolve(u.href);
    return fetch('/admin/s3-link/' + u.pathname.slice(S3.length), { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (d) { return d.url + (u.search ? '&' + u.search.slice(1) : ''); })
      .catch(function () { return u.href; });
  }

  window.edfOpenExternal = function (url) {
    var a = api(), u = toURL(url);
    if (a && a.open_external && u && (isMedia(u) || isExternal(u))) {
      (isMedia(u) ? withToken(u) : Promise.resolve(u.href)).then(function (h) { a.open_external(h); });
      return true;
    }
    return false;
  };

  window.edfNativeSave = function (url, name) {
    var a = api(), u = toURL(url);
    if (a && a.save_file && isMedia(u)) {
      withToken(u).then(function (h) { a.save_file(h, name || ''); });
      return true;
    }
    return false;
  };

  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!el) return;
    var u = toURL(el.getAttribute('href'));
    if (!u || !/^https?:$/.test(u.protocol)) return;
    // Copias CSV/JSON: la ventana nativa no descarga por navegación; se guarda con el diálogo del sistema
    if (u.origin === window.location.origin && BACKUP.test(u.pathname)) {
      if (window.edfNativeSave(u.href, 'catalog_backup.' + u.pathname.split('/').pop())) { e.preventDefault(); e.stopPropagation(); }
      return;
    }
    if (el.hasAttribute('download')) {
      if (window.edfNativeSave(u.href, el.getAttribute('download'))) { e.preventDefault(); e.stopPropagation(); }
      return;
    }
    if (el.target === '_blank') {
      if (window.edfOpenExternal(u.href)) { e.preventDefault(); e.stopPropagation(); }
    }
  }, true);
})();
