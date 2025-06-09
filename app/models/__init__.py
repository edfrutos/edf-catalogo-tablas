# Exportar las funciones y clases necesarias
from .user import User
from .database import (
    get_users_collection,
    get_resets_collection,
    find_user_by_email_or_email as find_user_by_email_or_name,
    find_reset_token,
    update_user_password,
    mark_token_as_used,
    get_mongo_client,
    get_mongo_db
)

# Hacer disponibles estas funciones al importar desde app.models
__all__ = [
    'User',
    'get_users_collection',
    'get_resets_collection',
    'find_user_by_email_or_name',
    'find_reset_token',
    'update_user_password',
    'mark_token_as_used',
    'get_mongo_client',
    'get_mongo_db'
]
