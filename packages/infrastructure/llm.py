import json
import re
import time
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

from packages.core.config import get_settings
from packages.observability.logger import logger

settings = get_settings()


AVAILABLE_LOCAL_MODELS: dict[str, dict] = {
    "qwen2.5:7b-instruct": {
        "id": "qwen2.5:7b-instruct",
        "name": "Qwen 2.5 7B Instruct",
        "family": "qwen",
        "description": "Enterprise-grade general instruction following and precise JSON synthesis.",
        "strengths": ["Enterprise Q&A", "Structured JSON adherence", "Multi-lingual accuracy"],
        "recommended_for": "Default enterprise knowledge retrieval and citation verification",
        "context_window": 32768,
    },
    "llama3.2:3b": {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 3B",
        "family": "llama",
        "description": "Lightweight, ultra-fast Meta model optimized for rapid edge inference and low memory.",
        "strengths": ["Ultra-fast inference", "Low latency", "Small memory footprint (2 GB)"],
        "recommended_for": "High-throughput queries and rapid real-time summarization",
        "context_window": 8192,
    },
    "deepseek-r1:1.5b": {
        "id": "deepseek-r1:1.5b",
        "name": "DeepSeek R1 1.5B (Distill)",
        "family": "deepseek",
        "description": "Reasoning model trained with reinforcement learning for multi-step logical deduction.",
        "strengths": ["Chain-of-thought reasoning (<think> trace)", "Complex deduction", "Edge deployment"],
        "recommended_for": "Complex queries requiring step-by-step logic and transparent reasoning",
        "context_window": 32768,
    },
}


class ModelAnswerSchema(BaseModel):
    answer: str = Field(description="Direct, factual answer synthesized strictly from context.")
    citations: list[str] = Field(default_factory=list, description="List of chunk UUIDs directly supporting the answer.")
    insufficient_evidence: bool = Field(default=False, description="Set to true if context lacks sufficient information.")


@dataclass
class LLMResponse:
    content: str
    parsed: ModelAnswerSchema | None
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    model_name: str = ""
    reasoning_trace: str | None = None


def extract_reasoning_and_json(raw_text: str) -> tuple[str | None, ModelAnswerSchema | None]:
    """
    Extracts optional <think>...</think> reasoning traces (e.g. from DeepSeek-R1)
    and robustly parses the remaining JSON body into ModelAnswerSchema.
    """
    reasoning_trace: str | None = None

    # 1. Extract <think> reasoning tags
    think_match = re.search(r"<think>(.*?)</think>", raw_text, re.DOTALL)
    if think_match:
        reasoning_trace = think_match.group(1).strip()
        # Remove think tags from the text to isolate the final answer / JSON
        cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    else:
        cleaned = raw_text.strip()

    # 2. Strip Markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # 3. Parse JSON into ModelAnswerSchema
    parsed_schema: ModelAnswerSchema | None = None
    try:
        parsed_dict = json.loads(cleaned)
        parsed_schema = ModelAnswerSchema(**parsed_dict)
    except Exception:
        # Fallback: search for outermost JSON object {...}
        json_obj_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_obj_match:
            try:
                candidate = json.loads(json_obj_match.group(1))
                parsed_schema = ModelAnswerSchema(**candidate)
            except Exception as e:
                logger.warn("JSON substring parse failed", error=str(e), candidate=json_obj_match.group(1)[:120])
        else:
            logger.warn("Could not parse JSON schema from model response", raw=cleaned[:200])

    return reasoning_trace, parsed_schema


class OllamaClient:
    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/chat"
        self.default_model = settings.LLM_MODEL

    async def list_available_models(self) -> list[dict]:
        """Queries local Ollama instance and returns metadata for supported models with installation status."""
        installed_names = set()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                if resp.status_code == 200:
                    installed_names = {m.get("name") for m in resp.json().get("models", [])}
        except Exception as e:
            logger.warn("Could not query Ollama tags", error=str(e))

        models_info = []
        for model_id, meta in AVAILABLE_LOCAL_MODELS.items():
            is_installed = any(model_id == name or model_id.split(":")[0] in name for name in installed_names)
            item = dict(meta)
            item["installed"] = is_installed
            item["is_default"] = (model_id == self.default_model)
            models_info.append(item)

        return models_info

    async def generate_grounded_answer(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> LLMResponse:
        start_time = time.time()
        target_model = model.strip() if model and model.strip() else self.default_model

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                resp = await client.post(self.url, json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama call for model '{target_model}' failed ({resp.status_code}): {resp.text}")

                data = resp.json()
                raw_text = data.get("message", {}).get("content", "")
                latency_ms = int((time.time() - start_time) * 1000)

                reasoning_trace, parsed_schema = extract_reasoning_and_json(raw_text)

                return LLMResponse(
                    content=raw_text,
                    parsed=parsed_schema,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    latency_ms=latency_ms,
                    model_name=target_model,
                    reasoning_trace=reasoning_trace,
                )
            except Exception as e:
                logger.error("LLM communication error", model=target_model, error=str(e))
                raise


llm_client = OllamaClient()
