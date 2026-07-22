"""Manejadores de errores HTTP con el diseño del sitio."""
from flask import render_template
from app import db


def registrar_errores(app):
    @app.errorhandler(403)
    def prohibido(e):
        return render_template('errores/error.html', codigo=403,
                               titulo='Acceso denegado',
                               mensaje='No tienes permiso para ver esta página.'), 403

    @app.errorhandler(404)
    def no_encontrado(e):
        return render_template('errores/error.html', codigo=404,
                               titulo='Página no encontrada',
                               mensaje='La página que buscas no existe o fue movida.'), 404

    @app.errorhandler(413)
    def muy_grande(e):
        return render_template('errores/error.html', codigo=413,
                               titulo='Archivo demasiado grande',
                               mensaje='El archivo supera el tamaño máximo permitido (5 MB).'), 413

    @app.errorhandler(500)
    def error_servidor(e):
        db.session.rollback()   # evita dejar la sesión de BD en mal estado
        return render_template('errores/error.html', codigo=500,
                               titulo='Error del servidor',
                               mensaje='Ocurrió un problema. Inténtalo de nuevo en un momento.'), 500
