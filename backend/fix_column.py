from app.db.session import SessionLocal
from sqlalchemy import text

s = SessionLocal()
try:
    s.execute(text("ALTER TABLE crime_person_associations ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION DEFAULT 0.9;"))
    s.execute(text("UPDATE crime_person_associations SET confidence = extraction_confidence WHERE confidence IS NULL AND extraction_confidence IS NOT NULL;"))
    s.commit()
    print("SUCCESS: column confidence ensured on crime_person_associations.")
except Exception as e:
    s.rollback()
    print("ERROR:", e)
finally:
    s.close()
