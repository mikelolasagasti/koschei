"""Add user table

Revision ID: 42ad047fd7ff
Revises: 5cd786f3176
Create Date: 2014-10-03 12:14:11.091123

"""

# revision identifiers, used by Alembic.
revision = '42ad047fd7ff'
down_revision = '5cd786f3176'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('timezone', sa.String(), nullable=True),
    sa.Column('admin', sa.Boolean(), server_default='false', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    ### end Alembic commands ###
