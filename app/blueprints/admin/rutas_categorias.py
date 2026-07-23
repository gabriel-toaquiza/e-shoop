"""CRUD de categorías."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Categoria
from app.utils import redirigir_seguro
from . import admin_bp
from .decorators import admin_requerido
from .forms import FormCategoria
from .helpers import guardar_imagen, eliminar_imagen, escapar_like, hay_imagen_nueva


@admin_bp.route('/categorias')
@login_required
@admin_requerido
def categorias():
    q      = (request.args.get('q') or '').strip()
    estado = request.args.get('estado') or ''

    consulta = Categoria.query
    if q:
        consulta = consulta.filter(Categoria.nombre.ilike(f'%{escapar_like(q)}%', escape='\\'))
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
    return redirigir_seguro(request.referrer, url_for('admin.categorias'))


@admin_bp.route('/categorias/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_requerido
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    # No se puede borrar si tiene productos (rompería las claves foráneas)
    if categoria.productos:
        flash('No se puede eliminar: la categoría tiene productos asociados. '
              'Elimina o mueve esos productos primero.', 'warning')
        return redirigir_seguro(request.referrer, url_for('admin.categorias'))

    nombre = categoria.nombre
    eliminar_imagen(categoria.imagen)
    db.session.delete(categoria)
    db.session.commit()
    flash(f'Categoría "{nombre}" eliminada.', 'success')
    return redirigir_seguro(request.referrer, url_for('admin.categorias'))
