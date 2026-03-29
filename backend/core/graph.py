"""LangGraph compilation with in-memory checkpointer.

NOTE: Upstash Redis does not support the RediSearch module (`FT._LIST`)
required by `langgraph-checkpoint-redis`. Since our sessions are anonymous
and ephemeral (no login, no long-term persistence), MemorySaver is the
correct choice for a single-process FastAPI server. If horizontal scaling
is needed later, swap to PostgreSQL (`AsyncPostgresSaver`) or a Redis
instance with RediSearch enabled.
"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from agent import build_graph


# ── Module-level state ────────────────────────────────────────────────────────
_compiled_graph = None
_checkpointer: MemorySaver | None = None


# ── Lifecycle helpers (called from FastAPI lifespan) ───────────────────────────
async def init_graph() -> None:
    """Initialise the checkpointer and compile the graph once."""
    global _checkpointer, _compiled_graph  # noqa: PLW0603

    _checkpointer = MemorySaver()
    _compiled_graph = build_graph(checkpointer=_checkpointer)


async def shutdown_graph() -> None:
    """Tear down resources cleanly."""
    global _checkpointer, _compiled_graph  # noqa: PLW0603

    _checkpointer = None
    _compiled_graph = None


def get_graph():
    """Return the compiled graph (must be called after init_graph)."""
    if _compiled_graph is None:
        raise RuntimeError('Graph not initialised – call init_graph() first.')
    return _compiled_graph
