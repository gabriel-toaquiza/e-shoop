# Reexporta los modelos para poder importarlos como `from app.models import ...`
# y, de paso, registra todas las tablas en SQLAlchemy.
from .usuario import Usuario              # noqa: F401
from .categoria import Categoria          # noqa: F401
from .producto import Producto            # noqa: F401
from .pedido import Pedido, DetallePedido  # noqa: F401
