# Script: admin_notcations.py
# Descripción: Rutas administrativas para configuración y prueba de notificaciones.
# Autor: EDF Developer

import logging
import os

import app.notifications as notifications
from app.audit import audit_log
from app.decorators import admin_required
from flask import flash, jsonify, redirect, render_template, request, url_for

logger = logging.getLogger(__name__)


def register_admin_notification_routes(admin_bp) -> None:
    """Registra rutas de notificaciones sobre el blueprint admin existente."""

    @admin_bp.route("/notification-settings", methods=["GET", "POST"])
    @admin_required
    def notification_settings():
        """Página de configuración de notificaciones"""
        if request.method == "POST":
            # Validar campos obligatorios y tipos
            required_fields = [
                "smtp_server",
                "smtp_port",
                "smtp_username",
                "threshold_cpu",
                "threshold_memory",
                "threshold_disk",
                "threshold_error_rate",
                "cooldown",
            ]
            missing_fields = [f for f in required_fields if not request.form.get(f)]
            int_fields = [
                "smtp_port",
                "threshold_cpu",
                "threshold_memory",
                "threshold_disk",
                "threshold_error_rate",
                "cooldown",
            ]
            invalid_ints = []
            for f in int_fields:
                val = request.form.get(f)
                if val is not None and val != "":
                    try:
                        int(val)
                    except (ValueError, TypeError):
                        invalid_ints.append(f)
                else:
                    invalid_ints.append(f)
            if missing_fields or invalid_ints:
                flash(
                    f"Error: Faltan campos obligatorios o valores inválidos: {', '.join(set(missing_fields + invalid_ints))}",
                    "danger",
                )
                return redirect(url_for("admin.notification_settings"))

            enabled = request.form.get("enable_notifications") == "on"
            use_api = request.form.get("use_api") == "on"

            # Configuración SMTP
            smtp_settings = {
                "server": request.form.get("smtp_server"),
                "port": int(request.form.get("smtp_port") or "587"),
                "username": request.form.get("smtp_username"),
                "use_tls": request.form.get("smtp_tls") == "on",
            }
            password = request.form.get("smtp_password")
            if password:
                smtp_settings["password"] = password

            # Configuración API de Brevo
            brevo_api_settings = {
                "api_key": request.form.get("brevo_api_key"),
                "sender_name": request.form.get("sender_name"),
                "sender_email": request.form.get("sender_email"),
            }

            recipients = [r for r in request.form.getlist("recipients") if r.strip()]
            thresholds = {
                "cpu": int(request.form.get("threshold_cpu") or "80"),
                "memory": int(request.form.get("threshold_memory") or "80"),
                "disk": int(request.form.get("threshold_disk") or "80"),
                "error_rate": int(request.form.get("threshold_error_rate") or "10"),
            }
            cooldown = int(request.form.get("cooldown") or "300")

            if notifications.update_settings(
                enabled=enabled,
                use_api=use_api,
                smtp_settings=smtp_settings,
                brevo_api_settings=brevo_api_settings,
                recipients=recipients,
                thresholds=thresholds,
                cooldown=cooldown,
            ):
                flash(
                    "Configuración de notificaciones actualizada correctamente", "success"
                )
                audit_log(
                    "notification_settings_updated",
                    details={
                        "enabled": enabled,
                        "smtp_server": smtp_settings["server"],
                        "recipients_count": len(recipients),
                    },
                )
            else:
                flash("Error al guardar la configuración de notificaciones", "danger")
            return redirect(url_for("admin.notification_settings"))
        config = notifications.get_settings()
        return render_template("admin/notification_settings.html", config=config)


    @admin_bp.route("/api/test-email", methods=["POST"])
    @admin_required
    def test_email():
        """Enviar correo de prueba usando las credenciales del archivo .env"""
        email = request.form.get("email")
        if not email:
            return jsonify(
                {"success": False, "error": "No se proporcionó dirección de correo"}
            )

        try:
            # Registrar información sobre el intento de envío
            logger.info(f"[ADMIN] Intentando enviar correo de prueba a {email}")

            # Mostrar las variables de entorno relacionadas con el correo (sin la
            # contraseña)
            mail_server = os.environ.get("MAIL_SERVER")
            mail_port = os.environ.get("MAIL_PORT")
            mail_username = os.environ.get("MAIL_USERNAME")
            mail_use_tls = os.environ.get("MAIL_USE_TLS")
            mail_default_sender = os.environ.get("MAIL_DEFAULT_SENDER")
            mail_default_sender_name = os.environ.get("MAIL_DEFAULT_SENDER_NAME")
            mail_default_sender_email = os.environ.get("MAIL_DEFAULT_SENDER_EMAIL")

            logger.info(
                # type: ignore
                f"[ADMIN] Configuración de correo: Servidor={mail_server}, Puerto={mail_port}, "
                f"Usuario={mail_username}, TLS={mail_use_tls}"
            )
            logger.info(
                # type: ignore
                f"[ADMIN] Remitentes configurados: DEFAULT_SENDER={mail_default_sender}, "
                f"SENDER_NAME={mail_default_sender_name}, SENDER_EMAIL={mail_default_sender_email}"
            )

            # Crear un correo de prueba extremadamente simple para diagnosticar el problema
            import smtplib
            from email.mime.text import MIMEText

            try:
                # Crear un mensaje simple de texto plano
                logger.info("[ADMIN] Creando mensaje de prueba simple...")
                msg = MIMEText("Este es un mensaje de prueba.")
                msg["Subject"] = "Prueba de correo desde edefrutos2025"
                msg["From"] = mail_username or "noreply@example.com"
                msg["To"] = email

                # Intentar enviar directamente
                logger.info(f"[ADMIN] Conectando a {mail_server}:{mail_port}...")
                server = smtplib.SMTP(mail_server or "localhost", int(mail_port or "587"))

                if mail_use_tls and mail_use_tls.lower() in ("true", "1", "t"):
                    logger.info("[ADMIN] Iniciando TLS...")
                    server.starttls()

                logger.info(f"[ADMIN] Iniciando sesión con {mail_username}...")
                server.login(mail_username or "", os.environ.get("MAIL_PASSWORD") or "")

                logger.info("[ADMIN] Enviando mensaje...")
                server.send_message(msg)

                logger.info("[ADMIN] Cerrando conexión...")
                server.quit()

                logger.info(
                    f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método directo"
                )
                audit_log(
                    "test_email_sent", details={"recipient": email, "method": "direct"}
                )
                return jsonify({"success": True})
            except (ConnectionError, TimeoutError, OSError, ValueError) as direct_err:
                logger.error(
                    f"[ADMIN] Error en método directo: {str(direct_err)}", exc_info=True
                )

                # Si el método directo falla, intentar con el método normal
                logger.info("[ADMIN] Intentando con el método normal...")
                result = notifications.send_test_email(email)

                if result:
                    logger.info(
                        f"[ADMIN] Correo de prueba enviado con éxito a {email} usando método normal"
                    )
                    audit_log(
                        "test_email_sent", details={"recipient": email, "method": "normal"}
                    )
                    return jsonify({"success": True})
                else:
                    logger.error(
                        f"[ADMIN] Error al enviar correo de prueba a {email}. Ambos métodos fallaron."
                    )
                    return jsonify(
                        {
                            "success": False,
                            "error": f"Error directo: {str(direct_err)}. Error en método normal: Resultado falso sin excepción. Revisa los logs para más detalles.",
                        }
                    )
        except (ConnectionError, TimeoutError, OSError, ValueError, AttributeError) as e:
            logger.error(
                f"[ADMIN] Excepción al enviar correo de prueba a {email}: {str(e)}",
                exc_info=True,
            )
            return jsonify({"success": False, "error": f"Error: {str(e)}"})

