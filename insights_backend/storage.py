from typing import Dict, List
from datetime import datetime
from uuid import uuid4

from .schemas import AnalysisResponse, InsightsPayload, StatusType


class InMemoryStore:
    def __init__(self) -> None:
        self._items: Dict[str, AnalysisResponse] = {}

    def create_pending(self, conversation_id: str) -> AnalysisResponse:
        now = datetime.utcnow().isoformat() + "Z"
        analysis = AnalysisResponse(
            id=str(uuid4()),
            conversation_id=conversation_id,
            status="pending",
            insights=None,
            metadata=None,
            created_at=now,
            updated_at=now,
            latency_ms=None,
            error=None,
            assistant_message=None,
        )
        self._items[analysis.id] = analysis
        return analysis

    def complete(
        self,
        analysis_id: str,
        insights: InsightsPayload,
        metadata=None,
        latency_ms: int | None = None,
        status: StatusType = "completed",
        error: str | None = None,
        assistant_message: str | None = None,
    ) -> AnalysisResponse | None:
        existing = self._items.get(analysis_id)
        if existing is None:
            return None
        updated = existing.model_copy(update={
            "status": status,
            "insights": insights,
            "metadata": metadata,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "latency_ms": latency_ms,
            "error": error,
            "assistant_message": assistant_message,
        })
        self._items[analysis_id] = updated
        return updated

    def get(self, analysis_id: str) -> AnalysisResponse | None:
        return self._items.get(analysis_id)

    def list(self) -> List[AnalysisResponse]:
        return list(self._items.values())


store = InMemoryStore()

