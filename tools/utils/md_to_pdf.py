# Script para convertir Markdown a PDF usando Python y pdfkit
# Requiere: pip install markdown pdfkit
# Además, necesitas tener wkhtmltopdf instalado en el sistema

import markdown
import pdfkit


# Leer el archivo Markdown
def md_to_pdf(input_md, output_pdf):
    with open(input_md, encoding='utf-8') as f:
        text = f.read()
    # Convertir Markdown a HTML
    html = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    # Opcional: añadir estilos básicos para PDF
    html = f"""
    <html><head><meta charset='utf-8'>
    <style>
    body {{ font-family: Arial, sans-serif; margin: 2em; }}
    h1, h2, h3 {{ color: #2c3e50; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; }}
    </style></head><body>{html}</body></html>
    """
    # Convertir HTML a PDF
    pdfkit.from_string(html, output_pdf)
    print(f"PDF generado: {output_pdf}")

if __name__ == '__main__':
    import os
    import sys
    if len(sys.argv) >= 2:
        input_md = sys.argv[1]
        if len(sys.argv) >= 3:
            output_pdf = sys.argv[2]
        else:
            output_pdf = os.path.splitext(input_md)[0] + '.pdf'
    else:
        input_md = input('Introduce el nombre del archivo .md a convertir: ').strip()
        while not os.path.isfile(input_md):
            print(f"Archivo '{input_md}' no encontrado. Intenta de nuevo.")
            input_md = input('Introduce el nombre del archivo .md a convertir: ').strip()
        output_pdf = input(f"Nombre del PDF de salida (ENTER para '{os.path.splitext(input_md)[0] + '.pdf'}'): ").strip()
        if not output_pdf:
            output_pdf = os.path.splitext(input_md)[0] + '.pdf'
    md_to_pdf(input_md, output_pdf)
