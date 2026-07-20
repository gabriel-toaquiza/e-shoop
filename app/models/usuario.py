from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# Tabla de asociación para favoritos (muchos-a-muchos Usuario <-> Producto)
favoritos_table = db.Table(
    'favoritos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('producto_id', db.Integer, db.ForeignKey('productos.id'), primary_key=True),
)


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer , primary_key=True)
    nombre = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256),nullable=False)
    rol = db.Column(db.Enum('cliente','admin'), default='cliente')
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación: un usuario tiene muchos pedidos
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

    # Relación: productos marcados como favoritos
    favoritos = db.relationship('Producto', secondary=favoritos_table,
                                lazy='subquery',
                                backref=db.backref('favorito_de', lazy=True))


    # -- Metodos de contraseña
    def set_password(self, password_plano):
        """ Hash a la contraseña en texto plano """
        self.password = generate_password_hash(password_plano)
    
    def check_password(self, passwd):
        """ Compara el texto plano con la contraseña hash """
        return check_password_hash(self.password, passwd)
    
    def es_admin(self):
        return self.rol == "admin"

    @property
    def is_active(self):
        # Flask-Login lo usa: una cuenta desactivada no puede iniciar sesión
        return self.activo

    def __repr__(self):
        return f'<Usuario: {self.email} | {self.rol} >'