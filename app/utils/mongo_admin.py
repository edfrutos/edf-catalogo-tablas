"""Comandos de administración de MongoDB que pueden no estar permitidos.

Atlas gratuito/compartido y los usuarios sin rol de monitorización (clusterMonitor) rechazan
serverStatus y currentOp con OperationFailure ("not authorized"). Las páginas de monitorización
deben degradarse con un mensaje, no devolver un 500.
"""

from typing import Any, Optional, Tuple

from pymongo.errors import PyMongoError


def admin_command(client: Any, name: str) -> Tuple[Optional[dict], Optional[str]]:
    """Ejecuta `client.admin.command(name)`. Devuelve (resultado, None) o (None, mensaje de error)."""
    try:
        return client.admin.command(name), None
    except PyMongoError as exc:
        return None, str(exc)
