from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


RoleType = Literal["user", "agent", "system"]
StatusType = Literal["pending", "processing", "completed", "failed"]


class Message(BaseModel):
    role: RoleType
    content: str = Field(min_length=1)
    timestamp: Optional[str] = None


class InsightsRequest(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[Message] = Field(min_items=1)
    metadata: Optional[Dict[str, Any]] = None


class Sentiment(BaseModel):
    overall: Literal["positive", "neutral", "negative", "unknown"] = "unknown"
    score: float = Field(ge=0.0, le=1.0, default=0.5)


class Topic(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)


class ActionItem(BaseModel):
    description: str
    owner: Optional[Literal["agent", "customer", "system"]] = None
    due_by: Optional[str] = None


class RiskFlag(BaseModel):
    type: Literal["churn", "escalation", "compliance", "other"] = "other"
    severity: Literal["low", "medium", "high"] = "low"
    details: Optional[str] = None


class InsightsPayload(BaseModel):
    summary: str
    sentiment: Sentiment
    topics: List[Topic] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    risk_flags: List[RiskFlag] = Field(default_factory=list)


class AnalysisBase(BaseModel):
    id: str
    conversation_id: str
    status: StatusType


class AnalysisResponse(AnalysisBase):
    insights: Optional[InsightsPayload] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    assistant_message: Optional[str] = None


class AnalysisListResponse(BaseModel):
    items: List[AnalysisResponse]
    page: int
    page_size: int
    total: int

