# app/auth2fa_routes.py
import io

import pyotp
import qrcode  # type: ignore
from bson.objectid import ObjectId
from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for

from app.models import users_collection  # type: ignore

auth2fa_bp = Blueprint("auth2fa", __name__, url_prefix="/2fa")

# -------------------------------------------
# CONFIGURACIÓN DE 2FA
# -------------------------------------------


@auth2fa_bp.route("/setup", methods=["GET", "POST"])
def setup_2fa():
    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    usuario = users_collection.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        token = request.form.get("token")
        secret = usuario.get("2fa_secret")
        totp = pyotp.TOTP(secret)

        if token and totp.verify(token):
            users_collection.update_one(
                {"_id": usuario["_id"]}, {"$set": {"2fa_enabled": True}}
            )
            flash("Autenticación 2FA activada exitosamente.", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Código inválido. Inténtalo de nuevo.", "error")

    # Si el usuario ya tiene secret, usarlo; sino, generarlo
    if "2fa_secret" not in usuario:
        secret = pyotp.random_base32()
        users_collection.update_one(
            {"_id": usuario["_id"]}, {"$set": {"2fa_secret": secret}}
        )
    else:
        secret = usuario["2fa_secret"]

    # QR para Google Authenticator
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=usuario["email"], issuer_name="EDF Catalogo Tablas"
    )
    return render_template("setup_2fa.html", otp_uri=otp_uri, secret=secret)


@auth2fa_bp.route("/qrcode")
def qrcode_2fa():
    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    usuario = users_collection.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario or "2fa_secret" not in usuario:
        return "No autorizado", 403

    secret = usuario["2fa_secret"]
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=usuario["email"], issuer_name="EDF Catalogo Tablas"
    )

    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype="image/png")


# -------------------------------------------
# VERIFICACIÓN 2FA EN LOGIN
# -------------------------------------------


@auth2fa_bp.route("/verify", methods=["GET", "POST"])
def verify_2fa():
    if "2fa_user_id" not in session:
        flash("Sesión de autenticación inválida.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        token = request.form.get("token")
        usuario = users_collection.find_one({"_id": ObjectId(session["2fa_user_id"])})
        if not usuario or "2fa_secret" not in usuario:
            flash("Error interno.", "error")
            return redirect(url_for("auth.login"))

        totp = pyotp.TOTP(usuario["2fa_secret"])
        if token and totp.verify(token):
            session["usuario"] = usuario["nombre"]
            session["usuario_id"] = str(usuario["_id"])
            session.pop("2fa_user_id", None)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Código incorrecto. Intenta nuevamente.", "error")

    return render_template("verificar_2fa.html")
