from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

HARNESS_POLICY = {
    "max_context_chunks": 5,
    "retrieval_timeout_seconds": 15.0,
    "llm_timeout_seconds": 90.0,
    "max_retries": 2,
    "min_relevance": 0.30,
}

# Retry policy for idempotent read-only operations
harness_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=1, max=4),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True,
)

