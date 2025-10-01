# Exportar las funciones y clases necesarias
from .database import (
    find_reset_token,
)
from .database import find_user_by_email_or_email as find_user_by_email_or_name
from .database import (
    get_mongo_client,
    get_mongo_db,
    get_resets_collection,
    get_users_collection,
    mark_token_as_used,
    update_user_password,
)
from .user import User

# Hacer disponibles estas funciones al importar desde app.models
__all__ = [
    "User",
    "get_users_collection",
    "get_resets_collection",
    "find_user_by_email_or_name",
    "find_reset_token",
    "update_user_password",
    "mark_token_as_used",
    "get_mongo_client",
    "get_mongo_db",
]
