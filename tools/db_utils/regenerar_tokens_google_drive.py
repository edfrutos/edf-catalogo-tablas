#!/usr/bin/env python3
# Script: regenerar_tokens_google_drive.py
# Descripción: Regenera de una sola pasada OAuth los DOS artefactos de token que
#              usa la integración de Google Drive de este proyecto:
#                - token.pickle  -> google_drive_utils_v2.py y la rama
#                                   googleapiclient de google_drive_utils.py
#                - token.json    -> get_drive() (PyDrive2 / oauth2client) de
#                                   google_drive_utils.py
# Uso: python3 tools/db_utils/regenerar_tokens_google_drive.py
# Requiere: google-auth-oauthlib (ya en requirements.txt). credentials.json en
#           esta misma carpeta; si no está, se copia del client_secret_*.json
#           de la raíz del repo.
# Autor: EDF Developer - 2026-09-03
"""Regenera token.pickle y token.json para Google Drive.

Contexto: la integración de Drive tiene dos módulos con dos formatos de token
(ver README_google_drive.md). Mantener los dos sincronizados a mano es una
fuente de errores; este script hace UN solo flujo de consentimiento OAuth y
escribe ambos.

Tras ejecutarlo en local, copia AMBOS al servidor:

    scp -P 2222 tools/db_utils/token.pickle tools/db_utils/token.json \\
        root@208.76.221.20:/var/www/vhosts/edefrutos2020.com/edf_catalogotablas/tools/db_utils/
"""

from __future__ import annotations

import json
import pickle
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[1]

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

CREDENTIALS = BASE / "credentials.json"
TOKEN_PICKLE = BASE / "token.pickle"
TOKEN_JSON = BASE / "token.json"


def ensure_credentials() -> None:
    """Garantiza tools/db_utils/credentials.json; si falta, lo copia del
    client_secret_*.json de la raíz del repo."""
    if CREDENTIALS.exists():
        return
    candidates = sorted(REPO_ROOT.glob("client_secret_*.json"))
    if not candidates:
        sys.exit(
            f"❌ No hay {CREDENTIALS} ni ningún client_secret_*.json en {REPO_ROOT}.\n"
            "   Descarga las credenciales OAuth de escritorio de Google Cloud Console\n"
            f"   y guárdalas como {CREDENTIALS}."
        )
    shutil.copy2(candidates[0], CREDENTIALS)
    print(f"✓ credentials.json copiado desde {candidates[0].name}")


def write_token_json(creds) -> None:
    """Traduce unas credenciales google-auth al formato oauth2client que
    PyDrive2 (`LoadCredentialsFile`) espera en token.json."""
    expiry = creds.expiry.strftime("%Y-%m-%dT%H:%M:%SZ") if creds.expiry else None
    scopes = list(creds.scopes or SCOPES)
    payload = {
        "access_token": creds.token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "token_expiry": expiry,
        "token_uri": creds.token_uri or "https://oauth2.googleapis.com/token",
        "user_agent": None,
        "revoke_uri": "https://oauth2.googleapis.com/revoke",
        "id_token": None,
        "id_token_jwt": None,
        "token_response": {
            "access_token": creds.token,
            "expires_in": 3599,
            "refresh_token": creds.refresh_token,
            "scope": " ".join(scopes),
            "token_type": "Bearer",
        },
        "scopes": scopes,
        "token_info_uri": "https://oauth2.googleapis.com/tokeninfo",
        "invalid": False,
        "_class": "OAuth2Credentials",
        "_module": "oauth2client.client",
    }
    TOKEN_JSON.write_text(json.dumps(payload, indent=2))


def main() -> int:
    from google_auth_oauthlib.flow import InstalledAppFlow

    ensure_credentials()

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), scopes=SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    with open(TOKEN_PICKLE, "wb") as fh:
        pickle.dump(creds, fh)
    print(f"✓ {TOKEN_PICKLE}")

    write_token_json(creds)
    print(f"✓ {TOKEN_JSON}  (formato oauth2client para PyDrive2)")

    if not creds.refresh_token:
        print(
            "\n⚠️  Google no devolvió refresh_token (suele pasar si ya habías\n"
            "   autorizado esta app). Revoca el acceso en\n"
            "   https://myaccount.google.com/permissions y vuelve a ejecutar,\n"
            "   o añade prompt='consent' al flujo."
        )

    print(
        "\nSiguiente paso — copiar AMBOS al servidor:\n"
        "  scp -P 2222 tools/db_utils/token.pickle tools/db_utils/token.json \\\n"
        "      root@208.76.221.20:/var/www/vhosts/edefrutos2020.com/edf_catalogotablas/tools/db_utils/"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
