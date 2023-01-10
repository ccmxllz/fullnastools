"""1.0.9

Revision ID: cc7232dfe2b5
Revises: acbada719942
Create Date: 2023-01-10 09:14:56.448498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc7232dfe2b5'
down_revision = 'acbada719942'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        with op.batch_alter_table("SITE_USER_INFO_STATS") as batch_op:
            batch_op.drop_column('FAVICON')
    except Exception as e:
        print(e)
    try:
        with op.batch_alter_table("DOUBAN_MEDIAS") as batch_op:
            batch_op.add_column(sa.Column('ADD_TIME', sa.Text, nullable=True))
    except Exception as e:
        print(str(e))
    try:
        with op.batch_alter_table("SITE_BRUSH_TASK") as batch_op:
            batch_op.add_column(sa.Column('SENDMESSAGE', sa.Text, nullable=True))
            batch_op.add_column(sa.Column('FORCEUPLOAD', sa.Text, nullable=True))
    except Exception as e:
        print(str(e))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        with op.batch_alter_table("SITE_USER_INFO_STATS") as batch_op:
            batch_op.add_column(sa.Column('FAVICON', sa.Text, nullable=True))
    except Exception as e:
        print(str(e))
    try:
        with op.batch_alter_table("DOUBAN_MEDIAS") as batch_op:
            batch_op.drop_column('ADD_TIME')
    except Exception as e:
        print(e)
    try:
        with op.batch_alter_table("DOUBAN_MEDIAS") as batch_op:
            batch_op.drop_column('ADD_TIME')
    except Exception as e:
        print(e)
    try:
        with op.batch_alter_table("SITE_BRUSH_TASK") as batch_op:
            batch_op.drop_column('FORCEUPLOAD')
            batch_op.drop_column('SENDMESSAGE')
    except Exception as e:
        print(e)
    # ### end Alembic commands ###
