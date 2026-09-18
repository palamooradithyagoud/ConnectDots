import pytest
from app.services.text_preprocessor import TextPreprocessor
from app.services.entity_extraction_service import EntityExtractionService
from app.services.classification_service import ClassificationService
from app.services.modus_operandi_service import ModusOperandiService
from app.services.graph_ready_service import GraphReadyService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


def test_text_preprocessor_clean():
    # Null and empty
    assert TextPreprocessor.clean(None) == ""
    assert TextPreprocessor.clean("") == ""
    assert TextPreprocessor.clean("   ") == ""

    # Whitespace and repeated spaces
    raw = "  Robbery   at    store  \n\n with   knife .  "
    cleaned = TextPreprocessor.clean(raw)
    assert cleaned == "Robbery at store with knife."

    # Unicode normalization
    unicode_text = "Théft of laptöp"
    cleaned_unicode = TextPreprocessor.clean(unicode_text)
    assert "Theft" in cleaned_unicode or "Théft" in cleaned_unicode

    # Boilerplate stripping
    boilerplate = "Incident Report: Suspect stole motorcycle. FIR registered."
    cleaned_bp = TextPreprocessor.clean(boilerplate)
    assert "Incident Report:" not in cleaned_bp
    assert "FIR registered" not in cleaned_bp


def test_entity_extraction_prompt_example():
    text = "Two suspects robbed a jewellery store near Banjara Hills at 10 PM using a knife and escaped in a black motorcycle."
    entities = EntityExtractionService.extract_entities(text)

    # Required entity categories
    assert "Two suspects" in entities["persons"]
    assert any("Banjara Hills" in loc for loc in entities["locations"])
    assert "knife" in entities["weapons"]
    assert "black motorcycle" in entities["vehicles"]
    assert any("10 PM" in t for t in entities["times"])

    # Non-hallucination check: Guns/explosives/money should not be present
    assert len(entities["money"]) == 0
    assert "gun" not in entities["weapons"]


def test_modus_operandi_extraction():
    text = "Two suspects robbed a jewellery store near Banjara Hills at 10 PM using a knife and escaped in a black motorcycle."
    mos = ModusOperandiService.extract_modus_operandi(text)
    patterns = [m["pattern"] for m in mos]

    assert "Armed robbery" in patterns
    assert "Escape using vehicle" in patterns
    assert all(m["certainty"] == "explicitly_stated" for m in mos)


def test_modus_operandi_forced_entry():
    text = "Overnight break-in where lock was broken and forced entry was detected."
    mos = ModusOperandiService.extract_modus_operandi(text)
    patterns = [m["pattern"] for m in mos]

    assert "Forced entry" in patterns
    assert "Overnight / Night burglary" in patterns


def test_classification_service_high_confidence():
    text = "Armed robbery at convenience store cash register with knife threat"
    result = ClassificationService.classify(text, original_category="ROBBERY")

    assert result["predicted_category"] == "ROBBERY"
    assert result["confidence"] > 0.60
    assert result["needs_review"] is False


def test_classification_service_low_confidence_flagged():
    text = "Something unusual occurred around the block."
    result = ClassificationService.classify(text, original_category="THEFT")

    # Low-signal description should trigger needs_review
    assert result["needs_review"] is True


def test_embedding_generation_shape():
    text = "Theft of mobile phone from electronics store"
    emb = EmbeddingService.generate_embedding(text)

    assert isinstance(emb, list)
    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)

    # Empty text returns zero vector
    empty_emb = EmbeddingService.generate_embedding("")
    assert len(empty_emb) == 384
    assert sum(empty_emb) == 0.0


def test_graph_ready_payload_generation():
    entities = {
        "locations": ["Banjara Hills"],
        "weapons": ["knife"],
        "vehicles": ["motorcycle"],
        "persons": ["Two suspects"],
        "organizations": ["Jewellery Shop"],
        "dates": [],
        "times": [],
        "money": []
    }
    mos = [{"pattern": "Armed robbery", "certainty": "explicitly_stated"}]

    payload = GraphReadyService.generate_graph_payload(
        crime_id="test-uuid-123",
        record_id="CR-TEST-001",
        category="ROBBERY",
        occurred_at="2026-03-01T10:00:00Z",
        entities=entities,
        modus_operandi=mos
    )

    assert payload["crime_id"] == "test-uuid-123"
    assert payload["record_id"] == "CR-TEST-001"
    assert len(payload["nodes"]) >= 5
    assert len(payload["relationships"]) >= 4

    relations = [r["relation"] for r in payload["relationships"]]
    assert "OCCURRED_AT" in relations
    assert "USED_WEAPON" in relations
    assert "USED_VEHICLE" in relations
    assert "EXHIBITS_MO" in relations


def test_qdrant_service_in_memory_upsert_and_search():
    client = QdrantService.get_client()
    assert client is not None

    test_vector = [0.1] * 384
    point_id = QdrantService.upsert_crime_vector(
        crime_id="test-crime-999",
        vector=test_vector,
        payload={
            "record_id": "CR-TEST-999",
            "category": "ROBBERY",
            "location": "Banjara Hills",
            "occurred_at": "2026-03-01T10:00:00Z",
            "source": "Test Station"
        }
    )
    assert point_id is not None

    # Search with exact vector
    matches = QdrantService.search_similar_crimes(
        query_vector=test_vector,
        limit=5,
        score_threshold=0.50
    )
    assert len(matches) > 0
    assert matches[0]["payload"]["record_id"] == "CR-TEST-999"
