from dataclasses import dataclass
from packages.infrastructure.llm import ModelAnswerSchema


@dataclass
class VerificationVerdict:
    is_valid: bool
    status: str  # "answered", "refused", "failed"
    reason: str | None = None


def verify_answer_citations(
    model_output: ModelAnswerSchema | None,
    retrieved_chunk_ids: list[str],
) -> VerificationVerdict:
    if model_output is None:
        return VerificationVerdict(is_valid=False, status="failed", reason="Model output failed JSON parsing")

    if model_output.insufficient_evidence:
        return VerificationVerdict(is_valid=True, status="refused", reason="Model indicated insufficient context")

    citations = model_output.citations
    if not citations:
        return VerificationVerdict(is_valid=False, status="failed", reason="Answer provided without any citations")

    invalid_citations = [c for c in citations if c not in retrieved_chunk_ids]
    if invalid_citations:
        return VerificationVerdict(
            is_valid=False,
            status="failed",
            reason=f"Hallucinated citations detected: {invalid_citations}",
        )

    return VerificationVerdict(is_valid=True, status="answered")

