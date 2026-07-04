from app import create_app, db
from app.models import Usuario, Categoria, Producto

app = create_app()

with app.app_context():
    # Categorías
    cat1 = Categoria(nombre='Electrónica',  descripcion='Dispositivos y gadgets')
    cat2 = Categoria(nombre='Ropa',         descripcion='Prendas de vestir')
    cat3 = Categoria(nombre='Hogar',        descripcion='Artículos para el hogar')
    db.session.add_all([cat1, cat2, cat3])
    db.session.commit()

    # Productos
    p1 = Producto(nombre='Audífonos Bluetooth', precio=49.99,
                  stock=20, categoria_id=cat1.id)
    p2 = Producto(nombre='Camiseta básica',     precio=12.50,
                  stock=50, categoria_id=cat2.id)
    p3 = Producto(nombre='Lámpara de escritorio', precio=25.00,
                  stock=15, categoria_id=cat3.id)
    db.session.add_all([p1, p2, p3])

    # Usuarios
    admin = Usuario(nombre='Administrador', email='admin@tienda.com', rol='admin')
    admin.set_password('admin123')

    cliente = Usuario(nombre='Juan Pérez', email='juan@email.com', rol='cliente')
    cliente.set_password('cliente123')

    db.session.add_all([admin, cliente])
    db.session.commit()

    print("✅ Datos de prueba insertados correctamente")