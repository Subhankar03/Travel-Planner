"""Chat API route — POST /api/chat."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.graph import get_graph
from backend.core.stream_formatter import stream_langgraph_as_vercel_sse
from backend.models.schemas import ChatRequest

router = APIRouter()


# ── POST /api/chat ─────────────────────────────────────────────────────────────
@router.post('/chat')
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream LangGraph agent output as Vercel AI SDK v6 SSE."""
    graph = get_graph()

    messages = [
        {'role': msg.role, 'content': msg.content}
        for msg in request.messages
    ]

    sse_generator = stream_langgraph_as_vercel_sse(
        graph=graph,
        messages=messages,
        thread_id=request.thread_id,
        user_location=request.user_location,
    )

    return StreamingResponse(
        sse_generator,
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'x-vercel-ai-ui-message-stream': 'v1',
        },
    )
