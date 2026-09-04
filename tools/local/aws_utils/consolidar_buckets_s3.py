#!/usr/bin/env python3
# Script: consolidar_buckets_s3.py
# Descripción: Consolida el contenido de varios buckets S3 "retales" en el
#              bucket canónico (edfcatalogotablas-sp). Copia servidor-a-servidor
#              (sin descargar) solo los objetos que faltan en el destino.
# Uso: python3 tools/local/aws_utils/consolidar_buckets_s3.py [--apply]
#      python3 tools/local/aws_utils/consolidar_buckets_s3.py --apply --src edf-catalogo-tablas-sp
# Requiere: boto3, python-dotenv. Lee AWS_ACCESS_KEY_ID/SECRET del .env.
# Autor: EDF Developer - 2026-09-04
"""Consolida buckets S3 en el canónico.

Contexto: por experimentos previos existen 3 buckets casi homónimos en
`eu-south-2`: `edf-catalogo-tablas-sp`, `edf-catalogotablas-sp` y
`edfcatalogotablas-sp`. El último es el bueno (coincide con las URLs guardadas
en Mongo y con la config del cliente .NET). Este script copia al bueno todo lo
que solo esté en los otros, sin borrar nada.

`--apply` copia; sin él, solo audita (dry-run). Es idempotente: no recopia lo
que ya existe en el destino (compara por Key y tamaño).
"""

from __future__ import annotations

import argparse
import os
import sys

REGION = "eu-south-2"
DEST_DEFAULT = "edfcatalogotablas-sp"
SRC_DEFAULT = ["edf-catalogo-tablas-sp", "edf-catalogotablas-sp", "edfcatalogo"]


def _client():
    try:
        import boto3
        from dotenv import load_dotenv
    except ImportError as exc:
        sys.exit(f"❌ Falta dependencia: {exc} (pip install boto3 python-dotenv)")
    load_dotenv()
    key = os.getenv("AWS_ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not key or not secret:
        sys.exit("❌ AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY no están en el .env")
    return boto3.client(
        "s3", aws_access_key_id=key, aws_secret_access_key=secret, region_name=REGION
    )


def scan(s3, bucket: str) -> dict[str, int] | None:
    """Devuelve {key: size} de todo el bucket, o None si no hay acceso."""
    out: dict[str, int] = {}
    kwargs: dict = {"Bucket": bucket}
    try:
        while True:
            resp = s3.list_objects_v2(**kwargs)
            for obj in resp.get("Contents", []):
                out[obj["Key"]] = obj["Size"]
            if not resp.get("IsTruncated"):
                return out
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠️  {bucket}: sin acceso / no existe -> {type(exc).__name__}: {exc}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Copia (por defecto dry-run)")
    parser.add_argument("--dest", default=DEST_DEFAULT, help=f"Bucket destino (def: {DEST_DEFAULT})")
    parser.add_argument("--src", nargs="+", default=SRC_DEFAULT, help="Buckets origen")
    args = parser.parse_args()

    s3 = _client()

    print(f"Destino: {args.dest} ({REGION})")
    dest = scan(s3, args.dest)
    if dest is None:
        return 2
    print(f"  {len(dest)} objetos, {sum(dest.values()) / 1e9:.2f} GB\n")
    print(f"Modo: {'APPLY (copia)' if args.apply else 'DRY-RUN (solo audita)'}\n")

    grand_copied = grand_pending = 0
    for src_name in args.src:
        if src_name == args.dest:
            continue
        print(f"— {src_name}")
        src = scan(s3, src_name)
        if src is None:
            continue
        faltan = [k for k, sz in src.items() if dest.get(k) != sz]
        ya = len(src) - len(faltan)
        print(f"    {len(src)} objetos · {ya} ya en destino · {len(faltan)} a copiar")
        for k in sorted(faltan)[:8]:
            print(f"      + {k}")
        if len(faltan) > 8:
            print(f"      … y {len(faltan) - 8} más")

        if args.apply and faltan:
            copied = errors = 0
            for k in faltan:
                try:
                    # s3.copy() gestiona multipart para objetos > 5 GB.
                    s3.copy({"Bucket": src_name, "Key": k}, args.dest, k)
                    copied += 1
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    print(f"      ✗ {k}: {type(exc).__name__}: {exc}")
            print(f"    ✓ copiados {copied}/{len(faltan)}" + (f" · {errors} errores" if errors else ""))
            grand_copied += copied
        grand_pending += len(faltan)

    print()
    if args.apply:
        print(f"TOTAL copiado: {grand_copied}")
    else:
        print(f"TOTAL a copiar: {grand_pending}  → vuelve a ejecutar con --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
