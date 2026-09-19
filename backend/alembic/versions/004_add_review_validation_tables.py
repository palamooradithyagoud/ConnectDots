"""Add Investigator Validation and Review History tables

Revision ID: 004_review_validation
Revises: 003_person_network
Create Date: 2026-09-19 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_review_validation'
down_revision = '003_person_network'
branch_labels = None
depends_on = None


def upgrade():
    # 1. investigation_relationship_reviews
    op.create_table(
        'investigation_relationship_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('relationship_ref', sa.String(length=255), nullable=False),
        sa.Column('source_entity_type', sa.String(length=50), nullable=False),
        sa.Column('source_entity_id', sa.String(length=100), nullable=False),
        sa.Column('target_entity_type', sa.String(length=50), nullable=False),
        sa.Column('target_entity_id', sa.String(length=100), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('original_relationship_type', sa.String(length=50), nullable=False),
        sa.Column('final_relationship_type', sa.String(length=50), nullable=True),
        sa.Column('original_confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('provenance', sa.String(length=50), nullable=False, server_default='GRAPH_DERIVED'),
        sa.Column('discovery_method', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('reviewer_id', sa.String(length=100), nullable=True),
        sa.Column('reviewer_display_name', sa.String(length=255), nullable=True),
        sa.Column('investigator_note', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('evidence_snapshot', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investigation_relationship_reviews_relationship_ref', 'investigation_relationship_reviews', ['relationship_ref'], unique=True)
    op.create_index('ix_investigation_relationship_reviews_status', 'investigation_relationship_reviews', ['status'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_source_type', 'investigation_relationship_reviews', ['source_entity_type'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_source_id', 'investigation_relationship_reviews', ['source_entity_id'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_target_type', 'investigation_relationship_reviews', ['target_entity_type'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_target_id', 'investigation_relationship_reviews', ['target_entity_id'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_rel_type', 'investigation_relationship_reviews', ['relationship_type'], unique=False)
    op.create_index('ix_investigation_relationship_reviews_reviewer_id', 'investigation_relationship_reviews', ['reviewer_id'], unique=False)
    op.create_index('idx_review_source_target', 'investigation_relationship_reviews', ['source_entity_id', 'target_entity_id'], unique=False)
    op.create_index('idx_review_status_conf', 'investigation_relationship_reviews', ['status', 'original_confidence'], unique=False)

    # 2. investigation_review_histories
    op.create_table(
        'investigation_review_histories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('review_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=False),
        sa.Column('reviewer_id', sa.String(length=100), nullable=False),
        sa.Column('reviewer_display_name', sa.String(length=255), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('metadata_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['review_id'], ['investigation_relationship_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investigation_review_histories_review_id', 'investigation_review_histories', ['review_id'], unique=False)


def downgrade():
    op.drop_table('investigation_review_histories')
    op.drop_table('investigation_relationship_reviews')
