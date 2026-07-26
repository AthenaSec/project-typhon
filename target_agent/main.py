"""Mock target chatbot for the red-team demo.

Deliberately weak system prompt (see system_prompt.txt) — this is the thing
that gets attacked. Swap SYSTEM_PROMPT_PATH / TARGET_MODEL via env vars to
point this at a different persona or model without touching code.
"""

import os
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", Path(__file__).parent / "system_prompt.txt"))
TARGET_MODEL = os.getenv("TARGET_MODEL", "claude-opus-5")

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text().strip()

app = FastAPI(title="BrightPath Assistant (target agent)")
client = anthropic.Anthropic()

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

    message = client.messages.create(
        model=TARGET_MODEL,
        max_tokens=1024,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=history,
    )

    reply_text = next((b.text for b in message.content if b.type == "text"), "")
    history.append({"role": "assistant", "content": reply_text})

    return ChatResponse(response=reply_text, conversation_id=conversation_id)
