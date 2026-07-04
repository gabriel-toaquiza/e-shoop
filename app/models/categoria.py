from app import db

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    activa      = db.Column(db.Boolean, default=True)

    # Relación: una categoría tiene muchos productos
    productos   = db.relationship('Producto', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'