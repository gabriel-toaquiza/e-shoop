from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import Usuario, Categoria, Producto, Pedido
from . import admin_bp
from .decorators import admin_requerido
from .forms import FormCategoria

# Umbral para considerar un producto con "bajo stock"
STOCK_MINIMO = 5

# Estados que cuentan como una venta concretada
ESTADOS_VENTA = ('pagado', 'enviado', 'entregado')


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


# ── RUTAS PENDIENTES (se construyen en los siguientes puntos) ─────
@admin_bp.route('/admin/productos')
def productos():
    return render_template('admin/productos.html')

@admin_bp.route('/admin/clientes')
def clientes():
    return render_template('admin/clientes.html')

@admin_bp.route('/admin/pedidos')
def pedidos():
    return render_template('admin/pedidos.html')
