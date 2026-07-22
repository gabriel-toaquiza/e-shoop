import os
import uuid
from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, current_app, request
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import Usuario, Categoria, Producto, Pedido
from . import admin_bp
from .decorators import admin_requerido
from .forms import FormCategoria, FormProducto

# Umbral para considerar un producto con "bajo stock"
STOCK_MINIMO = 5

# Estados que cuentan como una venta concretada
ESTADOS_VENTA = ('pagado', 'enviado', 'entregado')

# Flujo ordenado de estados una vez confirmado el pago
FLUJO_PEDIDO = ['pagado', 'enviado', 'entregado']

# Imágenes adicionales (galería) por producto
MAX_IMAGENES = 4
EXTENSIONES_IMG = {'jpg', 'jpeg', 'webp'}


# ── HELPERS DE IMAGEN ─────────────────────────────────────────────
def guardar_imagen(archivo, subcarpeta=''):
    """Guarda la imagen en static/img/<subcarpeta> con nombre único.

    Devuelve la ruta relativa a static/img (p. ej. 'productos/abc.jpg'),
    usando siempre '/' para que sirva tanto en la URL como en disco.
    """
    nombre_seguro = secure_filename(archivo.filename)
    extension     = os.path.splitext(nombre_seguro)[1].lower()
    nombre_unico  = f"{uuid.uuid4().hex}{extension}"
    carpeta       = os.path.join(current_app.root_path, 'static', 'img', subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre_unico))
    return f"{subcarpeta}/{nombre_unico}" if subcarpeta else nombre_unico


def eliminar_imagen(nombre):
    """Elimina un archivo de static/img si existe (para no dejar huérfanos)."""
    if not nombre:
        return
    ruta = os.path.join(current_app.root_path, 'static', 'img', *nombre.split('/'))
    if os.path.exists(ruta):
        os.remove(ruta)


def _escapar_like(texto):
    """Escapa los comodines de LIKE para que el usuario no los use por error."""
    return texto.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def hay_imagen_nueva(campo):
    """True solo si el campo trae un archivo realmente subido (no un nombre previo)."""
    return isinstance(campo.data, FileStorage) and bool(campo.data.filename)


def _redirigir_seguro(referrer, fallback):
    """Redirige al referrer solo si es del mismo sitio (evita redirecciones externas)."""
    if referrer and urlparse(referrer).netloc == urlparse(request.host_url).netloc:
        return redirect(referrer)
    return redirect(fallback)


def _extension_valida(nombre):
    """True si el nombre de archivo tiene una extensión de imagen permitida."""
    ext = os.path.splitext(nombre)[1].lower().lstrip('.')
    return ext in EXTENSIONES_IMG


# ── DASHBOARD ─────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_requerido
def dashboard():
    # Ventas: suma del total solo de pedidos realmente concretados
    ventas_totales = db.session.query(
        func.coalesce(func.sum(Pedido.total), 0)
    ).filter(Pedido.estado.in_(ESTADOS_VENTA)).scalar()

    total_pedidos      = Pedido.query.count()
    pedidos_pendientes = Pedido.query.filter_by(estado='pendiente').count()

    # Productos con bajo stock (los de menor stock primero)
    productos_bajo_stock = Producto.query.filter(
        Producto.activo == True,
        Producto.stock <= STOCK_MINIMO
    ).order_by(Producto.stock.asc()).all()

    # Métricas secundarias
    total_clientes   = Usuario.query.filter_by(rol='cliente').count()
    total_productos  = Producto.query.filter_by(activo=True).count()
    total_categorias = Categoria.query.filter_by(activa=True).count()

    # Últimos 5 pedidos
    ultimos_pedidos = Pedido.query.order_by(Pedido.fecha.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           ventas_totales=ventas_totales,
                           total_pedidos=total_pedidos,
                           pedidos_pendientes=pedidos_pendientes,
                           productos_bajo_stock=productos_bajo_stock,
                           stock_minimo=STOCK_MINIMO,
                           total_clientes=total_clientes,
                           total_productos=total_productos,
                           total_categorias=total_categorias,
                           ultimos_pedidos=ultimos_pedidos)


# ── CRUD CATEGORÍAS ───────────────────────────────────────────────
@admin_bp.route('/categorias')
@login_required
@admin_requerido
def categorias():
    q      = (request.args.get('q') or '').strip()
    estado = request.args.get('estado') or ''

    consulta = Categoria.query
    if q:
        consulta = consulta.filter(Categoria.nombre.ilike(f'%{_escapar_like(q)}%', escape='\\'))
    if estado == 'activa':
        consulta = consulta.filter(Categoria.activa.is_(True))
    elif estado == 'inactiva':
        consulta = consulta.filter(Categoria.activa.is_(False))

    categorias = consulta.order_by(Categoria.nombre).all()
    return render_template('admin/categorias/listar.html',
                           categorias=categorias,
                           total=Categoria.query.count(),
                           q=q, estado=estado)


@admin_bp.route('/categorias/crear', methods=['GET', 'POST'])
@login_required
@admin_requerido
def crear_categoria():
    form = FormCategoria()
    if form.validate_on_submit():
        categoria = Categoria(
            nombre      = form.nombre.data,
            descripcion = form.descripcion.data,
            activa      = form.activa.data
        )
        if hay_imagen_nueva(form.imagen):
            categoria.imagen = guardar_imagen(form.imagen.data, 'categorias')
        db.session.add(categoria)
        db.session.commit()
        flash('Categoría creada correctamente.', 'success')
        return redirect(url_for('admin.categorias'))
    return render_template('admin/categorias/form.html',
                           form=form, titulo='Nueva categoría')


@admin_bp.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_requerido
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    form = FormCategoria(categoria_original=categoria, obj=categoria)
    if form.validate_on_submit():
        categoria.nombre      = form.nombre.data
        categoria.descripcion = form.descripcion.data
        categoria.activa      = form.activa.data

        imagen_anterior = categoria.imagen
        if hay_imagen_nueva(form.imagen):
            categoria.imagen = guardar_imagen(form.imagen.data, 'categorias')
        elif form.quitar_imagen.data and categoria.imagen:
            categoria.imagen = None

        db.session.commit()
        if imagen_anterior and imagen_anterior != categoria.imagen:
            eliminar_imagen(imagen_anterior)
        flash('Categoría actualizada correctamente.', 'success')
        return redirect(url_for('admin.categorias'))
    return render_template('admin/categorias/form.html',
                           form=form, titulo='Editar categoría', categoria=categoria)


@admin_bp.route('/categorias/<int:id>/toggle', methods=['POST'])
@login_required
@admin_requerido
def toggle_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    categoria.activa = not categoria.activa
    db.session.commit()
    estado = 'activada' if categoria.activa else 'desactivada'
    flash(f'Categoría "{categoria.nombre}" {estado}.', 'info')
    return _redirigir_seguro(request.referrer, url_for('admin.categorias'))


@admin_bp.route('/categorias/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_requerido
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    # No se puede borrar si tiene productos (rompería las claves foráneas)
    if categoria.productos:
        flash('No se puede eliminar: la categoría tiene productos asociados. '
              'Elimina o mueve esos productos primero.', 'warning')
        return _redirigir_seguro(request.referrer, url_for('admin.categorias'))

    nombre = categoria.nombre
    eliminar_imagen(categoria.imagen)
    db.session.delete(categoria)
    db.session.commit()
    flash(f'Categoría "{nombre}" eliminada.', 'success')
    return _redirigir_seguro(request.referrer, url_for('admin.categorias'))


# ── CRUD PRODUCTOS ────────────────────────────────────────────────
@admin_bp.route('/productos')
@login_required
@admin_requerido
def productos():
    q         = (request.args.get('q') or '').strip()
    categoria = request.args.get('categoria', type=int)
    estado    = request.args.get('estado') or ''
    stock     = request.args.get('stock') or ''

    consulta = Producto.query
    if q:
        consulta = consulta.filter(Producto.nombre.ilike(f'%{_escapar_like(q)}%', escape='\\'))
    if categoria:
        consulta = consulta.filter(Producto.categoria_id == categoria)
    if estado == 'activo':
        consulta = consulta.filter(Producto.activo.is_(True))
    elif estado == 'inactivo':
        consulta = consulta.filter(Producto.activo.is_(False))
    if stock == 'bajo':
        consulta = consulta.filter(Producto.stock <= STOCK_MINIMO)

    productos = consulta.order_by(Producto.nombre).all()
    return render_template('admin/productos/listar.html',
                           productos=productos,
                           total=Producto.query.count(),
                           categorias=Categoria.query.order_by(Categoria.nombre).all(),
                           stock_minimo=STOCK_MINIMO,
                           q=q, categoria=categoria, estado=estado, stock=stock)


@admin_bp.route('/productos/crear', methods=['GET', 'POST'])
@login_required
@admin_requerido
def crear_producto():
    categorias_activas = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    if not categorias_activas:
        flash('Primero debes crear al menos una categoría activa.', 'warning')
        return redirect(url_for('admin.categorias'))

    form = FormProducto()
    form.categoria_id.choices = [(c.id, c.nombre) for c in categorias_activas]

    if form.validate_on_submit():
        producto = Producto(
            nombre       = form.nombre.data,
            descripcion  = form.descripcion.data,
            precio       = form.precio.data,
            stock        = form.stock.data or 0,
            categoria_id = form.categoria_id.data,
            personalizable = form.personalizable.data,
            instrucciones_personalizacion = form.instrucciones_personalizacion.data or None,
            activo       = form.activo.data
        )
        guardadas = []   # todos los archivos guardados, para limpiar si falla el commit

        # Portada
        if hay_imagen_nueva(form.imagen):
            producto.imagen = guardar_imagen(form.imagen.data, 'productos')
            guardadas.append(producto.imagen)

        # Imágenes adicionales (galería), máximo MAX_IMAGENES
        adicionales = []
        for archivo in (form.imagenes_nuevas.data or []):
            if len(adicionales) >= MAX_IMAGENES:
                break
            if isinstance(archivo, FileStorage) and archivo.filename and _extension_valida(archivo.filename):
                nombre = guardar_imagen(archivo, 'productos')
                adicionales.append(nombre)
                guardadas.append(nombre)
        if adicionales:
            producto.imagenes = ','.join(adicionales)

        db.session.add(producto)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            for n in guardadas:
                eliminar_imagen(n)
            flash('No se pudo crear el producto. Intenta de nuevo.', 'danger')
            return redirect(url_for('admin.crear_producto'))

        flash('Producto creado correctamente.', 'success')
        return redirect(url_for('admin.productos'))

    return render_template('admin/productos/form.html',
                           form=form, titulo='Nuevo producto')


@admin_bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_requerido
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    categorias_activas = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()

    form = FormProducto(obj=producto)
    choices = [(c.id, c.nombre) for c in categorias_activas]
    # Mantener la categoría actual en las opciones aunque esté inactiva
    if producto.categoria and producto.categoria_id not in [c.id for c in categorias_activas]:
        choices.insert(0, (producto.categoria_id, producto.categoria.nombre + ' (inactiva)'))
    form.categoria_id.choices = choices

    if form.validate_on_submit():
        producto.nombre       = form.nombre.data
        producto.descripcion  = form.descripcion.data
        producto.precio       = form.precio.data
        producto.stock        = form.stock.data or 0
        producto.categoria_id = form.categoria_id.data
        producto.personalizable = form.personalizable.data
        producto.instrucciones_personalizacion = form.instrucciones_personalizacion.data or None
        producto.activo       = form.activo.data

        # --- Portada ---
        imagen_anterior = producto.imagen
        imagen_nueva    = None
        if hay_imagen_nueva(form.imagen):
            imagen_nueva    = guardar_imagen(form.imagen.data, 'productos')
            producto.imagen = imagen_nueva
        elif form.quitar_imagen.data and producto.imagen:
            producto.imagen = None

        # --- Imágenes adicionales ---
        adicionales = producto.lista_imagenes()
        a_borrar    = request.form.getlist('borrar_imagenes')
        adicionales = [img for img in adicionales if img not in a_borrar]

        nuevas_guardadas = []
        for archivo in (form.imagenes_nuevas.data or []):
            if len(adicionales) >= MAX_IMAGENES:
                break
            if isinstance(archivo, FileStorage) and archivo.filename and _extension_valida(archivo.filename):
                nombre = guardar_imagen(archivo, 'productos')
                adicionales.append(nombre)
                nuevas_guardadas.append(nombre)
        producto.imagenes = ','.join(adicionales) if adicionales else None

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            eliminar_imagen(imagen_nueva)
            for n in nuevas_guardadas:
                eliminar_imagen(n)
            flash('No se pudo actualizar el producto. Intenta de nuevo.', 'danger')
            return redirect(url_for('admin.editar_producto', id=id))

        # Commit OK: borrar del disco lo que ya no se usa
        if imagen_anterior and imagen_anterior != producto.imagen:
            eliminar_imagen(imagen_anterior)
        for nombre in a_borrar:
            eliminar_imagen(nombre)

        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('admin.productos'))

    return render_template('admin/productos/form.html',
                           form=form, titulo='Editar producto', producto=producto)


@admin_bp.route('/productos/<int:id>/toggle', methods=['POST'])
@login_required
@admin_requerido
def toggle_producto(id):
    producto = Producto.query.get_or_404(id)
    producto.activo = not producto.activo
    db.session.commit()
    estado = 'activado' if producto.activo else 'desactivado'
    flash(f'Producto "{producto.nombre}" {estado}.', 'info')
    return _redirigir_seguro(request.referrer, url_for('admin.productos'))


@admin_bp.route('/productos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_requerido
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    # No se puede borrar si está en pedidos (rompería el historial)
    if producto.detalles:
        flash('No se puede eliminar: el producto tiene pedidos asociados. '
              'Desactívalo en su lugar.', 'warning')
        return _redirigir_seguro(request.referrer, url_for('admin.productos'))

    nombre = producto.nombre
    # Borrar sus imágenes del disco
    eliminar_imagen(producto.imagen)
    for img in producto.lista_imagenes():
        eliminar_imagen(img)

    db.session.delete(producto)
    db.session.commit()
    flash(f'Producto "{nombre}" eliminado.', 'success')
    return _redirigir_seguro(request.referrer, url_for('admin.productos'))


# ── GESTIÓN DE CLIENTES ───────────────────────────────────────────
@admin_bp.route('/clientes')
@login_required
@admin_requerido
def clientes():
    clientes = Usuario.query.filter_by(rol='cliente').order_by(Usuario.nombre).all()
    return render_template('admin/clientes/listar.html', clientes=clientes)


@admin_bp.route('/clientes/<int:id>/toggle', methods=['POST'])
@login_required
@admin_requerido
def toggle_cliente(id):
    cliente = Usuario.query.get_or_404(id)
    # Seguridad: solo se gestionan cuentas de clientes (nunca las de admin)
    if cliente.rol != 'cliente':
        flash('Solo se pueden activar/desactivar cuentas de clientes.', 'warning')
        return redirect(url_for('admin.clientes'))

    cliente.activo = not cliente.activo
    db.session.commit()
    estado = 'activada' if cliente.activo else 'desactivada'
    flash(f'Cuenta de "{cliente.nombre}" {estado}.', 'info')
    return redirect(url_for('admin.clientes'))


# ── GESTIÓN DE PEDIDOS ────────────────────────────────────────────
@admin_bp.route('/pedidos')
@login_required
@admin_requerido
def pedidos():
    estado = request.args.get('estado', '').strip()
    query = Pedido.query
    if estado:
        query = query.filter_by(estado=estado)
    pedidos = query.order_by(Pedido.fecha.desc()).all()
    return render_template('admin/pedidos/listar.html',
                           pedidos=pedidos, estado=estado, flujo=FLUJO_PEDIDO)


@admin_bp.route('/pedidos/<int:id>')
@login_required
@admin_requerido
def detalle_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    return render_template('admin/pedidos/detalle.html', pedido=pedido)


@admin_bp.route('/pedidos/<int:id>/avanzar', methods=['POST'])
@login_required
@admin_requerido
def avanzar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado not in FLUJO_PEDIDO:
        flash('Este pedido no se puede avanzar.', 'warning')
        return _redirigir_seguro(request.referrer, url_for('admin.pedidos'))

    indice = FLUJO_PEDIDO.index(pedido.estado)
    if indice >= len(FLUJO_PEDIDO) - 1:
        flash(f'El pedido #{pedido.id} ya está entregado.', 'info')
    else:
        pedido.estado = FLUJO_PEDIDO[indice + 1]
        db.session.commit()
        flash(f'Pedido #{pedido.id} actualizado a "{pedido.estado}".', 'success')
    return _redirigir_seguro(request.referrer, url_for('admin.pedidos'))


@admin_bp.route('/pedidos/<int:id>/confirmar-pago', methods=['POST'])
@login_required
@admin_requerido
def confirmar_pago(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado not in ('en_verificacion', 'rechazado'):
        flash('Este pedido no está a la espera de confirmación de pago.', 'warning')
        return _redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))

    # Revalidar stock antes de descontar (pudo cambiar desde que se hizo el pedido)
    faltantes = []
    necesario = {}
    for d in pedido.detalles:
        if d.producto:
            necesario[d.producto] = necesario.get(d.producto, 0) + d.cantidad
    for producto, cantidad in necesario.items():
        if producto.stock < cantidad:
            faltantes.append(f'{producto.nombre} (disponible {producto.stock}, requiere {cantidad})')
    if faltantes:
        flash('No se puede confirmar: sin stock suficiente de ' + ', '.join(faltantes) + '.', 'danger')
        return _redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))

    # Descontar stock y marcar como pagado
    for producto, cantidad in necesario.items():
        producto.stock -= cantidad
    pedido.estado = 'pagado'
    db.session.commit()
    flash(f'Pago del pedido #{pedido.id} confirmado. Stock descontado.', 'success')
    return _redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))


@admin_bp.route('/pedidos/<int:id>/rechazar-pago', methods=['POST'])
@login_required
@admin_requerido
def rechazar_pago(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado != 'en_verificacion':
        flash('Solo se puede rechazar un pago en verificación.', 'warning')
    else:
        pedido.estado = 'rechazado'
        db.session.commit()
        flash(f'Comprobante del pedido #{pedido.id} rechazado. El cliente puede subir otro.', 'info')
    return _redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))


@admin_bp.route('/pedidos/<int:id>/cancelar', methods=['POST'])
@login_required
@admin_requerido
def cancelar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado in ('entregado', 'cancelado'):
        flash('Este pedido ya no se puede cancelar.', 'warning')
    else:
        # Si el pago ya estaba confirmado, se repone el stock descontado
        if pedido.estado in ESTADOS_VENTA:
            for d in pedido.detalles:
                if d.producto:
                    d.producto.stock += d.cantidad
        pedido.estado = 'cancelado'
        db.session.commit()
        flash(f'Pedido #{pedido.id} cancelado.', 'info')
    return _redirigir_seguro(request.referrer, url_for('admin.pedidos'))
