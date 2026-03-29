"""Pydantic request / response schemas for the chat API."""

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(description='Message role: "user" or "assistant".')
    content: str = Field(description='Text content of the message.')


class ChatRequest(BaseModel):
    """Payload sent by the React frontend to POST /api/chat."""

    messages: list[ChatMessage] = Field(
        description='Full conversation history as sent by the Vercel AI SDK useChat hook.'
    )
    thread_id: str = Field(
        description='Client-generated UUID that identifies this conversation thread.'
    )
    user_location: str | None = Field(
        default=None,
        description='Optional user location string from the frontend (e.g. "Kolkata, West Bengal").',
    )
