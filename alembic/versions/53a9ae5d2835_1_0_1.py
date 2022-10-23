"""1.0.1

Revision ID: 53a9ae5d2835
Revises: 6940fa00ebb9
Create Date: 2022-10-23 14:00:07.495863

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53a9ae5d2835'
down_revision = '6940fa00ebb9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('CONFIG_SYNC_PATHS',
                    sa.Column('ID', sa.Integer(), nullable=False),
                    sa.Column('SOURCE', sa.Text(), nullable=True),
                    sa.Column('DEST', sa.Text(), nullable=True),
                    sa.Column('UNKNOWN', sa.Text(), nullable=True),
                    sa.Column('MODE', sa.Text(), nullable=True),
                    sa.Column('RENAME', sa.Integer(), nullable=True),
                    sa.Column('ENABLED', sa.Integer(), nullable=True),
                    sa.Column('NOTE', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('ID'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('CONFIG_SYNC_PATHS')
    # ### end Alembic commands ###
