#!/usr/bin/env python3
"""
Utilidades para manejo de archivos multimedia y documentos
"""

import os
import uuid

from werkzeug.utils import secure_filename


def allowed_multimedia(filename: str) -> bool:
    """Verificar si el archivo multimedia está permitido"""
    ALLOWED_MULTIMEDIA_EXTENSIONS = {
        "video": {"mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"},
        "audio": {"mp3", "wav", "ogg", "aac", "flac", "m4a"},
        "image": {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"},
    }

    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in {
        ext
        for extensions in ALLOWED_MULTIMEDIA_EXTENSIONS.values()
        for ext in extensions
    }


def allowed_document(filename: str) -> bool:
    """Verificar si el archivo de documento está permitido"""
    ALLOWED_DOCUMENT_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "txt",
        "rtf",
        "odt",
        "ods",
        "odp",
        "csv",
    }

    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_DOCUMENT_EXTENSIONS


def get_file_type(filename: str) -> str:
    """Obtener el tipo de archivo basado en la extensión"""
    if "." not in filename:
        return "unknown"

    ext = filename.rsplit(".", 1)[1].lower()

    # Tipos de multimedia
    video_extensions = {"mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"}
    audio_extensions = {"mp3", "wav", "ogg", "aac", "flac", "m4a"}
    image_extensions = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"}

    # Tipos de documentos
    pdf_extensions = {"pdf"}
    word_extensions = {"doc", "docx"}
    excel_extensions = {"xls", "xlsx", "csv"}
    text_extensions = {"txt", "rtf"}

    if ext in video_extensions:
        return "video"
    elif ext in audio_extensions:
        return "audio"
    elif ext in image_extensions:
        return "image"
    elif ext in pdf_extensions:
        return "pdf"
    elif ext in word_extensions:
        return "word"
    elif ext in excel_extensions:
        return "excel"
    elif ext in text_extensions:
        return "text"
    else:
        return "document"


def get_file_icon(filename: str) -> str:
    """Obtener el icono apropiado para el tipo de archivo"""
    file_type = get_file_type(filename)

    icon_map = {
        "video": "fas fa-video",
        "audio": "fas fa-music",
        "image": "fas fa-image",
        "pdf": "fas fa-file-pdf",
        "word": "fas fa-file-word",
        "excel": "fas fa-file-excel",
        "text": "fas fa-file-alt",
        "document": "fas fa-file",
        "unknown": "fas fa-file",
    }

    return icon_map.get(file_type, "fas fa-file")


def get_file_color_class(filename: str) -> str:
    """Obtener la clase de color apropiada para el tipo de archivo"""
    file_type = get_file_type(filename)

    color_map = {
        "video": "btn-outline-primary",
        "audio": "btn-outline-info",
        "image": "btn-outline-success",
        "pdf": "btn-outline-danger",
        "word": "btn-outline-primary",
        "excel": "btn-outline-success",
        "text": "btn-outline-secondary",
        "document": "btn-outline-dark",
        "unknown": "btn-outline-secondary",
    }

    return color_map.get(file_type, "btn-outline-secondary")


def process_multimedia_field(
    multimedia_url: str, multimedia_file, upload_dir: str
) -> str:
    """Procesar campo multimedia (URL o archivo)"""
    if multimedia_url and multimedia_url.strip():
        return multimedia_url.strip()
    elif multimedia_file and multimedia_file.filename:
        if allowed_multimedia(multimedia_file.filename):
            # Validar tamaño del archivo
            if not validate_file_size(multimedia_file, max_size_mb=300):
                file_size_mb = get_file_size_mb(multimedia_file)
                raise ValueError(
                    f"El archivo multimedia es demasiado grande: {file_size_mb:.1f}MB. El límite máximo es 300MB."
                )

            filename = secure_filename(f"{uuid.uuid4().hex}_{multimedia_file.filename}")
            file_path = os.path.join(upload_dir, filename)
            multimedia_file.save(file_path)
            return filename
        else:
            raise ValueError(
                f"Tipo de archivo multimedia no permitido: {multimedia_file.filename}"
            )
    else:
        return ""


def process_document_field(document_url: str, document_file, upload_dir: str) -> str:
    """Procesar campo documento (URL o archivo)"""
    if document_url and document_url.strip():
        return document_url.strip()
    elif document_file and document_file.filename:
        if allowed_document(document_file.filename):
            # Validar tamaño del archivo
            if not validate_file_size(document_file, max_size_mb=50):
                file_size_mb = get_file_size_mb(document_file)
                raise ValueError(
                    f"El archivo de documento es demasiado grande: {file_size_mb:.1f}MB. El límite máximo es 50MB."
                )

            filename = secure_filename(f"{uuid.uuid4().hex}_{document_file.filename}")
            file_path = os.path.join(upload_dir, filename)
            document_file.save(file_path)
            return filename
        else:
            raise ValueError(
                f"Tipo de archivo de documento no permitido: {document_file.filename}"
            )
    else:
        return ""


def get_file_preview_html(
    filename: str, file_url: str, is_external: bool = False
) -> str:
    """Generar HTML para vista previa de archivo"""
    if not filename:
        return '<span class="text-muted">-</span>'

    file_type = get_file_type(filename)
    icon = get_file_icon(filename)
    color_class = get_file_color_class(filename)

    if is_external:
        return f"""
            <a href="{file_url}" target="_blank" class="btn btn-sm {color_class}">
                <i class="{icon}"></i> Ver {file_type.title()}
            </a>
        """
    else:
        return f"""
            <a href="{file_url}" target="_blank" class="btn btn-sm {color_class}">
                <i class="{icon}"></i> Ver {file_type.title()}
            </a>
        """


def validate_file_size(file, max_size_mb: int = 50) -> bool:
    """Validar tamaño del archivo"""
    if not file:
        return True

    # Obtener tamaño del archivo
    file.seek(0, 2)  # Ir al final del archivo
    file_size = file.tell()
    file.seek(0)  # Volver al inicio

    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def get_file_size_mb(file) -> float:
    """Obtener tamaño del archivo en MB"""
    if not file:
        return 0.0

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    return file_size / (1024 * 1024)
