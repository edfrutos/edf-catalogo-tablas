# Documentos, imágenes y multimedia

## Documentos

Las URLs externas se guardan como enlaces.

Cuando una URL externa apunta a una página web normal, no se fuerza su visualización dentro del modal. En su lugar se muestra una ficha con botón para abrir en nueva pestaña.

Los documentos tipo PDF, TXT o Markdown pueden intentarse visualizar dentro del modal.

## Multimedia

El modal multimedia permite visualizar vídeos, audio e imágenes.

El tamaño del modal se ha ajustado para mejorar la visualización de vídeos por URL y YouTube.

## Limitación conocida

Muchas webs externas impiden ser mostradas dentro de un `iframe` por seguridad mediante cabeceras como:

- `X-Frame-Options`
- `Content-Security-Policy`

Esto no es un error de Flask ni del código de la aplicación.
