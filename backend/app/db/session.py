from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Configure connection engine
engine_kwargs = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

import sqlite3
from sqlalchemy import event

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

@event.listens_for(engine, "connect")
def add_sqlite_geo_functions(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function("ST_GeogFromText", 1, lambda val: val)
        dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda val: "{}")
        dbapi_conn.create_function("AsBinary", 1, lambda val: val)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
