from packages.harness.verifier import verify_answer_citations
from packages.infrastructure.llm import ModelAnswerSchema


def test_verifier_accepts_valid_citations():
    schema = ModelAnswerSchema(
        answer="Employees receive 24 days.",
        citations=["chunk-1"],
        insufficient_evidence=False,
    )
    verdict = verify_answer_citations(schema, ["chunk-1", "chunk-2"])
    assert verdict.is_valid is True
    assert verdict.status == "answered"


def test_verifier_rejects_hallucinated_citations():
    schema = ModelAnswerSchema(
        answer="Employees receive 24 days.",
        citations=["chunk-invented"],
        insufficient_evidence=False,
    )
    verdict = verify_answer_citations(schema, ["chunk-1"])
    assert verdict.is_valid is False
    assert "Hallucinated citations" in verdict.reason


def test_verifier_handles_refusal():
    schema = ModelAnswerSchema(
        answer="",
        citations=[],
        insufficient_evidence=True,
    )
    verdict = verify_answer_citations(schema, ["chunk-1"])
    assert verdict.is_valid is True
    assert verdict.status == "refused"

