from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Categoria, Pedido, DetallePedido
from app.blueprints.public import public_bp


# ── HOME ──────────────────────────────────────────────────────────
@public_bp.route('/')
def home():
    productos_destacados = Producto.query.filter_by(activo=True).limit(8).all()
    categorias = Categoria.query.filter_by(activa=True).all()
    return render_template('public/home.html',
                           productos=productos_destacados,
                           categorias=categorias)


# ── TIENDA ────────────────────────────────────────────────────────
@public_bp.route('/tienda')
def tienda():
    categoria_id = request.args.get('categoria', type=int)
    busqueda     = request.args.get('q', '').strip()
    pagina       = request.args.get('pagina', 1, type=int)

    query = Producto.query.filter_by(activo=True)

    # Filtro por categoría
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    # Filtro por búsqueda
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))

    # Paginación: 9 productos por página
    productos  = query.paginate(page=pagina, per_page=9, error_out=False)
    categorias = Categoria.query.filter_by(activa=True).all()

    return render_template('public/tienda.html',
                           productos=productos,
                           categorias=categorias,
                           categoria_id=categoria_id,
                           busqueda=busqueda)


# ── DETALLE DE PRODUCTO ───────────────────────────────────────────
@public_bp.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Producto.query.get_or_404(id)
    relacionados = Producto.query.filter(
        Producto.categoria_id == producto.categoria_id,
        Producto.id != producto.id,
        Producto.activo == True
    ).limit(4).all()
    return render_template('public/detalle_producto.html',
                           producto=producto,
                           relacionados=relacionados)


# ── CARRITO ───────────────────────────────────────────────────────
@public_bp.route('/carrito')
def carrito():
    carrito   = session.get('carrito', {})
    items     = []
    total     = 0

    for prod_id, cantidad in carrito.items():
        producto = Producto.query.get(int(prod_id))
        if producto:
            subtotal = float(producto.precio) * cantidad
            total   += subtotal
            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })

    return render_template('public/carrito.html',
                           items=items,
                           total=total)


@public_bp.route('/carrito/agregar/<int:id>', methods=['POST'])
def agregar_carrito(id):
    producto = Producto.query.get_or_404(id)

    if not producto.tiene_stock():
        flash('Producto sin stock disponible.', 'warning')
        return redirect(url_for('public.tienda'))

    carrito = session.get('carrito', {})
    clave   = str(id)
    cantidad_solicitada = int(request.form.get('cantidad', 1))

    # Sumar si ya existe en el carrito
    carrito[clave] = carrito.get(clave, 0) + cantidad_solicitada

    # No superar el stock disponible
    if carrito[clave] > producto.stock:
        carrito[clave] = producto.stock
        flash('Cantidad ajustada al stock disponible.', 'info')

    session['carrito'] = carrito
    flash(f'"{producto.nombre}" agregado al carrito.', 'success')
    return redirect(url_for('public.carrito'))


@public_bp.route('/carrito/eliminar/<int:id>')
def eliminar_carrito(id):
    carrito = session.get('carrito', {})
    carrito.pop(str(id), None)
    session['carrito'] = carrito
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('public.carrito'))


@public_bp.route('/carrito/vaciar')
def vaciar_carrito():
    session.pop('carrito', None)
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('public.tienda'))


# ── PAGO ──────────────────────────────────────────────────────────
@public_bp.route('/pago', methods=['GET', 'POST'])
@login_required
def pago():
    carrito = session.get('carrito', {})

    if not carrito:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('public.tienda'))

    if request.method == 'POST':
        direccion = request.form.get('direccion', '').strip()
        notas     = request.form.get('notas', '').strip()

        if not direccion:
            flash('La dirección de entrega es obligatoria.', 'danger')
            return redirect(url_for('public.pago'))

        # Crear el pedido
        nuevo_pedido = Pedido(
            usuario_id = current_user.id,
            direccion  = direccion,
            notas      = notas,
            estado     = 'pendiente'
        )
        db.session.add(nuevo_pedido)
        db.session.flush()   # obtiene el ID sin hacer commit

        # Crear los detalles y descontar stock
        for prod_id, cantidad in carrito.items():
            producto = Producto.query.get(int(prod_id))
            if producto and producto.stock >= cantidad:
                detalle = DetallePedido(
                    pedido_id       = nuevo_pedido.id,
                    producto_id     = producto.id,
                    cantidad        = cantidad,
                    precio_unitario = producto.precio
                )
                producto.stock -= cantidad
                db.session.add(detalle)

        nuevo_pedido.calcular_total()
        db.session.commit()

        # Vaciar carrito de la sesión
        session.pop('carrito', None)

        flash('¡Pedido realizado con éxito!', 'success')
        return redirect(url_for('public.confirmacion', id=nuevo_pedido.id))

    # GET → mostrar resumen antes de confirmar
    items = []
    total = 0
    for prod_id, cantidad in carrito.items():
        producto = Producto.query.get(int(prod_id))
        if producto:
            subtotal = float(producto.precio) * cantidad
            total   += subtotal
            items.append({'producto': producto,
                          'cantidad': cantidad,
                          'subtotal': subtotal})

    return render_template('public/pago.html', items=items, total=total)


# ── CONFIRMACIÓN ──────────────────────────────────────────────────
@public_bp.route('/confirmacion/<int:id>')
@login_required
def confirmacion(id):
    pedido = Pedido.query.get_or_404(id)

    # Seguridad: solo el dueño del pedido puede verlo
    if pedido.usuario_id != current_user.id:
        abort(403)

    return render_template('public/confirmacion.html', pedido=pedido)


# ── MIS PEDIDOS ───────────────────────────────────────────────────
@public_bp.route('/mis-pedidos')
@login_required
def mis_pedidos():
    pedidos = Pedido.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Pedido.fecha.desc()).all()
    return render_template('public/mis_pedidos.html', pedidos=pedidos)