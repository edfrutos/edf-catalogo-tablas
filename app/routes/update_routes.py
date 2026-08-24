# app/routes/update_routes.py

from flask import Blueprint, jsonify

from app.update_checker import check_for_update

update_bp = Blueprint("update", __name__)


@update_bp.route("/api/system/check-update", methods=["GET"])
def check_update():
    return jsonify(check_for_update())
