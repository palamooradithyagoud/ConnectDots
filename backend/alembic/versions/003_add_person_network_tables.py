"""Add Person Network and Key Individual Intelligence tables

Revision ID: 003_person_network
Revises: 002_telecom_cdr
Create Date: 2026-09-19 18:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_person_network'
down_revision = '002_telecom_cdr'
branch_labels = None
depends_on = None


def upgrade():
    # 0. person_phone_associations person_id column
    try:
        op.add_column('person_phone_associations', sa.Column('person_id', sa.String(length=64), nullable=True))
        op.create_index('ix_person_phone_associations_person_id', 'person_phone_associations', ['person_id'], unique=False)
    except Exception:
        pass

    # 1. persons
    op.create_table(
        'persons',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('identifiers', sa.JSON(), nullable=True),
        sa.Column('source_provenance', sa.String(length=100), server_default='FIR_NARRATIVE', nullable=True),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_persons_id', 'persons', ['id'], unique=False)
    op.create_index('ix_persons_canonical_name', 'persons', ['canonical_name'], unique=False)
    op.create_index('ix_persons_normalized_name', 'persons', ['normalized_name'], unique=False)

    # 2. crime_person_associations
    op.create_table(
        'crime_person_associations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crime_id', sa.String(length=36), nullable=False),
        sa.Column('person_id', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='PERSON_OF_INTEREST', nullable=True),
        sa.Column('relationship_type', sa.String(length=50), server_default='MENTIONED_IN', nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.9', nullable=True),
        sa.Column('extraction_confidence', sa.Float(), server_default='0.9', nullable=True),
        sa.Column('evidence_excerpt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crime_id'], ['crimes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crime_person_associations_crime_id', 'crime_person_associations', ['crime_id'], unique=False)
    op.create_index('ix_crime_person_associations_person_id', 'crime_person_associations', ['person_id'], unique=False)

    # 3. network_centrality_results
    op.create_table(
        'network_centrality_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('person_id', sa.String(length=64), nullable=False),
        sa.Column('scope_type', sa.String(length=50), nullable=False),
        sa.Column('scope_id', sa.String(length=64), nullable=True),
        sa.Column('degree_centrality', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('betweenness_centrality', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('pagerank', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('raw_degree', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('connected_crimes', sa.Integer(), server_default='0', nullable=True),
        sa.Column('connected_people', sa.Integer(), server_default='0', nullable=True),
        sa.Column('connected_phones', sa.Integer(), server_default='0', nullable=True),
        sa.Column('connected_vehicles', sa.Integer(), server_default='0', nullable=True),
        sa.Column('connected_organizations', sa.Integer(), server_default='0', nullable=True),
        sa.Column('metrics_metadata', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), server_default='v1.0-gds-nx', nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_network_centrality_results_person_id', 'network_centrality_results', ['person_id'], unique=False)
    op.create_index('ix_network_centrality_results_scope_type', 'network_centrality_results', ['scope_type'], unique=False)
    op.create_index('ix_network_centrality_results_scope_id', 'network_centrality_results', ['scope_id'], unique=False)


def downgrade():
    op.drop_index('ix_network_centrality_results_scope_id', table_name='network_centrality_results')
    op.drop_index('ix_network_centrality_results_scope_type', table_name='network_centrality_results')
    op.drop_index('ix_network_centrality_results_person_id', table_name='network_centrality_results')
    op.drop_table('network_centrality_results')

    op.drop_index('ix_crime_person_associations_person_id', table_name='crime_person_associations')
    op.drop_index('ix_crime_person_associations_crime_id', table_name='crime_person_associations')
    op.drop_table('crime_person_associations')

    op.drop_index('ix_persons_normalized_name', table_name='persons')
    op.drop_index('ix_persons_canonical_name', table_name='persons')
    op.drop_index('ix_persons_id', table_name='persons')
    op.drop_table('persons')
