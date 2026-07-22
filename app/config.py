import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY','dev-secret')
    #Configuración de la BD
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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