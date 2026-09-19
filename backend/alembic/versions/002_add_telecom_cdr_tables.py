"""Add Telecom and CDR Intelligence tables

Revision ID: 002_telecom_cdr
Revises: 
Create Date: 2026-09-19 17:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_telecom_cdr'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. phone_numbers
    op.create_table(
        'phone_numbers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('normalized_number', sa.String(length=32), nullable=False),
        sa.Column('country_code', sa.String(length=8), nullable=True),
        sa.Column('national_number', sa.String(length=20), nullable=True),
        sa.Column('number_type', sa.String(length=50), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_number')
    )
    op.create_index('ix_phone_numbers_normalized_number', 'phone_numbers', ['normalized_number'], unique=True)
    op.create_index('ix_phone_numbers_national_number', 'phone_numbers', ['national_number'])
    op.create_index('ix_phone_numbers_country_code', 'phone_numbers', ['country_code'])

    # 2. cdr_records
    op.create_table(
        'cdr_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('caller_phone_id', sa.String(length=36), nullable=False),
        sa.Column('callee_phone_id', sa.String(length=36), nullable=False),
        sa.Column('call_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('call_type', sa.String(length=50), nullable=False, server_default='VOICE'),
        sa.Column('location_or_tower', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('source_batch_id', sa.String(length=36), nullable=True),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('duration_seconds >= 0', name='chk_cdr_duration_positive'),
        sa.ForeignKeyConstraint(['caller_phone_id'], ['phone_numbers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['callee_phone_id'], ['phone_numbers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_batch_id'], ['import_batches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fingerprint')
    )
    op.create_index('ix_cdr_records_caller_phone_id', 'cdr_records', ['caller_phone_id'])
    op.create_index('ix_cdr_records_callee_phone_id', 'cdr_records', ['callee_phone_id'])
    op.create_index('ix_cdr_records_call_timestamp', 'cdr_records', ['call_timestamp'])
    op.create_index('ix_cdr_records_fingerprint', 'cdr_records', ['fingerprint'], unique=True)
    op.create_index('idx_cdr_caller_time', 'cdr_records', ['caller_phone_id', 'call_timestamp'])
    op.create_index('idx_cdr_callee_time', 'cdr_records', ['callee_phone_id', 'call_timestamp'])
    op.create_index('idx_cdr_call_pair', 'cdr_records', ['caller_phone_id', 'callee_phone_id'])

    # 3. crime_phone_associations
    op.create_table(
        'crime_phone_associations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crime_id', sa.String(length=36), nullable=False),
        sa.Column('phone_id', sa.String(length=36), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False, server_default='MENTIONED_IN_REPORT'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('confidence_type', sa.String(length=50), nullable=False, server_default='explicit'),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crime_id'], ['crimes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phone_id'], ['phone_numbers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crime_id', 'phone_id', 'relationship_type', name='uq_crime_phone_rel')
    )
    op.create_index('ix_crime_phone_associations_crime_id', 'crime_phone_associations', ['crime_id'])
    op.create_index('ix_crime_phone_associations_phone_id', 'crime_phone_associations', ['phone_id'])

    # 4. person_phone_associations
    op.create_table(
        'person_phone_associations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('person_name', sa.String(length=255), nullable=False),
        sa.Column('phone_id', sa.String(length=36), nullable=False),
        sa.Column('crime_id', sa.String(length=36), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='SUSPECT'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('confidence_type', sa.String(length=50), nullable=False, server_default='derived'),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crime_id'], ['crimes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['phone_id'], ['phone_numbers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('person_name', 'phone_id', name='uq_person_phone_rel')
    )
    op.create_index('ix_person_phone_associations_phone_id', 'person_phone_associations', ['phone_id'])
    op.create_index('ix_person_phone_associations_person_name', 'person_phone_associations', ['person_name'])


def downgrade():
    op.drop_table('person_phone_associations')
    op.drop_table('crime_phone_associations')
    op.drop_table('cdr_records')
    op.drop_table('phone_numbers')
