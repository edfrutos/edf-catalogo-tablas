from flask import Blueprint, send_from_directory, redirect, request
from app.utils.s3_utils import get_s3_url
from flask import current_app

images_bp = Blueprint('uploaded_images', __name__)



@images_bp.route('/imagenes_subidas/<filename>')
def uploaded_images(filename):
    s3_param = request.args.get('s3')
    if s3_param == 'true':
        url = get_s3_url(filename)
        if url:
            return redirect(url)
        return "❌ Error al acceder al archivo en S3", 404
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
