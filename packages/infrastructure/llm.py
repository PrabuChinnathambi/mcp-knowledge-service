import json
import re
import time
from dataclasses import dataclass
import httpx
from pydantic import BaseModel, Field
from packages.core.config import get_settings
from packages.observability.logger import logger

settings = get_settings()


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


class OllamaClient:
    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/chat"
        self.model = settings.LLM_MODEL

    async def generate_grounded_answer(self, messages: list[dict]) -> LLMResponse:
        start_time = time.time()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(self.url, json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama call failed with status {resp.status_code}: {resp.text}")

                data = resp.json()
                raw_text = data.get("message", {}).get("content", "")
                latency_ms = int((time.time() - start_time) * 1000)

                # Clean markdown backticks if present
                clean_json_str = raw_text.strip()
                if clean_json_str.startswith("```"):
                    clean_json_str = re.sub(r"^```(?:json)?\s*", "", clean_json_str)
                    clean_json_str = re.sub(r"\s*```$", "", clean_json_str)

                parsed_schema = None
                try:
                    parsed_dict = json.loads(clean_json_str)
                    parsed_schema = ModelAnswerSchema(**parsed_dict)
                except Exception as parse_err:
                    logger.warn("Failed to parse JSON schema from model response", error=str(parse_err), raw=raw_text)

                return LLMResponse(
                    content=raw_text,
                    parsed=parsed_schema,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.error("LLM communication error", error=str(e))
                raise


llm_client = OllamaClient()

