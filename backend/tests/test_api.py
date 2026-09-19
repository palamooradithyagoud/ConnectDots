import io
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up an in-memory SQLite engine for API testing
from sqlalchemy.pool import StaticPool
import sqlite3
from sqlalchemy import event

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def add_sqlite_geo_functions(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function("ST_GeogFromText", 1, lambda val: val)
        dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda val: "{}")
        dbapi_conn.create_function("AsBinary", 1, lambda val: val)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geography

@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_, compiler, **kw):
    return "BLOB"

# Create all tables on the in-memory test engine
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


import pytest

@pytest.fixture(autouse=True)
def setup_api_db():
    app.dependency_overrides[get_db] = override_get_db
    yield

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "AI Crime Analysis System" in data["service"]


def test_dry_run_import_csv():
    csv_content = """record_id,crime_type,location,date,time,latitude,longitude,description,source
CR-TEST-101,THEFT,MG Road,2026-03-01,10:00:00,12.9716,77.5946,Valid theft,Police
CR-TEST-102,BURGLARY,Indiranagar,2026-03-02,02:00:00,999.0,77.6408,Invalid lat,Police
"""
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/crimes/import?dry_run=true", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert data["total_rows"] == 2
    assert data["valid_count"] == 1
    assert data["rejected_count"] == 1
    assert data["rejections"][0]["error_category"] == "INVALID_COORDINATES"


def test_commit_import_csv():
    import uuid
    uid = uuid.uuid4().hex[:6]
    rec_id = f"CR-COMMIT-{uid}"
    csv_content = f"""record_id,crime_type,location,date,time,latitude,longitude,description,source
{rec_id},THEFT,Brigade Road,2026-03-05,11:30:00,12.9733,77.6074,Committed record,Police
"""
    files = {"file": ("commit.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/crimes/import?dry_run=false", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is False
    assert data["valid_count"] == 1
    assert data["batch_id"] is not None

    # Verify query
    query_res = client.get(f"/api/v1/crimes?search={rec_id}")
    assert query_res.status_code == 200
    items = query_res.json()["items"]
    assert len(items) == 1
    assert items[0]["record_id"] == rec_id
    assert items[0]["category"] == "THEFT"
