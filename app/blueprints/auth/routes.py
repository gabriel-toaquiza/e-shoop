from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import FormRegistro, FormLogin


# ── REGISTRO ──────────────────────────────────────────────────────
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # Si ya está logueado, redirigir al inicio
    if current_user.is_authenticated:
        return redirect(url_for('public.home'))

    form = FormRegistro()

    if form.validate_on_submit():          # POST + validaciones OK
        nuevo_usuario = Usuario(
            nombre = form.nombre.data,
            email  = form.email.data,
            rol    = 'cliente'
        )
        nuevo_usuario.set_password(form.password.data)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Cuenta creada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/registro.html', form=form)


# ── LOGIN ─────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.home'))

    form = FormLogin()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        if usuario and usuario.check_password(form.password.data):
            login_user(usuario, remember=form.remember.data)
            flash(f'Bienvenido, {usuario.nombre}!', 'success')

            # Redirigir a la página que intentaba visitar (si aplica)
            next_page = request.args.get('next')

            # Redirigir según rol
            if usuario.es_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                return redirect(next_page or url_for('public.home'))

        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html', form=form)


# ── LOGOUT ────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))