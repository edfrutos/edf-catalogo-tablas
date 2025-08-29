# Stub file for flask_login
from typing import Any, Optional, Callable
from flask import Flask

class LoginManager:
    def __init__(self) -> None: ...
    def init_app(self, app: Flask) -> None: ...
    login_view: Optional[str]

# Add other flask_login types as needed
