"""Estados de un pedido y su presentación, en un solo lugar.

Centralizar esto evita que las cadenas ('pagado', 'en_verificacion', ...) y sus
etiquetas/colores queden repetidas y desincronizadas por rutas y plantillas.
"""

# Texto legible de cada estado (para mostrar al usuario)
ESTADO_ETIQUETAS = {
    'en_verificacion': 'En verificación',
    'pagado':          'Pagado',
    'enviado':         'Enviado',
    'entregado':       'Entregado',
    'rechazado':       'Rechazado',
    'cancelado':       'Cancelado',
}

# Color de badge de Bootstrap por estado
ESTADO_COLORES = {
    'en_verificacion': 'info',
    'pagado':          'primary',
    'enviado':         'primary',
    'entregado':       'success',
    'rechazado':       'warning',
    'cancelado':       'danger',
}

# Estados que cuentan como una venta concretada (para métricas de ingresos)
ESTADOS_VENTA = ('pagado', 'enviado', 'entregado')

# Estados a la espera de que el admin verifique el pago
ESTADOS_POR_VERIFICAR = ('en_verificacion',)

# Flujo ordenado de avance una vez confirmado el pago
FLUJO_PEDIDO = ['pagado', 'enviado', 'entregado']

# Pasos de la línea de tiempo que ve el cliente
LINEA_TIEMPO = ['en_verificacion', 'pagado', 'enviado', 'entregado']
