"""Add user.packages_queried

Revision ID: 2c84d6f01e8c
Revises: 4552a3543a68
Create Date: 2015-04-27 14:24:59.442465

"""

# revision identifiers, used by Alembic.
revision = '2c84d6f01e8c'
down_revision = '4552a3543a68'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('packages_retrieved', sa.Boolean(), server_default='false', nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'packages_retrieved')
    ### end Alembic commands ###