import os
import uuid
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

# Flujo ordenado de estados de un pedido
FLUJO_PEDIDO = ['pendiente', 'pagado', 'enviado', 'entregado']


# ── HELPERS DE IMAGEN ─────────────────────────────────────────────
def guardar_imagen(archivo):
    """Guarda la imagen subida en static/img con un nombre único y lo devuelve."""
    nombre_seguro = secure_filename(archivo.filename)
    extension     = os.path.splitext(nombre_seguro)[1].lower()
    nombre_unico  = f"{uuid.uuid4().hex}{extension}"
    carpeta       = os.path.join(current_app.root_path, 'static', 'img')
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre_unico))
    return nombre_unico


def eliminar_imagen(nombre):
    """Elimina un archivo de static/img si existe (para no dejar huérfanos)."""
    if not nombre:
        return
    ruta = os.path.join(current_app.root_path, 'static', 'img', nombre)
    if os.path.exists(ruta):
        os.remove(ruta)


def hay_imagen_nueva(campo):
    """True solo si el campo trae un archivo realmente subido (no un nombre previo)."""
    return isinstance(campo.data, FileStorage) and bool(campo.data.filename)


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
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('admin/categorias/listar.html', categorias=categorias)


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
        db.session.commit()
        flash('Categoría actualizada correctamente.', 'success')
        return redirect(url_for('admin.categorias'))
    return render_template('admin/categorias/form.html',
                           form=form, titulo='Editar categoría')


@admin_bp.route('/categorias/<int:id>/toggle', methods=['POST'])
@login_required
@admin_requerido
def toggle_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    categoria.activa = not categoria.activa
    db.session.commit()
    estado = 'activada' if categoria.activa else 'desactivada'
    flash(f'Categoría "{categoria.nombre}" {estado}.', 'info')
    return redirect(url_for('admin.categorias'))


# ── CRUD PRODUCTOS ────────────────────────────────────────────────
@admin_bp.route('/productos')
@login_required
@admin_requerido
def productos():
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template('admin/productos/listar.html',
                           productos=productos, stock_minimo=STOCK_MINIMO)


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
            activo       = form.activo.data
        )
        if hay_imagen_nueva(form.imagen):
            producto.imagen = guardar_imagen(form.imagen.data)

        db.session.add(producto)
        db.session.commit()
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
        producto.activo       = form.activo.data

        if hay_imagen_nueva(form.imagen):
            # Se subió una nueva: reemplaza la anterior
            eliminar_imagen(producto.imagen)
            producto.imagen = guardar_imagen(form.imagen.data)
        elif form.quitar_imagen.data and producto.imagen:
            # Se pidió quitar la imagen y dejar el producto sin foto
            eliminar_imagen(producto.imagen)
            producto.imagen = None

        db.session.commit()
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
    return redirect(url_for('admin.productos'))


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
        return redirect(request.referrer or url_for('admin.pedidos'))

    indice = FLUJO_PEDIDO.index(pedido.estado)
    if indice >= len(FLUJO_PEDIDO) - 1:
        flash(f'El pedido #{pedido.id} ya está entregado.', 'info')
    else:
        pedido.estado = FLUJO_PEDIDO[indice + 1]
        db.session.commit()
        flash(f'Pedido #{pedido.id} actualizado a "{pedido.estado}".', 'success')
    return redirect(request.referrer or url_for('admin.pedidos'))


@admin_bp.route('/pedidos/<int:id>/cancelar', methods=['POST'])
@login_required
@admin_requerido
def cancelar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado in ('entregado', 'cancelado'):
        flash('Este pedido ya no se puede cancelar.', 'warning')
    else:
        pedido.estado = 'cancelado'
        db.session.commit()
        flash(f'Pedido #{pedido.id} cancelado.', 'info')
    return redirect(request.referrer or url_for('admin.pedidos'))
