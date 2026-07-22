"""Pago por transferencia: datos de entrega, comprobante y estado en_verificacion

Revision ID: 9cecbc633281
Revises: 45ed1c9fdd0c
Create Date: 2026-07-22 17:30:00.530113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9cecbc633281'
down_revision = '45ed1c9fdd0c'
branch_labels = None
depends_on = None


ESTADOS_NUEVO = "('pendiente','en_verificacion','pagado','enviado','entregado','cancelado')"
ESTADOS_VIEJO = "('pendiente','pagado','enviado','entregado','cancelado')"


def upgrade():
    with op.batch_alter_table('pedidos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre_receptor', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('cedula', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('comprobante', sa.String(length=300), nullable=True))

    # Ampliar el ENUM de estado para incluir 'en_verificacion'
    op.execute(f"ALTER TABLE pedidos MODIFY estado ENUM{ESTADOS_NUEVO} DEFAULT 'pendiente'")


def downgrade():
    # Volver el ENUM al conjunto anterior (los pedidos en_verificacion pasan a pendiente)
    op.execute("UPDATE pedidos SET estado='pendiente' WHERE estado='en_verificacion'")
    op.execute(f"ALTER TABLE pedidos MODIFY estado ENUM{ESTADOS_VIEJO} DEFAULT 'pendiente'")

    with op.batch_alter_table('pedidos', schema=None) as batch_op:
        batch_op.drop_column('comprobante')
        batch_op.drop_column('cedula')
        batch_op.drop_column('nombre_receptor')
