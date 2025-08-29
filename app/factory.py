# app/factory.py

import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask, g
from flask_login import LoginManager


def create_app(testing=False):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        static_url_path="/static",
    )

    if testing:
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

    app.secret_key = os.getenv("SECRET_KEY", "edf_secret_key_2025")
    app.config.from_object("config.Config")

    session_dir = app.config.get("SESSION_FILE_DIR")
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)
        app.logger.info(f"✅ Directorio de sesiones configurado: {session_dir}")

    try:
        from app.database import get_mongo_client, get_mongo_db, initialize_db

        initialize_db(app)
        app.logger.info("✅ Conexión global a MongoDB inicializada (initialize_db)")
        client = get_mongo_client()
        db = get_mongo_db()
    except Exception as e:
        app.logger.error(f"❌ Error inicializando la conexión global a MongoDB: {e}")
        db = None

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    def ensure_db():
        from flask import g

        from app.database import get_mongo_client, get_mongo_db

        client = get_mongo_client()
        db = get_mongo_db()
        g.mongo_client = client
        g.db = db
        if db is not None:
            g.users_collection = db["users"]
            g.resets_collection = db["password_resets"]
            g.spreadsheets_collection = db["spreadsheets"]
        else:
            g.users_collection = None
            g.resets_collection = None
            g.spreadsheets_collection = None

    app.before_request(ensure_db)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        if user_id is None or user_id == "":
            return None
        users_collection = getattr(g, "users_collection", None)
        if users_collection is None:
            app.logger.error(
                "[CRÍTICO] users_collection no está inicializada. Verifica la conexión a MongoDB antes de autenticar usuarios."
            )
            raise Exception(
                "users_collection no está inicializada. No se puede autenticar usuarios sin conexión a la base de datos."
            )
        user_data = users_collection.find_one({"email": user_id})
        if not user_data:
            return None
        return User(user_data)

    from app.filters import init_app as init_filters

    init_filters(app)

    from app.extensions import init_extensions

    init_extensions(app)

    from app.logging_unified import setup_unified_logging

    setup_unified_logging(app)

    from app.security_middleware import security_middleware

    security_middleware.init_app(app)

    # Registrar blueprints
    from .error_handlers import errors_bp
    from .routes.admin_routes import admin_bp, admin_logs_bp
    from .routes.auth_routes import auth_bp
    from .routes.catalog_images_routes import image_bp
    from .routes.catalogs_routes import catalogs_bp
    from .routes.dev_template import bp_dev_template
    from .routes.emergency_access import emergency_bp
    from .routes.images_routes import images_bp
    from .routes.main_routes import main_bp
    from .routes.maintenance_routes import register_maintenance_routes
    from .routes.scripts_routes import scripts_bp
    from .routes.scripts_tools_routes import scripts_tools_bp
    from .routes.testing_routes import testing_bp
    from .routes.usuarios_routes import usuarios_bp

    blueprints = [
        (main_bp, ""),
        (auth_bp, ""),
        (catalogs_bp, "/catalogs"),
        (image_bp, "/images"),
        (usuarios_bp, "/usuarios"),
        (errors_bp, ""),
        (admin_bp, "/admin"),
        (admin_logs_bp, "/admin"),
        (scripts_bp, None),
        (scripts_tools_bp, None),
        (bp_dev_template, None),
        (testing_bp, None),
        (images_bp, None),
        (emergency_bp, None),
    ]

    for bp, prefix in blueprints:
        if bp:
            app.register_blueprint(bp, url_prefix=prefix)

    register_maintenance_routes(app)

    # Error handlers
    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("error/404.html"), 404

    # Logging
    logs_dir = os.environ.get(
        "LOG_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"),
    )
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "flask_debug.log")

    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    return app
