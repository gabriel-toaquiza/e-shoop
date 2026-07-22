from app import create_app, db
from app.models import Usuario, Categoria, Producto

app = create_app()

with app.app_context():
    # Evitar duplicados: si ya hay datos, no volver a insertar
    if Categoria.query.first() or Usuario.query.first():
        print("La base de datos ya tiene datos. Seed cancelado.")
        raise SystemExit

    # Categorías (marca Verova – manualidades)
    cats = {
        'tote':   Categoria(nombre='Tote bags',                 descripcion='Bolsos de tela tejidos a mano.'),
        'cuadro': Categoria(nombre='Cuadros Decorativos',       descripcion='Cuadros de cuentas y arte hecho a mano.'),
        'velas':  Categoria(nombre='Velas',                     descripcion='Velas artesanales aromáticas.'),
        'deco':   Categoria(nombre='Decoración de Interiores',  descripcion='Piezas para darle calidez a tu espacio.'),
    }
    db.session.add_all(cats.values())
    db.session.commit()

    # Productos de ejemplo
    productos = [
        Producto(nombre='Tote bag andina',        precio=18.00, stock=12, categoria_id=cats['tote'].id,
                 personalizable=True,
                 instrucciones_personalizacion='Indícanos los colores y si quieres un nombre bordado.'),
        Producto(nombre='Tote bag lisa',          precio=14.00, stock=20, categoria_id=cats['tote'].id),
        Producto(nombre='Cuadro de cuentas',      precio=25.00, stock=8,  categoria_id=cats['cuadro'].id,
                 personalizable=True,
                 instrucciones_personalizacion='Dinos el diseño, los colores y las medidas.'),
        Producto(nombre='Vela aromática lavanda', precio=9.50,  stock=30, categoria_id=cats['velas'].id),
        Producto(nombre='Vela decorativa árbol',  precio=12.00, stock=15, categoria_id=cats['velas'].id),
        Producto(nombre='Cesta decorativa',       precio=22.00, stock=10, categoria_id=cats['deco'].id),
    ]
    db.session.add_all(productos)

    # Usuarios de prueba
    admin = Usuario(nombre='Administrador', email='admin@tienda.com', rol='admin')
    admin.set_password('admin123')

    cliente = Usuario(nombre='Juan Pérez', email='juan@email.com', rol='cliente')
    cliente.set_password('cliente123')

    db.session.add_all([admin, cliente])
    db.session.commit()

    print("Datos de prueba insertados correctamente.")
