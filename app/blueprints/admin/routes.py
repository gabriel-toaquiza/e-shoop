from flask import render_template
from . import admin_bp
from flask_login import login_required
from .decorators import admin_requerido

@admin_bp.route('/admin')
@login_required
@admin_requerido
def admin():
    return render_template('admin/index.html')

@admin_bp.route('/admin/productos')
def productos():
    return render_template('admin/productos.html')

@admin_bp.route('/admin/clientes')
def clientes():
    return render_template('admin/clientes.html')

@admin_bp.route('/admin/pedidos')
def pedidos():
    return render_template('admin/pedidos.html')