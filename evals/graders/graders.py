from dataclasses import dataclass


@dataclass
class Grade:
    grader_name: str
    passed: bool
    score: float
    details: str | None = None


def grade_source_recall(expected_sources: list[str], citations: list[dict]) -> Grade:
    if not expected_sources:
        return Grade("source_recall", True, 1.0)
    cited_uris = [c.get("source_uri", "") for c in citations]
    matched = any(any(exp in uri for uri in cited_uris) for exp in expected_sources)
    return Grade("source_recall", matched, 1.0 if matched else 0.0)


def grade_keyword_coverage(expected_keywords: list[str], answer: str) -> Grade:
    if not expected_keywords:
        return Grade("keyword_coverage", True, 1.0)
    found = [kw for kw in expected_keywords if kw.lower() in answer.lower()]
    score = len(found) / len(expected_keywords)
    return Grade(
        "keyword_coverage",
        score >= 0.99,
        score,
        details=f"Found {len(found)}/{len(expected_keywords)} keywords",
    )


def grade_refusal(must_refuse: bool, status: str) -> Grade:
    if not must_refuse:
        return Grade("refusal", True, 1.0)
    passed = status == "refused"
    return Grade("refusal", passed, 1.0 if passed else 0.0, details=f"Status: {status}")


def grade_access_control(expect_denied: bool, status: str) -> Grade:
    if not expect_denied:
        return Grade("access_control", True, 1.0)
    passed = status == "denied"
    return Grade("access_control", passed, 1.0 if passed else 0.0, details=f"Status: {status}")

