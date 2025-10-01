# Script: check_syntax.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 check_syntax.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import ast
import sys


def check_syntax(filename):
    try:
        with open(filename) as file:
            source = file.read()
        ast.parse(source)
        print(f"No syntax errors found in {filename}")
        return True
    except SyntaxError as e:
        print(
            f"Syntax error in {filename} at line {e.lineno}, column {e.offset}: {e.msg}"
        )
        # Print the problematic line and a few lines around it for context
        with open(filename) as file:
            lines = file.readlines()
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        print("\nContext:")
        for i in range(start, end):
            prefix = ">> " if i + 1 == e.lineno else "   "
            print(f"{prefix}{i + 1}: {lines[i].rstrip()}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_syntax.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    if not check_syntax(filename):
        sys.exit(1)
