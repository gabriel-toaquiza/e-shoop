from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configuración de Login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesión para continuar'
    login_manager.login_message_category = 'warning'

    # Importar los modelos registra todas las tablas (Usuario, Categoria,
    # Producto, Pedido, DetallePedido) en SQLAlchemy antes de las migraciones.
    from app.models import Usuario

    # User loader:
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    #Blueprints
    from app.blueprints.public import public_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Favoritos y contador de carrito disponibles en todas las plantillas
    @app.context_processor
    def inject_favoritos():
        from app.blueprints.public.carrito_utils import cantidad_total
        if current_user.is_authenticated:
            ids = {p.id for p in current_user.favoritos}
        else:
            ids = set(session.get('favoritos', []))
        return {'favoritos_ids': ids,
                'carrito_cantidad': cantidad_total(session.get('carrito', {}))}

    # Etiquetas y colores de los estados de pedido, disponibles en las plantillas
    @app.context_processor
    def inject_estados():
        from app.estados import ESTADO_ETIQUETAS, ESTADO_COLORES, LINEA_TIEMPO
        return {'estado_etiquetas': ESTADO_ETIQUETAS,
                'estado_colores': ESTADO_COLORES,
                'linea_tiempo': LINEA_TIEMPO}

    # Páginas de error con el diseño del sitio
    from app.errores import registrar_errores
    registrar_errores(app)

    return app

