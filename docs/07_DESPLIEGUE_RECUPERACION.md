# Despliegue y recuperación

## Repositorio

Repositorio actual (remoto `origin`, HTTPS — permite push/pull directo desde cualquier sandbox sin
configurar claves SSH):

```text
https://github.com/edfrutos/edf-catalogo-tablas.git
```

## Rama de trabajo

`main`. La rama `trabajo-local-catalogo-20260510` usada en la consolidación de 2026-05-10 ya fue
integrada y no está activa.

## Producción

- **Ruta**: `/var/www/vhosts/edefrutos2020.com/edf_catalogotablas`
- **Servicio**: systemd `catalogotablas.service`, escucha en `127.0.0.1:5100`
- **Python**: 3.10.13 (compilado con `pyenv`; el PPA deadsnakes de apt no funcionaba en el servidor
  Ubuntu 20.04/Plesk)
- Producción es un clon git real (`git init` + `remote add origin` + `git reset --hard origin/main`)
  sincronizado con este repositorio.

## Recomendación

Antes de limpiezas o refactorizaciones importantes, crear una rama específica y validar la aplicación antes del commit.
