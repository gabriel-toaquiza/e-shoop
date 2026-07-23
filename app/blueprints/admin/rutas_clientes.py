"""Gestión de cuentas de clientes."""
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Usuario
from . import admin_bp
from .decorators import admin_requerido


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
