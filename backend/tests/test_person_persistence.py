"""
Phase 5 Person Network: Person Persistence and Identity Resolution Tests
Tests PostgreSQL persistence for Person, CrimePersonAssociation, and conservative deduplication.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import Crime
from app.models.person import Person, CrimePersonAssociation, NetworkCentralityResult
from app.models.telecom import PhoneNumber, PersonPhoneAssociation
from app.services.person_resolution_service import PersonResolutionService


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite engine for test isolation with Geo functions registered."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def add_geo_functions(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_person_model_persistence(test_db):
    """Verifies that Person and CrimePersonAssociation records persist correctly in relational DB."""
    crime = Crime(
        id="crime-p1",
        record_id="FIR-2026-001",
        crime_type="Extortion",
        category="EXTORTION",
        location_name="Connaught Place",
        occurred_at=datetime.now(timezone.utc),
        latitude=28.6328,
        longitude=77.2197,
        description="Victim threatened by Vikram Singh demanding protection money.",
        source="fir_cad",
        status="VALID"
    )
    test_db.add(crime)
    test_db.commit()

    person = Person(
        id="person:vikram_singh",
        canonical_name="Vikram Singh",
        normalized_name="vikram singh",
        aliases=["Vicky", "Vikram Bhai"],
        identifiers={"aadhaar_hash": "a1b2c3d4", "voter_id": "VTR987654"},
        metadata_json={"notes": "Known extortion operative in Central Delhi"}
    )
    test_db.add(person)
    test_db.commit()

    assoc = CrimePersonAssociation(
        crime_id=crime.id,
        person_id=person.id,
        role="ACCUSED",
        evidence_excerpt="Victim threatened by Vikram Singh demanding protection money.",
        confidence=0.95
    )
    test_db.add(assoc)
    test_db.commit()

    # Query back
    saved_person = test_db.query(Person).filter(Person.id == "person:vikram_singh").first()
    assert saved_person is not None
    assert saved_person.canonical_name == "Vikram Singh"
    assert "Vicky" in saved_person.aliases
    assert saved_person.identifiers["voter_id"] == "VTR987654"

    saved_assoc = test_db.query(CrimePersonAssociation).filter(
        CrimePersonAssociation.crime_id == crime.id,
        CrimePersonAssociation.person_id == person.id
    ).first()
    assert saved_assoc is not None
    assert saved_assoc.role == "ACCUSED"
    assert saved_assoc.confidence == 0.95


def test_person_resolution_name_normalization():
    """Verifies Indian honorific removal, whitespace normalization, and title-casing."""
    assert PersonResolutionService.normalize_name("Shri Vikram Singh") == "Vikram Singh"
    assert PersonResolutionService.normalize_name("Smt. Sunita Sharma") == "Sunita Sharma"
    assert PersonResolutionService.normalize_name("Mohd. Aslam Khan") == "Aslam Khan"
    assert PersonResolutionService.normalize_name("Dr. Rajesh Verma") == "Rajesh Verma"
    assert PersonResolutionService.normalize_name("Late Harish Rao") == "Harish Rao"
    assert PersonResolutionService.normalize_name("  mr.   amit   patel  ") == "Amit Patel"
    assert PersonResolutionService.normalize_name("S/O RAMESH KUMAR") == "Ramesh Kumar"


def test_conservative_identity_deduplication(test_db):
    """
    Verifies Conservative Identity Resolution:
    - Same canonical name resolves to the same Person entity.
    - Dissimilar names (e.g. 'Raj Kumar' vs 'Ramesh Kumar') are NEVER falsely merged.
    """
    p1 = PersonResolutionService.resolve_or_create_person(
        db=test_db,
        raw_name="Shri Vikram Singh",
        aliases=["Vicky"]
    )
    test_db.commit()

    # 1. Exact match with honorific variation -> must resolve to existing person
    p2 = PersonResolutionService.resolve_or_create_person(
        db=test_db,
        raw_name="Mr. Vikram Singh",
        aliases=["Vikram"]
    )
    test_db.commit()
    assert p1.id == p2.id, "Expected same Person entity for honorific variations of Vikram Singh"
    assert "Vikram" in p1.aliases or "Vicky" in p1.aliases

    # 2. Conservative guard: Similar common names MUST NOT be merged
    p_raj = PersonResolutionService.resolve_or_create_person(
        db=test_db,
        raw_name="Raj Kumar"
    )
    p_ramesh = PersonResolutionService.resolve_or_create_person(
        db=test_db,
        raw_name="Ramesh Kumar"
    )
    test_db.commit()
    assert p_raj.id != p_ramesh.id, "Raj Kumar and Ramesh Kumar must remain distinct entities"
    assert p_raj.canonical_name == "Raj Kumar"
    assert p_ramesh.canonical_name == "Ramesh Kumar"


def test_person_phone_association(test_db):
    """Verifies that Person entities can be linked to PhoneNumber entities via foreign keys."""
    person = PersonResolutionService.resolve_or_create_person(
        db=test_db,
        raw_name="Sunil Sharma"
    )
    phone = PhoneNumber(
        id="phone:+919876543210",
        raw_number="9876543210",
        normalized_number="+919876543210",
        country_code="+91",
        carrier="Airtel",
        circle="Delhi",
        line_type="MOBILE",
        is_valid=True
    )
    test_db.add(phone)
    test_db.commit()

    ppa = PersonPhoneAssociation(
        phone_id=phone.id,
        person_name=person.canonical_name,
        person_id=person.id,
        source="sim_registration",
        confidence=0.9
    )
    test_db.add(ppa)
    test_db.commit()

    saved_ppa = test_db.query(PersonPhoneAssociation).filter(
        PersonPhoneAssociation.phone_id == phone.id
    ).first()
    assert saved_ppa is not None
    assert saved_ppa.person_id == person.id
    assert saved_ppa.person_name == "Sunil Sharma"


def test_associate_crime_person_service(test_db):
    """Verifies PersonResolutionService.associate_crime_person associates grounded FIR excerpts."""
    crime = Crime(
        id="c-assoc-1",
        record_id="FIR-2026-999",
        crime_type="Cyber Fraud",
        category="CYBERCRIME",
        location_name="Noida Cyber Park",
        occurred_at=datetime.now(timezone.utc),
        latitude=28.5355,
        longitude=77.3910,
        description="Cyber fraud ring coordinated by Amit Patel via spoofed banking portals.",
        source="cyber_cell",
        status="VALID"
    )
    test_db.add(crime)
    test_db.commit()

    assoc = PersonResolutionService.associate_crime_person(
        db=test_db,
        crime_id=crime.id,
        raw_name="Amit Patel",
        role="SUSPECT",
        excerpt="Cyber fraud ring coordinated by Amit Patel via spoofed banking portals.",
        confidence=0.9
    )
    test_db.commit()

    assert assoc is not None
    assert assoc.crime_id == crime.id
    assert assoc.person_id == "person:amit_patel"
    assert assoc.role == "SUSPECT"
    assert "Amit Patel" in assoc.evidence_excerpt
