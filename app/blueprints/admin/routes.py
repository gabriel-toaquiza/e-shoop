"""Agrupa las rutas del panel de admin, separadas por área.

Cada módulo registra sus rutas en admin_bp al importarse. El __init__ del
blueprint hace `from . import routes`, por lo que basta con importarlos aquí.
"""
from . import rutas_dashboard    # noqa: F401
from . import rutas_categorias   # noqa: F401
from . import rutas_productos    # noqa: F401
from . import rutas_clientes     # noqa: F401
from . import rutas_pedidos      # noqa: F401
