import json
from pathlib import Path

from app.services.rag import RetrievedChunk, evaluate_retrieval_quality


def test_retrieval_quality_fixture_cases_are_deterministic():
    cases = json.loads((Path(__file__).parent / "fixtures" / "ai_quality_cases.json").read_text(encoding="utf-8"))

    for case in cases:
        chunks = [RetrievedChunk(**chunk) for chunk in case["chunks"]]
        quality = evaluate_retrieval_quality(chunks)

        assert quality.confidence == case["expected_confidence"], case["name"]
        assert any(case["expected_note"] in note for note in quality.notes), case["name"]


def test_retrieval_quality_warns_when_only_one_high_similarity_chunk_is_found():
    quality = evaluate_retrieval_quality(
        [
            RetrievedChunk(
                chunk_id=1,
                document_title="network.pdf",
                course_title="Computer Networks",
                text="SNMP Trap uses UDP 162.",
                page_number=4,
                similarity=0.83,
                document_id="document-1",
            )
        ]
    )

    assert quality.confidence == "medium"
    assert any("引用资料较少" in note for note in quality.notes)
