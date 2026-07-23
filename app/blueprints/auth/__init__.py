from flask import Blueprint

auth_bp = Blueprint('auth',__name__, template_folder='../../templates/auth')

from . import routes  # noqa: F401  (registra las rutas del blueprint)