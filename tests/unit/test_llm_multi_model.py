from unittest.mock import AsyncMock, patch

import pytest

from packages.infrastructure.llm import (
    AVAILABLE_LOCAL_MODELS,
    LLMResponse,
    OllamaClient,
    extract_reasoning_and_json,
)


def test_available_models_catalog():
    """Ensure the 3 required offline models exist in catalog with metadata."""
    expected_models = ["qwen2.5:7b-instruct", "llama3.2:3b", "deepseek-r1:1.5b"]
    for model_id in expected_models:
        assert model_id in AVAILABLE_LOCAL_MODELS
        meta = AVAILABLE_LOCAL_MODELS[model_id]
        assert "name" in meta
        assert "family" in meta
        assert "description" in meta
        assert "recommended_for" in meta
        assert meta["context_window"] > 0


def test_extract_standard_json():
    raw = '{"answer": "Employees receive 20 days off.", "citations": ["chunk-123"], "insufficient_evidence": false}'
    reasoning, parsed = extract_reasoning_and_json(raw)
    assert reasoning is None
    assert parsed is not None
    assert parsed.answer == "Employees receive 20 days off."
    assert parsed.citations == ["chunk-123"]
    assert parsed.insufficient_evidence is False


def test_extract_deepseek_r1_reasoning():
    """Verify DeepSeek-R1 <think>...</think> tags are separated from the final JSON payload."""
    raw = (
        "<think>\n"
        "The user is asking about vacation days.\n"
        "Let me check chunk-abc: It states employees receive 20 days of paid vacation.\n"
        "Therefore the answer is 20 days, cited by chunk-abc.\n"
        "</think>\n"
        '{"answer": "20 days of paid annual vacation.", "citations": ["chunk-abc"], "insufficient_evidence": false}'
    )
    reasoning, parsed = extract_reasoning_and_json(raw)
    assert reasoning is not None
    assert "The user is asking about vacation days." in reasoning
    assert parsed is not None
    assert parsed.answer == "20 days of paid annual vacation."
    assert parsed.citations == ["chunk-abc"]


def test_extract_markdown_fenced_json():
    raw = (
        "```json\n"
        '{\n  "answer": "Coverage begins on day one.",\n  "citations": ["chunk-999"],\n  "insufficient_evidence": false\n}\n'
        "```"
    )
    reasoning, parsed = extract_reasoning_and_json(raw)
    assert reasoning is None
    assert parsed is not None
    assert parsed.answer == "Coverage begins on day one."
    assert parsed.citations == ["chunk-999"]


def test_extract_embedded_json():
    raw = (
        "Here is the answer you requested based on the policy:\n"
        '{"answer": "Remote work requires manager approval.", "citations": ["chunk-555"], "insufficient_evidence": false}\n'
        "Hope this helps!"
    )
    _reasoning, parsed = extract_reasoning_and_json(raw)
    assert parsed is not None
    assert parsed.answer == "Remote work requires manager approval."
    assert parsed.citations == ["chunk-555"]


@pytest.mark.asyncio
async def test_ollama_client_model_selection():
    client = OllamaClient()

    fake_response = {
        "message": {"content": '{"answer": "Test answer", "citations": []}'},
        "prompt_eval_count": 50,
        "eval_count": 25,
    }

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json = lambda: fake_response

    with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
        res = await client.generate_grounded_answer(
            messages=[{"role": "user", "content": "hi"}],
            model="llama3.2:3b",
        )

        assert isinstance(res, LLMResponse)
        assert res.model_name == "llama3.2:3b"
        assert res.parsed.answer == "Test answer"

        # Verify target model in JSON payload
        mock_post.assert_called_once()
        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload["model"] == "llama3.2:3b"
