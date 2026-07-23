"""Constantes y utilidades compartidas por las rutas del panel de admin."""
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# Umbral para considerar un producto con "bajo stock"
STOCK_MINIMO = 5

# Imágenes adicionales (galería) por producto
MAX_IMAGENES = 4
EXTENSIONES_IMG = {'jpg', 'jpeg', 'webp'}


def guardar_imagen(archivo, subcarpeta=''):
    """Guarda la imagen en static/img/<subcarpeta> con nombre único.

    Devuelve la ruta relativa a static/img (p. ej. 'productos/abc.jpg'),
    usando siempre '/' para que sirva tanto en la URL como en disco.
    """
    nombre_seguro = secure_filename(archivo.filename)
    extension     = os.path.splitext(nombre_seguro)[1].lower()
    nombre_unico  = f"{uuid.uuid4().hex}{extension}"
    carpeta       = os.path.join(current_app.root_path, 'static', 'img', subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre_unico))
    return f"{subcarpeta}/{nombre_unico}" if subcarpeta else nombre_unico


def eliminar_imagen(nombre):
    """Elimina un archivo de static/img si existe (para no dejar huérfanos)."""
    if not nombre:
        return
    ruta = os.path.join(current_app.root_path, 'static', 'img', *nombre.split('/'))
    if os.path.exists(ruta):
        os.remove(ruta)


def escapar_like(texto):
    """Escapa los comodines de LIKE para que el usuario no los use por error."""
    return texto.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def hay_imagen_nueva(campo):
    """True solo si el campo trae un archivo realmente subido (no un nombre previo)."""
    return isinstance(campo.data, FileStorage) and bool(campo.data.filename)


def extension_valida(nombre):
    """True si el nombre de archivo tiene una extensión de imagen permitida."""
    ext = os.path.splitext(nombre)[1].lower().lstrip('.')
    return ext in EXTENSIONES_IMG
