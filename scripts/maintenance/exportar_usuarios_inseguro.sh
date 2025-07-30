#!/bin/bash
# Script: exportar_usuarios_inseguro.sh
# Descripción: Ejecuta la exportación de usuarios desactivando la verificación de certificados SSL (solo para pruebas).
# Uso: bash tools/exportar_usuarios_inseguro.sh
# Autor: EDF EDF Equipo de desarrollo - 2024-05-28

cat <<EOF

[AVISO DE INSEGURIDAD]
--------------------------------------------------
La verificación de certificados SSL está DESACTIVADA.
Esto es INSEGURO y solo debe usarse para pruebas puntuales.
No uses esta opción en producción.
--------------------------------------------------

EOF

MONGO_ALLOW_INVALID_CERTS=true python3 tools/exportar_usuarios.py 