# Grok Insights Chat

Real-time conversation insights playground built with **FastAPI** and **Tailwind-powered frontend**, using xAI's **Grok** as both a chat assistant and an analysis engine.

- **Chat Grok**: responds like a normal assistant, with short replies.
- **Analyst Grok**: analyzes the full conversation and returns structured JSON (sentiment, topics, action items, risks, summary, key quotes).
- **UI**: X/Twitter-style chat feed with a right-hand insights column, API activity viewer, history panel, and conversation list.

## Features

- FastAPI backend with:
  - `POST /v1/insights` : chat + analysis in a single call.
  - `GET  /v1/insights` : list stored analyses (used by the History panel).
- Two Grok roles:
  - Chat role: concise replies (2 sentences, ~50 words).
  - Analyst role: JSON insights over the entire conversation.
- Frontend (static HTML + Tailwind CSS):
  - User and Grok chat bubbles.
  - Latest insights shown in a right-hand panel.
  - Per-turn 'i' icon on Grok replies to view that turn's analysis.
  - 'My conversations' list to reopen past threads.
  - API activity panel showing request/response JSON.
  - History panel demonstrating `GET /v1/insights`.

## Requirements

- Python 3.10+
- A Grok API key from xAI

## Setup

From the project root (where `insights_backend/` lives):

```bash
python3 -m venv .venv
source .venv/bin/activate  # on macOS/Linux
# On Windows: .venv\\Scripts\\activate

pip install -r insights_backend/requirements.txt
```

Set your Grok API key in the environment:

```bash
export GROK_API_KEY="your_xai_grok_api_key_here"  # macOS/Linux
# On Windows (PowerShell):
# $env:GROK_API_KEY="your_xai_grok_api_key_here"
```

## Running the app

From the project root:

```bash
source .venv/bin/activate
python3 -m uvicorn insights_backend.main:app --reload
```

The app will be available at:

- http://127.0.0.1:8000/  (chat UI)

FastAPI will also serve the API under `/v1/...`.

## Using the chat UI

1. Open `http://127.0.0.1:8000/` in your browser.
2. Type a message in the 'Send a message...' field and hit **Send** or press **Enter**.
3. The flow per turn:
   - Your user message appears as a white bubble on the right.
   - Chat Grok responds as a dark bubble on the left.
   - Analyst Grok analyzes the full conversation and returns JSON insights.
   - The right-hand **Insights** panel updates with the latest analysis.

### Per-turn insights

- Next to each Grok reply, there is a small `i` button.
- Clicking it will:
  - Show the analysis for that turn in the right-hand **Insights** panel.
  - Replace any currently displayed analysis (only one analysis is shown at a time).

### Conversation history

- The left sidebar has a **My conversations** section:
  - Each conversation gets a title based on the first user message.
  - Clicking a conversation will:
    - Repopulate the middle chat column with that conversation's messages.
    - Load the last analysis for that conversation into the Insights panel.
- Use the `+` button next to **My conversations** to start a **New conversation**:
  - Clears the current chat and insights.
  - The next message will start a fresh conversation.

## API activity & History panels

Right-hand sidebar:

- **API activity**
  - Shows the method, URL, status, and latency of the last `POST /v1/insights` call.
  - Displays both the request body and response JSON.

- **History (GET /v1/insights)**
  - Has a **Refresh** button.
  - On click, calls:

    ```http
    GET /v1/insights?page=1&page_size=20
    ```

  - Displays the raw JSON response in a code-style box.
  - This is a simple visual way to confirm the GET endpoint and in-memory store are working.

## API summary

- `GET  /health`
  - Simple health check.

- `POST /v1/insights`
  - Body:

    ```json
    {
      "conversation_id": "optional-string",  // omit for new conversations
      "messages": [
        { "role": "user", "content": "hi" },
        { "role": "agent", "content": "..." }
      ],
      "metadata": { "any": "optional context" }
    }
    ```

  - Response: `AnalysisResponse` with fields like `insights`, `assistant_message`, `latency_ms`, etc.

- `GET  /v1/insights?page=1&page_size=20`
  - Returns a paginated list of `AnalysisResponse` items from the in-memory store.

## Notes & limitations

- **In-memory storage only**: all data is lost when the server restarts.
- **No secrets committed**: you must set `GROK_API_KEY` via environment variables yourself.

This repo is intended as a starting point for building production-grade conversation analytics on top of Grok. You can swap the in-memory store for a real database and extend the schemas as needed.
