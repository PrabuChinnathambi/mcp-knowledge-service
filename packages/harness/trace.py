import time
import uuid
from packages.domain.models import ExecutionTrace
from packages.infrastructure.database import AsyncSessionLocal
from packages.observability.logger import logger


class TraceRecorder:
    def __init__(self, user_id: str, workspace_id: str, query: str):
        self.trace_id = f"tr-{uuid.uuid4().hex[:12]}"
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.query = query
        self.start_time = time.time()
        self.steps: list[dict] = []

    def record_step(self, step_name: str, payload: dict | None = None):
        self.steps.append(
            {
                "step": step_name,
                "elapsed_ms": int((time.time() - self.start_time) * 1000),
                "data": payload or {},
            }
        )

    async def persist(self, status: str, output: dict, top_score: float | None = None):
        latency_ms = int((time.time() - self.start_time) * 1000)
        trace_record = ExecutionTrace(
            trace_id=self.trace_id,
            user_id=self.user_id,
            workspace_id=self.workspace_id,
            query_text=self.query,
            status=status,
            latency_ms=latency_ms,
            data={
                "steps": self.steps,
                "output": output,
                "top_score": top_score,
            },
        )
        try:
            async with AsyncSessionLocal() as session:
                session.add(trace_record)
                await session.commit()
        except Exception as e:
            logger.warn("Could not save execution trace to database", error=str(e), trace_id=self.trace_id)

