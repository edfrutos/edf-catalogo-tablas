# Ficha de TablaTeca en App Store Connect

Textos y respuestas listos para copiar en App Store Connect (edición Mac App Store, 100 % local, sin cuentas).
Los límites de caracteres son los de Apple y están comprobados. Lo marcado con **[DECIDIR]** o **[TUYO]** necesita una decisión o un dato del titular.

## 1. Datos de la app (ya fijados en el paquete)

| Campo | Valor |
|---|---|
| Nombre | TablaTeca |
| Bundle ID | `com.edefrutos.tablateca` |
| Versión de marketing | 1.0 (el build sube en cada subida: es el número de run) |
| Categoría principal | Productividad (`public.app-category.productivity`) |
| Categoría secundaria (opcional) | Negocios o Utilidades **[DECIDIR]** |
| macOS mínimo | 12.0 (solo Apple Silicon) |
| Copyright | © 2026 Eugenio de Frutos Sanchez |
| Idioma principal de la ficha | Español (España) |
| Idioma de la interfaz | Español (la ficha en inglés es opcional) |

## 2. Textos en español

**Nombre (≤30):** `TablaTeca` (9)

**Subtítulo (≤30):** `Tus catálogos con archivos` (26)

**Texto promocional (≤170):**
`Organiza tus catálogos y tablas con imágenes, documentos y vídeos en un solo lugar. Todo se guarda en tu Mac, sin cuentas ni conexión.` (134)

**Palabras clave (≤100, separadas por comas, sin espacios tras la coma):**
`catálogo,tablas,inventario,colección,documentos,PDF,imágenes,organizador,base de datos,archivos` (95)

**Descripción (≤4000):**

```
TablaTeca te permite crear catálogos y tablas a tu medida y guardar en cada fila todo lo que la acompaña: imágenes, documentos y vídeos.

Pensada para inventarios, colecciones, proyectos, fichas técnicas o cualquier lista que necesite algo más que texto.

QUÉ PUEDES HACER
• Crear catálogos con las columnas que necesites.
• Añadir filas con imágenes, documentos (PDF, texto y Markdown) y archivos multimedia.
• Ver las imágenes y los documentos sin salir de la app, con visor de PDF integrado.
• Poner una miniatura a cada catálogo para reconocerlo de un vistazo.
• Buscar y ordenar las filas de la tabla.
• Exportar tus catálogos en CSV o JSON.
• Crear una copia de seguridad completa en un archivo ZIP (catálogos, imágenes y documentos) y restaurarla cuando quieras.

TUS DATOS SON TUYOS
• Todo se guarda localmente en tu Mac.
• No hace falta crear una cuenta ni iniciar sesión.
• Funciona sin conexión a internet.
• No recopila datos personales ni usa analítica o publicidad.

Interfaz en español.
```

**Novedades de esta versión (≤4000):** `Primera versión en la Mac App Store.`

## 3. Textos en inglés (localización opcional)

**Name:** `TablaTeca` · **Subtitle (≤30):** `Catalogs & tables with files` (28)

**Promotional text (≤170):** `Organize your catalogs and tables with images, documents and videos in one place. Everything stays on your Mac: no account, no connection needed.` (145)

**Keywords (≤100):** `catalog,tables,inventory,collection,documents,PDF,images,organizer,database,files` (81)

**Description:**

```
TablaTeca lets you build your own catalogs and tables and keep everything related to each row right next to it: images, documents and videos.

Made for inventories, collections, projects, spec sheets, or any list that needs more than plain text.

WHAT YOU CAN DO
• Create catalogs with the columns you need.
• Add rows with images, documents (PDF, text and Markdown) and media files.
• View images and documents inside the app, with a built-in PDF viewer.
• Give each catalog a thumbnail so you can spot it at a glance.
• Search and sort the rows of a table.
• Export your catalogs as CSV or JSON.
• Create a full backup as a ZIP file (catalogs, images and documents) and restore it whenever you want.

YOUR DATA IS YOURS
• Everything is stored locally on your Mac.
• No account and no sign-in required.
• Works without an internet connection.
• It does not collect personal data or use analytics or advertising.

Interface in Spanish.
```

**What's New:** `First release on the Mac App Store.`

## 4. Privacidad

**Etiquetas de privacidad de la app (App Privacy):** «Data Not Collected» (no se recopila ningún dato). La app no envía datos a ningún servidor propio ni de terceros; no integra analítica, publicidad ni SDK de terceros. **Nota sobre Google Drive (opcional, apagado por defecto):** si el usuario lo conecta, la app sube las copias que él pide directamente a *su propio* Drive (alcance `drive.file`). El desarrollador no recibe ni puede acceder a esos datos, por lo que «Data Not Collected» sigue siendo coherente con la definición de Apple (datos que el desarrollador y/o sus socios pueden consultar). Es una interpretación mía: revísala al rellenar el cuestionario y, si dudas, consulta la guía de Apple sobre «Data Collection».

Antes de marcarlo, confirma con la build final que no hay tráfico saliente. Comprobación (con la app abierta y el Wi-Fi activo, unos minutos de uso; solo debe aparecer `127.0.0.1`):

```bash
while true; do clear; date; lsof -nP -i -a -c TablaTeca; sleep 5; done
```

Esa comprobación vale con Google Drive **sin conectar** (es opcional y está apagado por defecto). Si aparece cualquier IP que no sea `127.0.0.1`, avísame con la salida. Con el run 33 ya no hay CDN ni consulta de actualizaciones: la app solo habla con su propio servidor local en `127.0.0.1`.

**URL de la política de privacidad (obligatoria):** `https://catalogo.efjdev.com/privacidad` (ruta `/privacidad` de la propia app web, ES + EN; hay que desplegarla). Texto base:

```
Política de privacidad de TablaTeca
Última actualización: [fecha]

TablaTeca no recopila, almacena en servidores ni comparte ningún dato personal.
Toda la información que introduces (catálogos, filas, imágenes, documentos y archivos
multimedia) se guarda únicamente en tu Mac, dentro del contenedor de la aplicación, y
no se envía a ningún servidor. La app no requiere cuenta, no usa cookies de seguimiento,
analítica ni publicidad y funciona sin conexión a internet.
Puedes eliminar tus datos en cualquier momento borrando la carpeta de datos de la app
o desinstalándola.
Contacto: [correo de soporte]
```

(Versión en inglés: misma estructura; «TablaTeca does not collect, store on servers or share any personal data…».)

**URL de soporte (obligatoria):** `https://catalogo.efjdev.com/soporte` (formulario de contacto que ya existía en la app web). **URL de marketing:** opcional, puede quedar vacía.

## 5. Clasificación por edades

Responde «Ninguno» a todos los contenidos (violencia, sexo, juego, terror, alcohol/drogas, etc.). «Acceso web sin restricciones»: **No** (la app solo muestra contenido local). Resultado esperado: **4+**.

## 6. Cumplimiento de exportación (cifrado)

**Decidido por el titular:** `ITSAppUsesNonExemptEncryption = false` (ya fijado en `packaging/mas/TablaTeca_mas.spec`; desde el build 35 App Store Connect no volverá a preguntar). Es una declaración del titular: la edición de tienda no implementa cifrado propio.

El `Info.plist` **no** declara `ITSAppUsesNonExemptEncryption`, así que App Store Connect preguntará por esto en cada build (aparece como «Missing Compliance» en TestFlight).

Hechos: la edición de tienda solo usa HTTP local en `127.0.0.1` y no cifra datos propios; el intérprete de Python empaquetado incluye las bibliotecas estándar de TLS, aunque la app no las usa en esta edición.

Opciones:
1. Responder en la web en cada subida (sin cambios de código).
2. Declarar `ITSAppUsesNonExemptEncryption = false` en el `Info.plist` (se haría en `packaging/mas/TablaTeca_mas.spec`), una vez estés seguro de que es veraz. **No estoy seguro** de que las bibliotecas empaquetadas obliguen a otra respuesta: es una declaración legal tuya. Si hay dudas, consúltalo con Apple o con un asesor de exportación antes de fijarlo.

## 7. Notas para el revisor (App Review Information)

**Contacto de revisión [TUYO]:** nombre, correo y teléfono. **Cuenta de demostración:** no aplica (la app no tiene cuentas).

Texto para el campo «Notes» (en inglés):

```
TablaTeca is a local catalog/table manager. There is NO login or account: the app opens directly with a single local user. No demo account is needed.

How to test (about 2 minutes):
1. Open the app. The dashboard lists your catalogs (empty at first).
2. Click "Catálogos" > create a catalog with a few columns (e.g. Fecha, Nombre, Descripción, Documentación, Multimedia).
3. Open it and use "Añadir Fila" to add a row with an image, a PDF or text document and a video/audio file.
4. Click the thumbnails/document buttons to preview images, PDFs and Markdown inside the app.
5. Use the search box and column sorting; use Backups > CSV/JSON to export the catalog.
6. Backups > "Copia completa (ZIP)" saves a full backup; Backups > "Importar copia (ZIP)" restores it (it asks for confirmation and first stores an automatic copy of the current state).
7. Settings (top bar): owner profile, a folder for local backups (native folder picker, remembered between launches) and an optional Google Drive connection. You do not need to use Google Drive to review the app.

Data and privacy: everything is stored locally in the app sandbox container (SQLite database and an uploads folder). The app collects no data and works fully offline; the optional Google Drive backup sends data only from the user's Mac to the user's own Google account, never to the developer.

Entitlements: App Sandbox is enabled. com.apple.security.network.server and .client are used only for the app's own loopback connection (127.0.0.1) between its embedded web view and its local engine; by default the app makes no external network requests. The only exception is the optional Google Drive backup in Settings, off by default: if the user connects it, the app talks directly to Google (OAuth with the user's own credentials, "drive.file" scope only) to upload backups the user requests to the user's own Drive; the developer receives no data. com.apple.security.files.user-selected.read-write is used when the user picks files to attach to a row.

Why this is more than a website (Guideline 4.2): the app is a self-contained desktop application with a local database, local file storage, native file pickers, embedded document/image/media viewers, CSV/JSON export, full ZIP backup and restore, and full offline operation. It does not load a remote website; all resources ship inside the app.
```

**Riesgo conocido (Guideline 4.2, funcionalidad mínima):** la app es una interfaz web empaquetada (pywebview + Flask). El texto anterior defiende su valor local y offline; aun así Apple puede pedir más funciones «nativas». Ya incluye copia completa en ZIP (exportar/importar). Ya incluye también Ajustes (perfil, carpeta de copias y Google Drive opcional). Refuerzos posibles si lo piden: arrastrar y soltar archivos, atajos de teclado y menús de macOS.

## 8. Capturas de pantalla (Mac)

Obligatorio al menos 1 y máximo 10, en una de estas resoluciones (16:10): 1280×800, 1440×900, 2560×1600 o 2880×1800. Formato PNG o JPEG, sin transparencia. Capturas sugeridas, con datos de ejemplo no personales:
1. Dashboard con varios catálogos.
2. Vista de un catálogo con filas, imágenes y documentos.
3. Modal de imagen ampliada.
4. Visor de PDF abierto.
5. Formulario de «Añadir fila».
6. Exportación CSV/JSON (menú Backups).

Se pueden hacer con ⇧⌘5 sobre la ventana ajustada al tamaño elegido.

## 9. Lista de pasos en App Store Connect

1. Subir el build final con Transporter y esperar el procesamiento.
2. Crear la versión 1.0 de la app Mac, elegir el build y rellenar textos, capturas, URLs y categoría.
3. Rellenar *App Privacy* («Data Not Collected») y la clasificación por edades.
4. Responder el cumplimiento de exportación (apartado 6).
5. Pegar las notas del revisor (apartado 7) y los datos de contacto.
6. Precio: **gratuita** (decidido); elegir disponibilidad por territorios.
7. Revisar que los builds de pruebas antiguos están expirados en TestFlight.
8. Enviar a revisión.
