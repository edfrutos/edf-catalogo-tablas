# Uso de catálogos y tablas

## Vistas principales

- Vista usuario: `/ver_tabla/<id>`
- Vista catálogo: `/catalogs/<id>`
- Vista administración: `/admin/catalogo/<collection>/<id>`

## Operaciones habituales

- Crear catálogo.
- Añadir fila.
- Editar fila.
- Asociar imágenes.
- Asociar documentos.
- Asociar multimedia.

## Nota sobre `data` y `rows`

La fuente principal de filas debe ser `data`.

`rows` se conserva por compatibilidad, pero no debe sobrescribir `data` cuando `data` contiene información más actualizada.
