#!/usr/bin/env python3
# Script: verificar_credenciales.py
# Descripción: Verifica en vivo que las credenciales del .env siguen siendo
#              válidas: MongoDB, AWS S3, SMTP Brevo y SMTP Google/Gmail
#              (y, si está, la API de Brevo). No imprime ningún secreto
#              completo: solo estado OK/FALLO y fragmentos enmascarados.
# Uso: python3 verificar_credenciales.py [--env-file RUTA] [--show-config]
# Requiere: python-dotenv y, según lo que se compruebe, pymongo / boto3 /
#           requests. Si falta una librería, esa comprobación se marca OMITIDA.
# Autor: EDF Developer - 2026-09-02
"""Comprobador de credenciales para EDF Catálogo de Tablas.

Lee las variables desde un archivo .env (sin hardcodear nada) y hace un
handshake de autenticación real contra cada proveedor configurado. La salida
está enmascarada; el script no escribe secretos en disco ni los envía a
ningún sitio salvo el propio proveedor que se está verificando.

Códigos de salida:
    0  Ninguna comprobación ha fallado (todo OK u OMITIDO).
    1  Al menos una comprobación ha fallado.
"""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

OK = "OK"
FAIL = "FALLO"
SKIP = "OMITIDO"

_ICON = {OK: "✅", FAIL: "❌", SKIP: "⏭️ "}


# --------------------------------------------------------------------------- #
# Utilidades                                                                  #
# --------------------------------------------------------------------------- #
def mask(value: str | None, show_start: int = 3, show_end: int = 2) -> str:
    """Devuelve una versión enmascarada de un valor sensible."""
    if value is None or value == "":
        return "<vacío>"
    text = str(value)
    if len(text) <= show_start + show_end:
        return "*" * len(text)
    return f"{text[:show_start]}{'*' * 6}{text[-show_end:]} ({len(text)} chars)"


def redact_uri(uri: str) -> str:
    """Oculta la contraseña de una URI tipo mongodb+srv://user:pass@host/db."""
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", uri)


def uri_host(uri: str) -> str:
    """Extrae el host (parte tras la @) de una URI de conexión."""
    match = re.search(r"@([^/?]+)", uri)
    return match.group(1) if match else "<host desconocido>"


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Result:
    name: str
    status: str = SKIP
    detail: str = ""
    extra: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Comprobaciones                                                              #
# --------------------------------------------------------------------------- #
def check_mongodb() -> Result:
    res = Result("MongoDB (MONGO_URI)")
    uri = os.getenv("MONGO_URI")
    if not uri:
        res.detail = "MONGO_URI no está definida en el .env"
        return res

    res.extra.append(f"host: {uri_host(uri)}")
    res.extra.append(f"uri : {redact_uri(uri)}")

    try:
        from pymongo import MongoClient
        from pymongo.errors import (
            OperationFailure,
            ServerSelectionTimeoutError,
        )
    except ImportError:
        res.detail = "pymongo no instalado (pip install pymongo)"
        return res

    db_name = os.getenv("MONGODB_DB") or os.getenv("MONGODB_DB_NAME")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=6000, appName="verificar_credenciales")
        client.admin.command("ping")
        res.status = OK
        res.detail = "autenticación y ping correctos"
        if db_name:
            try:
                names = client[db_name].list_collection_names()
                res.extra.append(f"BD '{db_name}': {len(names)} colecciones visibles")
            except OperationFailure as exc:
                res.extra.append(f"BD '{db_name}': ping OK, sin permiso para listar ({exc.code})")
        client.close()
    except OperationFailure as exc:
        res.status = FAIL
        res.detail = f"credenciales rechazadas: {exc.details.get('errmsg', exc)}"
    except ServerSelectionTimeoutError as exc:
        res.status = FAIL
        res.detail = f"no se pudo conectar (red/DNS/cluster caído): {str(exc)[:160]}"
    except Exception as exc:  # noqa: BLE001 - queremos reportar cualquier fallo
        res.status = FAIL
        res.detail = f"{type(exc).__name__}: {str(exc)[:160]}"
    return res


def check_aws() -> Result:
    res = Result("AWS S3 (AWS_ACCESS_KEY_ID / SECRET)")
    key_id = os.getenv("AWS_ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "eu-central-1")
    bucket = os.getenv("S3_BUCKET_NAME")

    if not key_id or not secret:
        res.detail = "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY no definidas"
        return res

    res.extra.append(f"access key id: {mask(key_id, 4, 4)}")
    res.extra.append(f"region       : {region}")
    res.extra.append(f"bucket       : {bucket or '<no definido>'}")

    try:
        import boto3
        from botocore.exceptions import ClientError, EndpointConnectionError
    except ImportError:
        res.detail = "boto3 no instalado (pip install boto3)"
        return res

    session = boto3.session.Session(
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name=region,
    )
    # 1) ¿La credencial está viva? -> STS get_caller_identity (casi siempre permitido)
    try:
        ident = session.client("sts").get_caller_identity()
        res.extra.append(f"identidad    : {ident.get('Arn', '?')}")
        res.status = OK
        res.detail = "credenciales válidas"
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "?")
        res.status = FAIL
        res.detail = f"credenciales inválidas ({code})"
        return res
    except EndpointConnectionError as exc:
        res.status = FAIL
        res.detail = f"sin conexión con AWS: {exc}"
        return res
    except Exception as exc:  # noqa: BLE001
        res.status = FAIL
        res.detail = f"{type(exc).__name__}: {str(exc)[:160]}"
        return res

    # 2) ¿Se puede acceder al bucket concreto?
    if bucket:
        try:
            session.client("s3").head_bucket(Bucket=bucket)
            res.extra.append(f"bucket '{bucket}': acceso OK")
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "?")
            if code in {"403", "AccessDenied"}:
                res.status = FAIL
                res.detail = "credenciales válidas pero SIN permiso sobre el bucket"
                res.extra.append(f"bucket '{bucket}': 403 AccessDenied")
            elif code in {"404", "NoSuchBucket"}:
                res.status = FAIL
                res.detail = f"el bucket '{bucket}' no existe en {region}"
            else:
                res.status = FAIL
                res.detail = f"error al acceder al bucket ({code})"
        except Exception as exc:  # noqa: BLE001
            res.status = FAIL
            res.detail = f"{type(exc).__name__}: {str(exc)[:160]}"
    return res


def _smtp_login(host: str, port: int, username: str, password: str, use_tls: bool, timeout: int = 15) -> None:
    """Hace login SMTP real. Lanza excepción si falla."""
    if port == 465:
        server: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)
    try:
        server.ehlo()
        if use_tls and port != 465:
            server.starttls()
            server.ehlo()
        server.login(username, password)
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001
            pass


def _run_smtp_check(res: Result, host: str, port: int, user: str, password: str, use_tls: bool) -> None:
    res.extra.append(f"servidor: {host}:{port} (TLS={use_tls})")
    res.extra.append(f"usuario : {user}")
    res.extra.append(f"password: {mask(password)}")
    try:
        _smtp_login(host, port, user, password, use_tls)
        res.status = OK
        res.detail = "login SMTP correcto"
    except smtplib.SMTPAuthenticationError as exc:
        res.status = FAIL
        res.detail = f"credenciales rechazadas: {exc.smtp_code} {exc.smtp_error!r}"
    except (smtplib.SMTPException, OSError) as exc:
        res.status = FAIL
        res.detail = f"{type(exc).__name__}: {str(exc)[:160]}"


def check_smtp_brevo() -> Result:
    res = Result("SMTP Brevo")
    user = os.getenv("BREVO_SMTP_USERNAME") or os.getenv("MAIL_USERNAME")
    password = os.getenv("BREVO_SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")
    host = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
    port = int(os.getenv("BREVO_SMTP_PORT", "587"))

    if not user or not password:
        res.detail = "BREVO_SMTP_USERNAME / BREVO_SMTP_PASSWORD no definidas"
        return res

    if "Rmp3UXwsIkvA0c1d" in password:
        res.status = FAIL
        res.detail = "usa la credencial marcada como COMPROMETIDA en verificar_env.py"
        res.extra.append(f"servidor: {host}:{port}")
        res.extra.append(f"usuario : {user}")
        return res

    _run_smtp_check(res, host, port, user, password, use_tls=True)
    return res


def check_smtp_google() -> Result:
    res = Result("SMTP Google / Gmail")
    # Preferencia: par dedicado GOOGLE_EMAIL / GOOGLE_APP_PASSWORD (.env.example).
    user = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_APP_PASSWORD")
    host = "smtp.gmail.com"
    port = 587

    # Fallback: MAIL_* si apuntan a Gmail.
    if not (user and password):
        mail_server = (os.getenv("MAIL_SERVER") or "").lower()
        if "gmail" in mail_server or "google" in mail_server:
            user = os.getenv("MAIL_USERNAME")
            password = os.getenv("MAIL_PASSWORD")
            host = os.getenv("MAIL_SERVER", host)
            port = int(os.getenv("MAIL_PORT", "587"))

    if not user or not password:
        res.detail = "GOOGLE_EMAIL / GOOGLE_APP_PASSWORD (o MAIL_* hacia Gmail) no definidas"
        return res

    if len(password.replace(" ", "")) != 16:
        res.extra.append("aviso: una contraseña de aplicación de Google tiene 16 caracteres")

    _run_smtp_check(res, host, port, user, password.replace(" ", ""), use_tls=True)
    return res


def check_brevo_api() -> Result:
    res = Result("API Brevo (BREVO_API_KEY)")
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        res.detail = "BREVO_API_KEY no definida (opcional)"
        return res
    res.extra.append(f"api key: {mask(api_key, 8, 4)}")

    if api_key.strip() in {"tu-nueva-brevo", "tu-brevo-api-key"} or "tu-" in api_key:
        res.status = FAIL
        res.detail = "valor de plantilla, sin configurar"
        return res

    try:
        import requests
    except ImportError:
        res.detail = "requests no instalado (pip install requests)"
        return res

    try:
        resp = requests.get(
            "https://api.brevo.com/v3/account",
            headers={"api-key": api_key, "accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            res.status = OK
            res.detail = f"clave válida (cuenta: {data.get('email', '?')})"
        elif resp.status_code in {401, 403}:
            res.status = FAIL
            res.detail = f"clave rechazada (HTTP {resp.status_code})"
        else:
            res.status = FAIL
            res.detail = f"respuesta inesperada HTTP {resp.status_code}: {resp.text[:120]}"
    except Exception as exc:  # noqa: BLE001
        res.status = FAIL
        res.detail = f"{type(exc).__name__}: {str(exc)[:160]}"
    return res


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def load_env(env_file: str | None) -> Path | None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("❌ python-dotenv no instalado. Ejecuta: pip install python-dotenv")
        sys.exit(2)

    if env_file:
        path = Path(env_file).expanduser().resolve()
    else:
        path = Path(".env").resolve()

    if not path.exists():
        print(f"❌ No se encuentra el archivo de entorno: {path}")
        print("   Pásalo con --env-file /ruta/al/.env")
        sys.exit(2)

    load_dotenv(path, override=True)
    return path


def print_result(res: Result) -> None:
    print(f"\n{_ICON[res.status]} {res.name}: {res.status}")
    if res.detail:
        print(f"    → {res.detail}")
    for line in res.extra:
        print(f"      · {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica credenciales del .env sin exponerlas.")
    parser.add_argument("--env-file", help="Ruta al archivo .env (por defecto ./.env)")
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Muestra (enmascaradas) las variables cargadas y termina",
    )
    parser.add_argument(
        "--only",
        choices=["mongo", "aws", "brevo-smtp", "google-smtp", "brevo-api"],
        nargs="+",
        help="Ejecuta solo las comprobaciones indicadas",
    )
    args = parser.parse_args()

    path = load_env(args.env_file)
    print("=" * 64)
    print("  VERIFICADOR DE CREDENCIALES — EDF Catálogo de Tablas")
    print(f"  .env: {path}")
    print("=" * 64)

    if args.show_config:
        keys = [
            "MONGO_URI", "MONGODB_DB",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "S3_BUCKET_NAME", "USE_S3",
            "BREVO_API_KEY", "BREVO_SMTP_USERNAME", "BREVO_SMTP_PASSWORD",
            "MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD",
            "GOOGLE_EMAIL", "GOOGLE_APP_PASSWORD",
        ]
        print("\nConfiguración cargada (enmascarada):")
        for key in keys:
            raw = os.getenv(key)
            if key == "MONGO_URI" and raw:
                shown = redact_uri(raw)
            elif key in {"AWS_REGION", "S3_BUCKET_NAME", "USE_S3", "MAIL_SERVER", "MAIL_PORT", "BREVO_SMTP_USERNAME", "MAIL_USERNAME", "GOOGLE_EMAIL", "MONGODB_DB"}:
                shown = raw or "<vacío>"
            else:
                shown = mask(raw)
            print(f"  {key:24} = {shown}")
        return 0

    checks: dict[str, Callable[[], Result]] = {
        "mongo": check_mongodb,
        "aws": check_aws,
        "brevo-smtp": check_smtp_brevo,
        "google-smtp": check_smtp_google,
        "brevo-api": check_brevo_api,
    }
    selected = args.only or list(checks)

    results = [checks[name]() for name in selected]
    for res in results:
        print_result(res)

    failed = [r for r in results if r.status == FAIL]
    ok = [r for r in results if r.status == OK]
    skipped = [r for r in results if r.status == SKIP]

    print("\n" + "=" * 64)
    print(f"  RESUMEN: {len(ok)} OK · {len(failed)} FALLO · {len(skipped)} OMITIDO")
    if failed:
        print("  Revisa: " + ", ".join(r.name for r in failed))
    print("=" * 64)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
