from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Categoria, Pedido, DetallePedido
from app.blueprints.public import public_bp


def _volver_atras(fallback):
    """Redirige a la página anterior si es del mismo sitio; si no, al fallback."""
    destino = request.referrer
    if not destino or urlparse(destino).netloc != urlparse(request.host_url).netloc:
        destino = fallback
    return redirect(destino)


# ── HOME ──────────────────────────────────────────────────────────
@public_bp.route('/')
def home():
    productos_destacados = (Producto.query.join(Categoria)
                            .filter(Producto.activo == True, Categoria.activa == True)
                            .limit(8).all())
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

    query = (Producto.query.join(Categoria)
             .filter(Producto.activo == True, Categoria.activa == True))

    # Filtro por categoría
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)

    # Filtro por búsqueda (se escapan los comodines del usuario)
    if busqueda:
        termino = busqueda.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.filter(Producto.nombre.ilike(f'%{termino}%', escape='\\'))

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
    # No mostrar productos inactivos ni de categorías desactivadas
    if not producto.activo or (producto.categoria and not producto.categoria.activa):
        abort(404)
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
        producto = db.session.get(Producto, int(prod_id))
        if producto and producto.activo:
            subtotal = producto.precio * cantidad
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

    if not producto.activo or (producto.categoria and not producto.categoria.activa):
        abort(404)

    if not producto.tiene_stock():
        flash('Producto sin stock disponible.', 'warning')
        return redirect(url_for('public.tienda'))

    carrito = session.get('carrito', {})
    clave   = str(id)
    try:
        cantidad_solicitada = int(request.form.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad_solicitada = 1
    if cantidad_solicitada < 1:
        cantidad_solicitada = 1

    # Sumar si ya existe en el carrito
    carrito[clave] = carrito.get(clave, 0) + cantidad_solicitada

    # No superar el stock disponible
    if carrito[clave] > producto.stock:
        carrito[clave] = producto.stock
        flash('Cantidad ajustada al stock disponible.', 'info')

    session['carrito'] = carrito
    flash(f'"{producto.nombre}" agregado al carrito.', 'success')
    return _volver_atras(url_for('public.tienda'))


@public_bp.route('/carrito/eliminar/<int:id>', methods=['POST'])
def eliminar_carrito(id):
    carrito = session.get('carrito', {})
    carrito.pop(str(id), None)
    session['carrito'] = carrito
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('public.carrito'))


@public_bp.route('/carrito/actualizar/<int:id>', methods=['POST'])
def actualizar_carrito(id):
    carrito = session.get('carrito', {})
    clave   = str(id)
    if clave not in carrito:
        return redirect(url_for('public.carrito'))

    accion   = request.form.get('accion')
    producto = db.session.get(Producto, id)

    if accion == 'sumar':
        carrito[clave] += 1
        if producto and carrito[clave] > producto.stock:
            carrito[clave] = producto.stock
            flash('Cantidad ajustada al stock disponible.', 'info')
    elif accion == 'restar':
        if carrito[clave] > 1:
            carrito[clave] -= 1

    session['carrito'] = carrito
    return redirect(url_for('public.carrito'))


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

        # Seleccionar solo las líneas que se pueden cumplir (activo y con stock)
        lineas   = []
        omitidos = []
        for prod_id, cantidad in carrito.items():
            producto = db.session.get(Producto, int(prod_id))
            if producto and producto.activo and producto.stock >= cantidad:
                lineas.append((producto, cantidad))
            elif producto:
                omitidos.append(producto.nombre)

        # No crear un pedido vacío
        if not lineas:
            flash('No se pudo procesar el pedido: los productos ya no están '
                  'disponibles o no tienen stock suficiente.', 'danger')
            return redirect(url_for('public.carrito'))

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
        for producto, cantidad in lineas:
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

        if omitidos:
            flash('Algunos productos no se incluyeron por falta de stock: '
                  + ', '.join(omitidos) + '.', 'warning')
        flash('¡Pedido realizado con éxito!', 'success')
        return redirect(url_for('public.confirmacion', id=nuevo_pedido.id))

    # GET → mostrar resumen antes de confirmar
    items = []
    total = 0
    for prod_id, cantidad in carrito.items():
        producto = db.session.get(Producto, int(prod_id))
        if producto and producto.activo:
            subtotal = producto.precio * cantidad
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


# ── ACERCA DE ─────────────────────────────────────────────────────
@public_bp.route('/acerca')
def acerca():
    return render_template('public/acerca.html')


# ── PÁGINAS INFORMATIVAS (solo banner por ahora) ──────────────────
@public_bp.route('/contacto')
def contacto():
    return render_template('public/contacto.html')


@public_bp.route('/terminos')
def terminos():
    return render_template('public/terminos.html')


@public_bp.route('/privacidad')
def privacidad():
    return render_template('public/privacidad.html')


# ── FAVORITOS ─────────────────────────────────────────────────────
@public_bp.route('/favoritos/toggle/<int:id>', methods=['POST'])
def toggle_favorito(id):
    producto = Producto.query.get_or_404(id)

    if current_user.is_authenticated:
        # Usuario logueado → se guarda en la base de datos
        if producto in current_user.favoritos:
            current_user.favoritos.remove(producto)
            flash(f'"{producto.nombre}" quitado de favoritos.', 'info')
        else:
            current_user.favoritos.append(producto)
            flash(f'"{producto.nombre}" agregado a favoritos.', 'success')
        db.session.commit()
    else:
        # Usuario anónimo → se guarda en la sesión
        favs = session.get('favoritos', [])
        if id in favs:
            favs.remove(id)
            flash(f'"{producto.nombre}" quitado de favoritos.', 'info')
        else:
            favs.append(id)
            flash(f'"{producto.nombre}" agregado a favoritos.', 'success')
        session['favoritos'] = favs

    return _volver_atras(url_for('public.favoritos'))


@public_bp.route('/favoritos')
def favoritos():
    if current_user.is_authenticated:
        productos = current_user.favoritos
    else:
        ids = session.get('favoritos', [])
        productos = Producto.query.filter(Producto.id.in_(ids)).all() if ids else []
    return render_template('public/favoritos.html', productos=productos)