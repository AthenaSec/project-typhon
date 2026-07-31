"""Mock target chatbot for the red-team demo.

Deliberately weak system prompt (see system_prompt.txt) — this is the thing
that gets attacked. Swap SYSTEM_PROMPT_PATH / TARGET_MODEL / LLM_PROVIDER via
env vars to point this at a different persona, model, or provider without
touching code.

Launch it using uv run uvicorn target_agent.main:app --port 8000 at the root of the repo

"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from llm_client import complete, default_model, get_client

load_dotenv()

SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", Path(__file__).parent / "system_prompt.txt"))
TARGET_MODEL = os.getenv("TARGET_MODEL", default_model())

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text().strip()

app = FastAPI(title="BrightPath Assistant (target agent)")
client = get_client()

# conversation_id -> message history. In-memory is fine for a single-process PoC.
conversations: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    history = conversations.setdefault(conversation_id, [])

    history.append({"role": "user", "content": req.message})

    reply_text = complete(client, TARGET_MODEL, SYSTEM_PROMPT, history)
    history.append({"role": "assistant", "content": reply_text})

    return ChatResponse(response=reply_text, conversation_id=conversation_id)
