from app import db
from datetime import datetime

class Producto(db.Model):
    __tablename__ = 'productos'

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(150), nullable=False)
    descripcion     = db.Column(db.Text)
    precio          = db.Column(db.Numeric(10, 2), nullable=False)  # 10 dígitos, 2 decimales
    stock           = db.Column(db.Integer, default=0)
    imagen          = db.Column(db.String(300))                      # ruta del archivo
    activo          = db.Column(db.Boolean, default=True)
    creado_en       = db.Column(db.DateTime, default=datetime.utcnow)

    # Clave foránea → categorias
    categoria_id    = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    # Relación inversa con detalle_pedido
    detalles        = db.relationship('DetallePedido', backref='producto', lazy=True)

    def tiene_stock(self):
        return self.stock > 0

    def __repr__(self):
        return f'<Producto {self.nombre} | ${self.precio}>'