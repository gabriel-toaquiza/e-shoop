import os
from dotenv import load_dotenv

load_dotenv()

_DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'


class Config:
    # En producción (sin FLASK_DEBUG) la SECRET_KEY es obligatoria: si falta,
    # la app no arranca (una clave conocida permitiría falsificar sesiones).
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if _DEBUG:
            SECRET_KEY = 'dev-secret'
        else:
            raise RuntimeError(
                'Falta SECRET_KEY. Defínela en el .env para producción '
                '(genera una con: python -c "import secrets; print(secrets.token_hex(32))").'
            )
    #Configuración de la BD
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Producción / seguridad de sesión ──────────────────────────
    # DEBUG solo se activa si FLASK_DEBUG=1 (por defecto, apagado = producción)
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    # La cookie de sesión no es accesible por JavaScript
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Enviar la cookie solo por HTTPS (actívalo en el servidor con SESSION_COOKIE_SECURE=1)
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'

    # Tamaño máximo del cuerpo de la petición (red de seguridad para subidas): 5 MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # ── Datos para el pago por transferencia ──────────────────────
    # PLACEHOLDERS: reemplaza estos valores por los reales de tu cuenta.
    DATOS_BANCARIOS = {
        'banco':   'Banco Pichincha',
        'tipo':    'Cuenta de Ahorros',
        'numero':  '0000000000',
        'titular': 'Nombre del Titular',
        'cedula':  '0000000000',
        'correo':  'pagos@verova.ec',
    }

    # Comprobantes de pago (archivos privados, fuera de /static)
    EXTENSIONES_COMPROBANTE = {'jpg', 'jpeg', 'png', 'webp', 'pdf'}