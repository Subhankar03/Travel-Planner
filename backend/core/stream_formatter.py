"""Translate LangGraph stream events into Vercel AI SDK v6 UI Message Stream Protocol.

Protocol reference: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol
Each yielded string is a complete SSE line: `data: {json}\n\n`
"""
from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage


# ── Nodes whose LLM token deltas should NOT be streamed to the client ──────────
# The supervisor emits raw routing tokens like "DIRECT_RESPONSE" or
# "booking_agent" — these are internal control signals, not user-facing text.
_MUTED_NODES = {'supervisor'}


# ── SSE helpers ────────────────────────────────────────────────────────────────
def _sse(payload: dict | str) -> str:
    """Wrap a payload dict (or raw string like [DONE]) into an SSE data line."""
    if isinstance(payload, str):
        return f'data: {payload}\n\n'
    return f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'


def _uid() -> str:
    """Generate a short unique ID for stream parts."""
    return uuid.uuid4().hex


def _extract_text(content: Any) -> str:
    """Extract plain text from an AIMessageChunk's content.

    Gemini models return structured content blocks like:
        [{"type": "text", "text": "hello", "index": 0}]
    Other models return a plain string. This handles both.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text = block.get('text', '')
                if text:
                    parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return ''.join(parts)
    return str(content) if content else ''


# ── Main stream generator ─────────────────────────────────────────────────────
async def stream_langgraph_as_vercel_sse(
    graph,
    messages: list[dict],
    thread_id: str,
    user_location: str | None = None,
) -> AsyncGenerator[str, None]:
    """Run the LangGraph agent and yield Vercel AI SDK v6 compatible SSE chunks.

    Uses `astream(stream_mode=["messages", "updates"], version="v2")` so we get
    both fine-grained LLM token deltas and coarse node-level updates (for tool
    call / tool result detection).
    """
    # ── Convert frontend messages to LangChain message objects ─────────────
    lc_messages: list[HumanMessage | AIMessage] = []
    for msg in messages:
        if msg['role'] == 'user':
            lc_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            lc_messages.append(AIMessage(content=msg['content']))

    config = {'configurable': {'thread_id': thread_id}}
    graph_input: dict[str, Any] = {
        'messages': lc_messages,
        'user_location': user_location,
        'itinerary': None,
    }

    # ── Protocol: message start ────────────────────────────────────────────
    message_id = _uid()
    yield _sse({'type': 'start', 'messageId': message_id})
    yield _sse({'type': 'start-step'})

    # ── State for deduplication / text assembly ────────────────────────────
    text_part_id: str | None = None
    text_part_open = False
    seen_tool_call_ids: set[str] = set()
    active_step_has_tools = False

    try:
        async for chunk in graph.astream(
            graph_input,
            config,
            stream_mode=['messages', 'updates'],
            version='v2',
        ):
            chunk_type = chunk.get('type')

            # ── Token-level LLM deltas ─────────────────────────────────────
            if chunk_type == 'messages':
                msg_chunk, metadata = chunk['data']

                if isinstance(msg_chunk, AIMessageChunk):
                    # Skip tokens from muted nodes (e.g. supervisor routing)
                    langgraph_node = metadata.get('langgraph_node', '')
                    if langgraph_node in _MUTED_NODES:
                        continue

                    # If the chunk has tool_call_chunks, skip text streaming
                    # (the model is building tool call arguments, not user text)
                    if getattr(msg_chunk, 'tool_call_chunks', None):
                        continue

                    delta = _extract_text(msg_chunk.content)
                    if delta:
                        # Open a text part if we haven't yet
                        if not text_part_open:
                            text_part_id = _uid()
                            yield _sse({'type': 'text-start', 'id': text_part_id})
                            text_part_open = True

                        yield _sse({
                            'type': 'text-delta',
                            'id': text_part_id,
                            'delta': delta,
                        })

            # ── Node-level updates (tool calls / results) ──────────────────
            elif chunk_type == 'updates':
                for _node_name, node_output in chunk['data'].items():
                    if not isinstance(node_output, dict):
                        continue

                    node_messages = node_output.get('messages', [])

                    for msg in node_messages:
                        # ── Tool call intents from AI ──────────────────────
                        if isinstance(msg, AIMessage):
                            tool_calls = getattr(msg, 'tool_calls', None) or []

                            if tool_calls:
                                for tc in tool_calls:
                                    tc_id = tc.get('id', '')
                                    if tc_id in seen_tool_call_ids:
                                        continue
                                    seen_tool_call_ids.add(tc_id)
                                    active_step_has_tools = True

                                    # Close any open text part before tool events
                                    if text_part_open:
                                        yield _sse({'type': 'text-end', 'id': text_part_id})
                                        text_part_open = False

                                    tool_name = tc.get('name', 'unknown')
                                    tool_args = tc.get('args', {})

                                    yield _sse({
                                        'type': 'tool-input-start',
                                        'toolCallId': tc_id,
                                        'toolName': tool_name,
                                    })
                                    yield _sse({
                                        'type': 'tool-input-available',
                                        'toolCallId': tc_id,
                                        'toolName': tool_name,
                                        'input': tool_args,
                                    })
                            else:
                                # No tool calls — this is a plain text AIMessage
                                # (e.g. the supervisor's DIRECT_RESPONSE).
                                # Only emit if we haven't already streamed this
                                # text via the messages stream.
                                text = _extract_text(msg.content)
                                if text and not text_part_open:
                                    text_part_id = _uid()
                                    yield _sse({'type': 'text-start', 'id': text_part_id})
                                    yield _sse({
                                        'type': 'text-delta',
                                        'id': text_part_id,
                                        'delta': text,
                                    })
                                    yield _sse({'type': 'text-end', 'id': text_part_id})
                                    text_part_id = None

                        # ── Tool execution results ─────────────────────────
                        elif isinstance(msg, ToolMessage):
                            tc_id = msg.tool_call_id or ''
                            tool_name = msg.name or 'tool'
                            raw_output = msg.content

                            # Try to parse the JSON result
                            parsed: Any = raw_output
                            if isinstance(raw_output, str):
                                try:
                                    parsed = json.loads(raw_output)
                                except (json.JSONDecodeError, TypeError):
                                    pass

                            # Emit the standard tool output
                            yield _sse({
                                'type': 'tool-output-available',
                                'toolCallId': tc_id,
                                'output': parsed,
                            })

                            # Also emit a custom data-* part so the frontend
                            # can render rich cards (flights, hotels, etc.)
                            data_type = f'data-{tool_name}'
                            yield _sse({
                                'type': data_type,
                                'data': parsed,
                            })

                    # ── Step boundary for multi-agent turns ─────────────────
                    if active_step_has_tools:
                        yield _sse({'type': 'finish-step'})
                        yield _sse({'type': 'start-step'})
                        active_step_has_tools = False

    except Exception as exc:
        # Emit error in-stream so the frontend can display it gracefully
        yield _sse({'type': 'error', 'errorText': str(exc)})

    # ── Close any open text part ───────────────────────────────────────────
    if text_part_open:
        yield _sse({'type': 'text-end', 'id': text_part_id})

    # ── Protocol: finish ───────────────────────────────────────────────────
    yield _sse({'type': 'finish-step'})
    yield _sse({'type': 'finish'})
    yield _sse('[DONE]')
