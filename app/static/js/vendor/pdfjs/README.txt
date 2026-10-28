pdf.js (pdfjs-dist 3.11.174, build legacy) - Apache License 2.0 - https://github.com/mozilla/pdf.js
Se usa para dibujar los PDF dentro del modal porque el visor integrado de WKWebView
los muestra como una página diminuta dentro del iframe.

Además (pdfjs-dist 3.11.174, mismo origen):
- cmaps/          CMaps de Adobe (BSD-3-Clause, ver cabeceras del propio pdf.js).
- standard_fonts/ Fuentes estándar de sustitución: Foxit (LICENSE_FOXIT) y
                  Liberation Sans (LICENSE_LIBERATION).
Se usan para PDF con fuentes no embebidas; con disableFontFace los glifos se dibujan
como trazados, sin depender de FontFace en WKWebView.
