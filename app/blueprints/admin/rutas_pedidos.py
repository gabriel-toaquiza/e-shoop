"""Gestión de pedidos: verificación de pago, avance de estado y eliminación."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Producto, Pedido
from app.estados import ESTADOS_VENTA, FLUJO_PEDIDO
from app.utils import redirigir_seguro
from app.blueprints.public.pagos_utils import eliminar_comprobante
from . import admin_bp
from .decorators import admin_requerido


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
        return redirigir_seguro(request.referrer, url_for('admin.pedidos'))

    indice = FLUJO_PEDIDO.index(pedido.estado)
    if indice >= len(FLUJO_PEDIDO) - 1:
        flash(f'El pedido #{pedido.id} ya está entregado.', 'info')
    else:
        pedido.estado = FLUJO_PEDIDO[indice + 1]
        db.session.commit()
        flash(f'Pedido #{pedido.id} actualizado a "{pedido.estado}".', 'success')
    return redirigir_seguro(request.referrer, url_for('admin.pedidos'))


@admin_bp.route('/pedidos/<int:id>/confirmar-pago', methods=['POST'])
@login_required
@admin_requerido
def confirmar_pago(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.estado not in ('en_verificacion', 'rechazado'):
        flash('Este pedido no está a la espera de confirmación de pago.', 'warning')
        return redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))

    # Unidades necesarias por producto (una pieza puede estar en varias líneas)
    necesario = {}
    for d in pedido.detalles:
        if d.producto:
            necesario[d.producto] = necesario.get(d.producto, 0) + d.cantidad

    # Descuento atómico: UPDATE ... WHERE stock >= cantidad. Si alguna fila no se
    # actualiza (rowcount 0) es que no había stock, y se revierte todo.
    for producto, cantidad in necesario.items():
        filas = (Producto.query
                 .filter(Producto.id == producto.id, Producto.stock >= cantidad)
                 .update({Producto.stock: Producto.stock - cantidad},
                         synchronize_session=False))
        if filas == 0:
            db.session.rollback()
            flash(f'No se puede confirmar: sin stock suficiente de "{producto.nombre}".', 'danger')
            return redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))

    pedido.estado = 'pagado'
    db.session.commit()
    flash(f'Pago del pedido #{pedido.id} confirmado. Stock descontado.', 'success')
    return redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))


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
    return redirigir_seguro(request.referrer, url_for('admin.detalle_pedido', id=id))


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
    return redirigir_seguro(request.referrer, url_for('admin.pedidos'))


@admin_bp.route('/pedidos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_requerido
def eliminar_pedido(id):
    pedido = Pedido.query.get_or_404(id)

    # Reponer stock si el pedido lo había descontado (pagado/enviado/entregado)
    if pedido.estado in ESTADOS_VENTA:
        for d in pedido.detalles:
            if d.producto:
                d.producto.stock += d.cantidad

    # Borrar el comprobante del disco (si tiene)
    eliminar_comprobante(pedido.comprobante)

    numero = pedido.id
    db.session.delete(pedido)   # cascade elimina las líneas de detalle
    db.session.commit()
    flash(f'Pedido #{numero} eliminado del historial.', 'success')
    # Si el borrado vino del detalle del pedido, ese detalle ya no existe → ir a la lista
    return redirect(url_for('admin.pedidos'))
