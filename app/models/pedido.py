from app import db
from datetime import datetime

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id              = db.Column(db.Integer, primary_key=True)
    fecha           = db.Column(db.DateTime, default=datetime.utcnow)
    estado          = db.Column(
                        db.Enum('pendiente', 'pagado', 'enviado', 'entregado', 'cancelado'),
                        default='pendiente'
                    )
    total           = db.Column(db.Numeric(10, 2), default=0)
    direccion       = db.Column(db.String(300))
    notas           = db.Column(db.Text)

    # Clave foránea → usuarios
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relación: un pedido tiene muchas líneas de detalle
    detalles        = db.relationship('DetallePedido', backref='pedido',
                                       lazy=True, cascade='all, delete-orphan')

    def calcular_total(self):
        """Suma el subtotal de cada línea y actualiza el total."""
        self.total = sum(d.subtotal() for d in self.detalles)

    def __repr__(self):
        return f'<Pedido #{self.id} | {self.estado} | ${self.total}>'


class DetallePedido(db.Model):
    """
    Tabla pivote: resuelve la relación muchos-a-muchos
    entre Pedido y Producto, y además guarda la cantidad y precio.
    """
    __tablename__ = 'detalle_pedido'

    id              = db.Column(db.Integer, primary_key=True)
    cantidad        = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # precio al momento de comprar

    # Claves foráneas
    pedido_id       = db.Column(db.Integer, db.ForeignKey('pedidos.id'),   nullable=False)
    producto_id     = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)

    def subtotal(self):
        return float(self.cantidad) * float(self.precio_unitario)

    def __repr__(self):
        return f'<Detalle pedido#{self.pedido_id} | {self.cantidad}x producto#{self.producto_id}>'