import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Text,
    Integer,
    ForeignKey,
    JSON,
    Index,
    func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geography
from app.db.session import Base

# Allow SQLite to compile Geography columns as BLOB for local development & testing
@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_, compiler, **kw):
    return "BLOB"


def generate_uuid():
    return str(uuid.uuid4())


class ImportBatch(Base):
    """Tracks batch ingestion runs for auditability and error reporting."""
    __tablename__ = "import_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'CSV' or 'JSON'
    total_rows = Column(Integer, default=0, nullable=False)
    valid_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)  # PENDING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    crimes = relationship("Crime", back_populates="batch", cascade="all, delete-orphan")
    rejections = relationship("CrimeRejection", back_populates="batch", cascade="all, delete-orphan")


class Crime(Base):
    """Standardized crime incident record stored in PostgreSQL + PostGIS."""
    __tablename__ = "crimes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    record_id = Column(String(100), unique=True, index=True, nullable=False)
    crime_type = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # Standardized canonical category
    location_name = Column(String(255), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Coordinates & Spatial Column
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # PostGIS spatial column: WGS84 coordinates (SRID 4326)
    geom = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True)

    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="VALID", nullable=False, index=True)

    # Ingestion tracking
    import_batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    batch = relationship("ImportBatch", back_populates="crimes")

    # Future-proof metadata store (for Phase 2 NLP entities, Phase 3 ML clusters, embeddings)
    extra_metadata = Column(JSON, nullable=True)

    # Phase 2: NLP Analysis relationship
    nlp_analysis = relationship("NlpAnalysis", back_populates="crime", uselist=False, cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_crimes_coords", "latitude", "longitude"),
        Index("idx_crimes_category_date", "category", "occurred_at"),
        Index("idx_crimes_geom_gist", "geom", postgresql_using="gist"),
    )


class CrimeRejection(Base):
    """Maintains an auditable log of rejected, malformed, or duplicate records."""
    __tablename__ = "crime_rejections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=True)
    raw_data = Column(JSON, nullable=False)
    error_category = Column(String(100), nullable=False, index=True)  # INVALID_COORDS, DUPLICATE_ID, etc.
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batch = relationship("ImportBatch", back_populates="rejections")
