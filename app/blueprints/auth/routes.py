from flask import render_template
from . import auth_bp

@auth_bp.route('/auth/login')
def login():
    return render_template('auth/login.html')

@auth_bp.route('/auth/registro')
def registro():
    return render_template('auth/registro.html')
