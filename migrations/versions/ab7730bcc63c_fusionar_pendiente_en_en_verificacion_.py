"""Fusionar pendiente en en_verificacion, agregar estado rechazado

Revision ID: ab7730bcc63c
Revises: 9cecbc633281
Create Date: 2026-07-22 17:48:43.584435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab7730bcc63c'
down_revision = '9cecbc633281'
branch_labels = None
depends_on = None


ESTADOS_NUEVO = "('en_verificacion','pagado','enviado','entregado','cancelado','rechazado')"
ESTADOS_VIEJO = "('pendiente','en_verificacion','pagado','enviado','entregado','cancelado')"


def upgrade():
    # Los pedidos que estuvieran "pendiente" (sin comprobante) se cancelan,
    # porque en el flujo nuevo un pedido no existe sin pago.
    op.execute("UPDATE pedidos SET estado='cancelado' WHERE estado='pendiente'")
    op.execute(f"ALTER TABLE pedidos MODIFY estado ENUM{ESTADOS_NUEVO} DEFAULT 'en_verificacion'")


def downgrade():
    op.execute("UPDATE pedidos SET estado='pendiente' WHERE estado='rechazado'")
    op.execute(f"ALTER TABLE pedidos MODIFY estado ENUM{ESTADOS_VIEJO} DEFAULT 'pendiente'")
