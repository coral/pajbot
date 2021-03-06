"""added by, edited by and last date used for commands

Revision ID: da98ae62a74c
Revises: 361a148f219
Create Date: 2016-02-06 16:19:12.263725

"""

# revision identifiers, used by Alembic.
revision = 'da98ae62a74c'
down_revision = '361a148f219'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tb_command_data', sa.Column('added_by', sa.Integer(), nullable=True))
    op.add_column('tb_command_data', sa.Column('edited_by', sa.Integer(), nullable=True))
    op.add_column('tb_command_data', sa.Column('last_date_used', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tb_command_data', 'last_date_used')
    op.drop_column('tb_command_data', 'edited_by')
    op.drop_column('tb_command_data', 'added_by')
    ### end Alembic commands ###
