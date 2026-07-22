"""Utilidades compartidas para redirecciones seguras (evitar open redirect)."""
from urllib.parse import urlparse
from flask import request, redirect


def es_url_local(destino):
    """True si 'destino' es una ruta del propio sitio (sin dominio ni esquema).

    Se usa para validar el parámetro ?next= del login.
    """
    if not destino:
        return False
    ref = urlparse(destino)
    return not ref.netloc and not ref.scheme


def _mismo_sitio(url):
    return bool(url) and urlparse(url).netloc == urlparse(request.host_url).netloc


def redirigir_seguro(url, fallback):
    """Redirige a 'url' solo si es del mismo sitio; si no, al 'fallback'."""
    return redirect(url if _mismo_sitio(url) else fallback)


def volver_atras(fallback):
    """Vuelve a la página anterior (referrer) si es del mismo sitio; si no, al fallback."""
    return redirigir_seguro(request.referrer, fallback)
