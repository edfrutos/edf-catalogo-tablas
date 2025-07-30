# Puedo proporcionar código específico como este:
from flask import Blueprint, jsonify

example_bp = Blueprint('example', __name__)

@example_bp.route('/api/example', methods=['GET'])
def example_endpoint():
    return jsonify({"status": "success", "message": "Endpoint funcionando"})
