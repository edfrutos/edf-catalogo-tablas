#!/usr/bin/env python3
import argparse
import os
from datetime import datetime

def truncate_log_lines(filepath, lines):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        all_lines = f.readlines()
    keep = all_lines[-lines:] if len(all_lines) > lines else all_lines
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(keep)
    print(f"✅ Log truncado a las últimas {len(keep)} líneas.")

def truncate_log_date(filepath, date_str):
    cutoff = datetime.strptime(date_str, '%Y-%m-%d').date()
    kept = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Busca fecha tipo [YYYY-MM-DD ...] al inicio de la línea
            if '[' in line:
                try:
                    date_part = line.split('[',1)[1][:10]
                    line_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                    if line_date >= cutoff:
                        kept.append(line)
                except Exception:
                    kept.append(line)  # Si no se puede parsear, la mantiene
            else:
                kept.append(line)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(kept)
    print(f"✅ Log truncado a partir de {date_str}. Líneas restantes: {len(kept)}")

def main():
    parser = argparse.ArgumentParser(description="Trunca un archivo de log a N líneas o desde una fecha.")
    parser.add_argument('--file', required=True, help='Ruta al archivo de log')
    parser.add_argument('--lines', type=int, help='Mantener solo las últimas N líneas')
    parser.add_argument('--date', help='Mantener solo líneas desde esta fecha (YYYY-MM-DD)')
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"❌ Archivo no encontrado: {args.file}")
        return
    if args.lines:
        truncate_log_lines(args.file, args.lines)
    elif args.date:
        truncate_log_date(args.file, args.date)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 