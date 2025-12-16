import os
import json
from typing import Dict, Any

import httpx

from .schemas import InsightsPayload, Sentiment, Topic, ActionItem, RiskFlag


GROK_API_KEY = os.getenv("GROK_API_KEY")


SYSTEM_PROMPT = (
    "You are an advanced conversation insights engine. "
    "Your task is to analyze the text of a conversation and produce a structured JSON output. "
    "The analysis should include the following fields:\n\n"
    "1. sentiment: overall tone of the conversation (Positive, Neutral, Negative)\n"
    "2. sentimentScore: confidence as a float between 0 and 1\n"
    "3. topics: list of main topics discussed\n"
    "4. actionItems: list of actionable items mentioned in the conversation\n"
    "5. riskFlags: list of potential risks or issues, each with severity (Low, Medium, High) and reason\n"
    "6. summary: a brief 2-3 sentence summary of the conversation\n"
    "7. keyQuotes: up to 3 important quotes or phrases that illustrate the conversation’s main points\n\n"
    "Output:\n"
    "Return ONLY a valid JSON object with the exact fields above. "
    "Do not include any explanation or extra text. "
    "Ensure all lists are present, even if empty."
)


async def _call_grok(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY environment variable is not set")

    messages = payload.get("messages", [])
    joined = "\n".join(m.get("content", "") for m in messages)

    body = {
        "model": "grok-4-1-fast-reasoning",  # adjust to the actual model name if needed
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": joined},
        ],
        "temperature": 0.2,
    }

    url = "https://api.x.ai/v1/chat/completions"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    raw = json.loads(content)
    return raw


async def _chat_reply(payload: Dict[str, Any]) -> str:
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY environment variable is not set")

    raw_messages = payload.get("messages", [])
    chat_messages = []
    for m in raw_messages:
        role = m.get("role", "user")
        if role == "agent":
            mapped_role = "assistant"
        elif role == "system":
            mapped_role = "system"
        else:
            mapped_role = "user"
        chat_messages.append({"role": mapped_role, "content": m.get("content", "")})

    system_chat_prompt = (
        "You are a concise, helpful support assistant. "
        "Respond naturally as a chat assistant, but keep your reply under about 50 words "
        "(no more than 2-3 short sentences)."
    )

    body = {
        "model": "grok-4-1-fast-reasoning",
        "messages": [
            {"role": "system", "content": system_chat_prompt},
            *chat_messages,
        ],
        "temperature": 0.4,
    }

    url = "https://api.x.ai/v1/chat/completions"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]


def _map_grok_to_insights(raw: Dict[str, Any], fallback_joined: str) -> InsightsPayload:
    messages_summary = fallback_joined[:200] + ("..." if len(fallback_joined) > 200 else "")

    sentiment_label = str(raw.get("sentiment", "Neutral")).lower()
    if sentiment_label not in {"positive", "neutral", "negative"}:
        sentiment_label = "neutral"
    score = float(raw.get("sentimentScore", 0.5))
    score = max(0.0, min(1.0, score))
    sentiment = Sentiment(overall=sentiment_label, score=score)

    topics_raw = raw.get("topics") or []
    topics = [
        Topic(label=str(t), confidence=1.0)
        for t in topics_raw
    ]

    actions_raw = raw.get("actionItems") or []
    action_items = [
        ActionItem(description=str(a))
        for a in actions_raw
        if str(a).strip()
    ]

    risks_raw = raw.get("riskFlags") or []
    risk_flags = []
    for r in risks_raw:
        if isinstance(r, dict):
            severity_raw = str(r.get("severity", "Low")).lower()
            if severity_raw not in {"low", "medium", "high"}:
                severity_raw = "low"
            reason = r.get("reason", None)
        else:
            severity_raw = "low"
            reason = str(r)
        risk_flags.append(
            RiskFlag(
                type="other",
                severity=severity_raw,  # type: ignore[arg-type]
                details=reason,
            )
        )

    summary = raw.get("summary") or messages_summary or "No content provided"

    return InsightsPayload(
        summary=summary,
        sentiment=sentiment,
        topics=topics,
        action_items=action_items,
        risk_flags=risk_flags,
    )


async def analyze_conversation(payload: Dict[str, Any]) -> tuple[InsightsPayload, str | None]:
    messages = payload.get("messages", [])
    joined = " \n".join(m.get("content", "") for m in messages)

    assistant_message: str | None = None

    assistant_message = await _chat_reply(payload)
    if assistant_message:
        messages.append({"role": "agent", "content": assistant_message})
        payload = {"messages": messages}

    raw = await _call_grok(payload)
    insights = _map_grok_to_insights(
        raw,
        joined + (" \n" + assistant_message if assistant_message else ""),
    )
    return insights, assistant_message


