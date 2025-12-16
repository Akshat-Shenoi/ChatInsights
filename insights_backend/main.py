from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .schemas import InsightsRequest, AnalysisResponse, AnalysisListResponse
from .storage import store
from .grok_client import analyze_conversation


app = FastAPI(title="Insights Platform", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.post("/v1/insights", response_model=AnalysisResponse)
async def create_insights(request: InsightsRequest) -> AnalysisResponse:
    conversation_id = request.conversation_id or f"conv-{datetime.utcnow().timestamp()}"
    pending = store.create_pending(conversation_id=conversation_id)

    start = datetime.utcnow()
    insights, assistant_message = await analyze_conversation(request.model_dump())
    latency_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

    completed = store.complete(
        analysis_id=pending.id,
        insights=insights,
        metadata=request.metadata,
        latency_ms=latency_ms,
        status="completed",
        error=None,
        assistant_message=assistant_message,
    )
    if completed is None:
        raise HTTPException(status_code=500, detail="Failed to persist analysis")
    return completed


@app.get("/v1/insights", response_model=AnalysisListResponse)
async def list_insights(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
) -> AnalysisListResponse:
    items = store.list()
    if status:
        items = [i for i in items if i.status == status]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    return AnalysisListResponse(
        items=page_items,
        page=page,
        page_size=page_size,
        total=total,
    )


app.mount("/", StaticFiles(directory="insights_backend/frontend", html=True), name="frontend")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse("insights_backend/frontend/index.html")

