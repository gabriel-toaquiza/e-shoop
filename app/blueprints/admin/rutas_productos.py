"""CRUD de productos (con portada y galería de imágenes)."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from werkzeug.datastructures import FileStorage
from app import db
from app.models import Categoria, Producto
from app.utils import redirigir_seguro
from . import admin_bp
from .decorators import admin_requerido
from .forms import FormProducto
from .helpers import (STOCK_MINIMO, MAX_IMAGENES, guardar_imagen, eliminar_imagen,
                      escapar_like, hay_imagen_nueva, extension_valida)


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
        consulta = consulta.filter(Producto.nombre.ilike(f'%{escapar_like(q)}%', escape='\\'))
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
            if isinstance(archivo, FileStorage) and archivo.filename and extension_valida(archivo.filename):
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
            if isinstance(archivo, FileStorage) and archivo.filename and extension_valida(archivo.filename):
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
    return redirigir_seguro(request.referrer, url_for('admin.productos'))


@admin_bp.route('/productos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_requerido
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    # No se puede borrar si está en pedidos (rompería el historial)
    if producto.detalles:
        flash('No se puede eliminar: el producto tiene pedidos asociados. '
              'Desactívalo en su lugar.', 'warning')
        return redirigir_seguro(request.referrer, url_for('admin.productos'))

    nombre = producto.nombre
    # Borrar sus imágenes del disco
    eliminar_imagen(producto.imagen)
    for img in producto.lista_imagenes():
        eliminar_imagen(img)

    db.session.delete(producto)
    db.session.commit()
    flash(f'Producto "{nombre}" eliminado.', 'success')
    return redirigir_seguro(request.referrer, url_for('admin.productos'))
