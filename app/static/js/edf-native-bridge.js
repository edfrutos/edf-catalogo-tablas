/* edf-native-bridge.js - puente JS <-> pywebview: enlaces externos y descargas nativas */
(function () {
  'use strict';
  var MEDIA = ['/static/uploads/', '/admin/s3/', '/imagenes_subidas/'];

  function api() { return window.pywebview && window.pywebview.api ? window.pywebview.api : null; }
  function toURL(u) { try { return new URL(u, window.location.href); } catch (e) { return null; } }
  function isMedia(u) {
    return !!u && u.origin === window.location.origin &&
      MEDIA.some(function (p) { return u.pathname.indexOf(p) === 0; });
  }
  function isExternal(u) {
    return !!u && /^https?:$/.test(u.protocol) && u.origin !== window.location.origin;
  }

  window.edfOpenExternal = function (url) {
    var a = api(), u = toURL(url);
    if (a && a.open_external && u && (isMedia(u) || isExternal(u))) { a.open_external(u.href); return true; }
    return false;
  };

  window.edfNativeSave = function (url, name) {
    var a = api(), u = toURL(url);
    if (a && a.save_file && isMedia(u)) { a.save_file(u.href, name || ''); return true; }
    return false;
  };

  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!el) return;
    var u = toURL(el.getAttribute('href'));
    if (!u || !/^https?:$/.test(u.protocol)) return;
    if (el.hasAttribute('download')) {
      if (window.edfNativeSave(u.href, el.getAttribute('download'))) { e.preventDefault(); e.stopPropagation(); }
      return;
    }
    if (el.target === '_blank') {
      if (window.edfOpenExternal(u.href)) { e.preventDefault(); e.stopPropagation(); }
    }
  }, true);
})();
