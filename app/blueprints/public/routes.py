from flask import (render_template, redirect, url_for, flash, request, session,
                   abort, current_app, send_from_directory)
from werkzeug.datastructures import FileStorage
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Producto, Categoria, Pedido, DetallePedido
from app.estados import ESTADOS_VENTA
from app.utils import volver_atras
from app.blueprints.public import public_bp
from app.blueprints.public.carrito_utils import (
    clave_item, normalizar_carrito, unidades_producto, MAX_ESPECIFICACIONES)
from app.blueprints.public.pagos_utils import (
    cedula_valida, guardar_comprobante, extension_comprobante_valida,
    carpeta_comprobantes, eliminar_comprobante)


def _categoria_mas_vendida():
    """Categoría activa con más unidades vendidas. None si todavía no hay ventas."""
    fila = (db.session.query(Categoria)
            .join(Producto, Producto.categoria_id == Categoria.id)
            .join(DetallePedido, DetallePedido.producto_id == Producto.id)
            .join(Pedido, Pedido.id == DetallePedido.pedido_id)
            .filter(Categoria.activa.is_(True), Pedido.estado.in_(ESTADOS_VENTA))
            .group_by(Categoria.id)
            .order_by(func.sum(DetallePedido.cantidad).desc())
            .first())
    return fila


def _resumen_carrito(carrito):
    """Devuelve (items, total) a partir del carrito normalizado."""
    items = []
    total = 0
    for clave, linea in carrito.items():
        producto = db.session.get(Producto, linea['producto_id'])
        if producto and producto.activo:
            subtotal = producto.precio * linea['cantidad']
            total   += subtotal
            items.append({'producto': producto,
                          'cantidad': linea['cantidad'],
                          'especificaciones': linea['especificaciones'],
                          'subtotal': subtotal})
    return items, total


# ── HOME ──────────────────────────────────────────────────────────
@public_bp.route('/')
def home():
    productos_destacados = (Producto.query.join(Categoria)
                            .filter(Producto.activo == True, Categoria.activa == True)
                            .order_by(Producto.creado_en.desc())
                            .limit(8).all())
    # La más vendida se destaca aparte, así que se excluye de las otras 3
    mas_vendida = _categoria_mas_vendida()
    consulta = Categoria.query.filter_by(activa=True)
    if mas_vendida:
        consulta = consulta.filter(Categoria.id != mas_vendida.id)
    # Sin ventas todavía: se rellenan las 4 casillas con categorías normales
    categorias = consulta.order_by(Categoria.nombre).limit(3 if mas_vendida else 4).all()

    return render_template('public/home.html',
                           productos=productos_destacados,
                           categorias=categorias,
                           mas_vendida=mas_vendida)


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
    carrito = normalizar_carrito(session.get('carrito', {}))
    items   = []
    total   = 0

    for clave, linea in carrito.items():
        producto = db.session.get(Producto, linea['producto_id'])
        if producto and producto.activo:
            subtotal = producto.precio * linea['cantidad']
            total   += subtotal
            items.append({
                'clave': clave,
                'producto': producto,
                'cantidad': linea['cantidad'],
                'especificaciones': linea['especificaciones'],
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

    carrito = normalizar_carrito(session.get('carrito', {}))

    # Especificaciones: solo para productos personalizables y obligatorias
    especificaciones = ''
    if producto.personalizable:
        especificaciones = request.form.get('especificaciones', '').strip()
        if not especificaciones:
            flash('Indica las especificaciones para personalizar este producto.', 'warning')
            return volver_atras(url_for('public.detalle_producto', id=id))
        especificaciones = especificaciones[:MAX_ESPECIFICACIONES]

    try:
        cantidad_solicitada = int(request.form.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad_solicitada = 1
    if cantidad_solicitada < 1:
        cantidad_solicitada = 1

    # Unidades de este producto ya presentes en el carrito (en todas sus líneas)
    disponible = producto.stock - unidades_producto(carrito, id)
    if disponible <= 0:
        flash('No hay más stock disponible de este producto.', 'warning')
        return volver_atras(url_for('public.detalle_producto', id=id))
    if cantidad_solicitada > disponible:
        cantidad_solicitada = disponible
        flash('Cantidad ajustada al stock disponible.', 'info')

    clave = clave_item(id, especificaciones)
    if clave in carrito:
        carrito[clave]['cantidad'] += cantidad_solicitada
    else:
        carrito[clave] = {
            'producto_id': id,
            'cantidad': cantidad_solicitada,
            'especificaciones': especificaciones
        }

    session['carrito'] = carrito
    flash(f'"{producto.nombre}" agregado al carrito.', 'success')
    return volver_atras(url_for('public.tienda'))


@public_bp.route('/carrito/eliminar/<clave>', methods=['POST'])
def eliminar_carrito(clave):
    carrito = normalizar_carrito(session.get('carrito', {}))
    carrito.pop(clave, None)
    session['carrito'] = carrito
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('public.carrito'))


@public_bp.route('/carrito/actualizar/<clave>', methods=['POST'])
def actualizar_carrito(clave):
    carrito = normalizar_carrito(session.get('carrito', {}))
    if clave not in carrito:
        return redirect(url_for('public.carrito'))

    linea    = carrito[clave]
    accion   = request.form.get('accion')
    producto = db.session.get(Producto, linea['producto_id'])

    if accion == 'sumar':
        # No superar el stock sumando todas las líneas del mismo producto
        if producto and unidades_producto(carrito, linea['producto_id']) < producto.stock:
            linea['cantidad'] += 1
        else:
            flash('No hay más stock disponible de este producto.', 'info')
    elif accion == 'restar':
        if linea['cantidad'] > 1:
            linea['cantidad'] -= 1

    session['carrito'] = carrito
    return redirect(url_for('public.carrito'))


# ── PAGO ──────────────────────────────────────────────────────────
@public_bp.route('/pago', methods=['GET', 'POST'])
@login_required
def pago():
    carrito = normalizar_carrito(session.get('carrito', {}))

    if not carrito:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('public.tienda'))

    if request.method == 'POST':
        nombre    = request.form.get('nombre_receptor', '').strip()
        cedula    = request.form.get('cedula', '').strip()
        direccion = request.form.get('direccion', '').strip()
        notas     = request.form.get('notas', '').strip()
        archivo   = request.files.get('comprobante')

        # Validación de datos de entrega y del comprobante (obligatorio)
        errores = []
        if not nombre:
            errores.append('El nombre de quien recibe es obligatorio.')
        if not cedula_valida(cedula):
            errores.append('La cédula no es válida (debe ser una cédula ecuatoriana de 10 dígitos).')
        if not direccion:
            errores.append('La dirección de entrega es obligatoria.')
        if not (isinstance(archivo, FileStorage) and archivo.filename):
            errores.append('Debes adjuntar el comprobante de la transferencia.')
        elif not extension_comprobante_valida(archivo.filename):
            errores.append('El comprobante debe ser una imagen (jpg, png, webp) o un PDF.')
        if errores:
            for e in errores:
                flash(e, 'danger')
            items, total = _resumen_carrito(carrito)
            return render_template('public/pago.html', items=items, total=total,
                                   datos_banco=current_app.config['DATOS_BANCARIOS'],
                                   nombre=nombre, cedula=cedula,
                                   direccion=direccion, notas=notas)

        # El stock NO se descuenta aquí: se descuenta cuando el admin confirma el
        # pago. Solo comprobamos que haya disponibilidad al momento del pedido.
        lineas   = []
        omitidos = []
        usado    = {}
        for clave, linea in carrito.items():
            producto = db.session.get(Producto, linea['producto_id'])
            if not (producto and producto.activo):
                if producto:
                    omitidos.append(producto.nombre)
                continue
            comprometido = usado.get(producto.id, 0)
            if producto.stock - comprometido >= linea['cantidad']:
                lineas.append((producto, linea['cantidad'], linea['especificaciones']))
                usado[producto.id] = comprometido + linea['cantidad']
            else:
                omitidos.append(producto.nombre)

        if not lineas:
            flash('No se pudo procesar el pedido: los productos ya no están '
                  'disponibles o no tienen stock suficiente.', 'danger')
            return redirect(url_for('public.carrito'))

        # Crear el pedido ya con el comprobante → "En verificación"
        nuevo_pedido = Pedido(
            usuario_id      = current_user.id,
            nombre_receptor = nombre,
            cedula          = cedula,
            direccion       = direccion,
            notas           = notas,
            estado          = 'en_verificacion'
        )
        db.session.add(nuevo_pedido)
        db.session.flush()

        for producto, cantidad, especificaciones in lineas:
            db.session.add(DetallePedido(
                pedido_id        = nuevo_pedido.id,
                producto_id      = producto.id,
                cantidad         = cantidad,
                precio_unitario  = producto.precio,
                especificaciones = especificaciones or None
            ))

        nuevo_pedido.comprobante = guardar_comprobante(archivo, nuevo_pedido.id)
        nuevo_pedido.calcular_total()
        db.session.commit()

        # Vaciar carrito de la sesión
        session.pop('carrito', None)

        if omitidos:
            flash('Algunos productos no se incluyeron por falta de stock: '
                  + ', '.join(omitidos) + '.', 'warning')
        flash('¡Pedido recibido! Estamos verificando tu pago.', 'success')
        return redirect(url_for('public.confirmacion', id=nuevo_pedido.id))

    # GET → mostrar resumen, datos del banco y formulario (incluye comprobante)
    items, total = _resumen_carrito(carrito)
    return render_template('public/pago.html', items=items, total=total,
                           datos_banco=current_app.config['DATOS_BANCARIOS'])


# ── CONFIRMACIÓN ──────────────────────────────────────────────────
@public_bp.route('/confirmacion/<int:id>')
@login_required
def confirmacion(id):
    pedido = Pedido.query.get_or_404(id)

    # Seguridad: solo el dueño del pedido puede verlo
    if pedido.usuario_id != current_user.id:
        abort(403)

    return render_template('public/confirmacion.html', pedido=pedido,
                           datos_banco=current_app.config['DATOS_BANCARIOS'])


@public_bp.route('/pedido/<int:id>/comprobante', methods=['POST'])
@login_required
def subir_comprobante(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.usuario_id != current_user.id:
        abort(403)

    # Solo se puede volver a subir cuando el comprobante fue rechazado
    if pedido.estado != 'rechazado':
        flash('Este pedido ya no admite un nuevo comprobante.', 'warning')
        return redirect(url_for('public.confirmacion', id=id))

    archivo = request.files.get('comprobante')
    if not (isinstance(archivo, FileStorage) and archivo.filename):
        flash('Selecciona el archivo del comprobante.', 'danger')
        return redirect(url_for('public.confirmacion', id=id))
    if not extension_comprobante_valida(archivo.filename):
        flash('Formato no permitido. Usa una imagen (jpg, png, webp) o PDF.', 'danger')
        return redirect(url_for('public.confirmacion', id=id))

    eliminar_comprobante(pedido.comprobante)          # si reemplaza uno anterior
    pedido.comprobante = guardar_comprobante(archivo, pedido.id)
    pedido.estado = 'en_verificacion'
    db.session.commit()

    flash('¡Comprobante recibido! Estamos verificando tu pago.', 'success')
    return redirect(url_for('public.confirmacion', id=id))


@public_bp.route('/pedido/<int:id>/comprobante/ver')
@login_required
def ver_comprobante(id):
    """Sirve el comprobante desde la carpeta privada. Solo dueño o admin."""
    pedido = Pedido.query.get_or_404(id)
    if pedido.usuario_id != current_user.id and not current_user.es_admin():
        abort(403)
    if not pedido.comprobante:
        abort(404)
    return send_from_directory(carpeta_comprobantes(), pedido.comprobante)


# ── MIS PEDIDOS ───────────────────────────────────────────────────
@public_bp.route('/mis-pedidos')
@login_required
def mis_pedidos():
    pedidos = Pedido.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Pedido.fecha.desc()).all()
    return render_template('public/mis_pedidos.html', pedidos=pedidos)


# ── NOSOTROS ──────────────────────────────────────────────────────
@public_bp.route('/nosotros')
def nosotros():
    return render_template('public/nosotros.html')


# ── PÁGINAS INFORMATIVAS ──────────────────────────────────────────
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

    return volver_atras(url_for('public.favoritos'))


@public_bp.route('/favoritos')
def favoritos():
    if current_user.is_authenticated:
        productos = current_user.favoritos
    else:
        ids = session.get('favoritos', [])
        productos = Producto.query.filter(Producto.id.in_(ids)).all() if ids else []
    return render_template('public/favoritos.html', productos=productos)