"""Utilidades del pago por transferencia: validación de cédula y comprobantes."""
import os
import uuid
from flask import current_app


def cedula_valida(cedula):
    """Valida una cédula ecuatoriana (10 dígitos, algoritmo del dígito verificador).

    Comprueba: longitud, que sean dígitos, código de provincia (01-24 o 30) y
    el dígito verificador con el módulo 10.
    """
    cedula = (cedula or '').strip()
    if len(cedula) != 10 or not cedula.isdigit():
        return False

    provincia = int(cedula[:2])
    if not (1 <= provincia <= 24 or provincia == 30):
        return False

    # El tercer dígito debe ser menor a 6 para personas naturales
    if int(cedula[2]) >= 6:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for digito, coef in zip(cedula[:9], coeficientes):
        producto = int(digito) * coef
        if producto >= 10:
            producto -= 9
        suma += producto

    verificador = (10 - (suma % 10)) % 10
    return verificador == int(cedula[9])


def carpeta_comprobantes():
    """Ruta de la carpeta privada de comprobantes (fuera de /static)."""
    carpeta = os.path.join(current_app.instance_path, 'comprobantes')
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def extension_comprobante_valida(nombre):
    ext = os.path.splitext(nombre)[1].lower().lstrip('.')
    return ext in current_app.config['EXTENSIONES_COMPROBANTE']


def guardar_comprobante(archivo, pedido_id):
    """Guarda el comprobante en la carpeta privada y devuelve el nombre único."""
    extension    = os.path.splitext(archivo.filename)[1].lower()
    nombre_unico = f"pedido{pedido_id}_{uuid.uuid4().hex}{extension}"
    archivo.save(os.path.join(carpeta_comprobantes(), nombre_unico))
    return nombre_unico


def eliminar_comprobante(nombre):
    if not nombre:
        return
    ruta = os.path.join(carpeta_comprobantes(), nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
