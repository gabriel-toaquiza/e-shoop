"""Utilidades del carrito de compras (guardado en sesión).

Estructura nueva del carrito:
    {
        clave: {"producto_id": int, "cantidad": int, "especificaciones": str},
        ...
    }

- La clave es el id del producto (str) para productos normales.
- Para productos personalizados es "id-hash", así el mismo producto con
  especificaciones distintas ocupa líneas separadas, y con la misma
  especificación se agrupa en una sola línea.
"""
import hashlib

MAX_ESPECIFICACIONES = 300


def clave_item(producto_id, especificaciones=''):
    """Clave única de una línea del carrito."""
    espec = (especificaciones or '').strip()
    if not espec:
        return str(producto_id)
    firma = hashlib.md5(espec.encode('utf-8')).hexdigest()[:8]
    return f"{producto_id}-{firma}"


def normalizar_carrito(carrito):
    """Devuelve el carrito en el formato nuevo.

    Convierte el formato antiguo ({id: cantidad}) para que las sesiones que
    ya existían no se rompan con el código nuevo.
    """
    if not carrito:
        return {}
    nuevo = {}
    for clave, valor in carrito.items():
        if isinstance(valor, dict):
            nuevo[clave] = {
                'producto_id': int(valor.get('producto_id', clave.split('-')[0])),
                'cantidad': int(valor.get('cantidad', 1)),
                'especificaciones': valor.get('especificaciones', '') or ''
            }
        else:
            # Formato antiguo: la clave era el id y el valor la cantidad
            nuevo[str(clave)] = {
                'producto_id': int(clave),
                'cantidad': int(valor),
                'especificaciones': ''
            }
    return nuevo


def unidades_producto(carrito, producto_id, excepto_clave=None):
    """Suma de unidades de un mismo producto repartidas en todas sus líneas."""
    total = 0
    for clave, linea in carrito.items():
        if clave == excepto_clave:
            continue
        if int(linea['producto_id']) == int(producto_id):
            total += int(linea['cantidad'])
    return total


def cantidad_total(carrito):
    """Total de unidades en el carrito (soporta el formato antiguo)."""
    total = 0
    for valor in (carrito or {}).values():
        total += int(valor['cantidad']) if isinstance(valor, dict) else int(valor)
    return total
