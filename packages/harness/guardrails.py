import re

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(admin|developer|god)\s+mode", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(system|previous)\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|secret\s+key|instructions)", re.IGNORECASE),
]

PII_RULES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"(\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"), "[PHONE]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN_ID]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR_ID]"),
]


def detect_prompt_injection(text: str) -> str | None:
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def redact_pii(text: str) -> str:
    cleaned = text
    for pattern, replacement in PII_RULES:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned

