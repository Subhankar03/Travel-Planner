"""FastAPI application entry-point for the AI Travel Planner backend."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.graph import init_graph, shutdown_graph
from backend.routes.chat import router as chat_router


# ── Lifespan (Redis init / teardown) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: connect to Redis and compile the graph.
    Shutdown: close Redis cleanly.
    """
    await init_graph()
    yield
    await shutdown_graph()


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title='AI Travel Planner API',
    version='0.2.0',
    lifespan=lifespan,
)

# CORS — permissive during development; lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ── API routes ─────────────────────────────────────────────────────────────────
app.include_router(chat_router, prefix='/api')


@app.get('/api/health')
async def health() -> JSONResponse:
    """Simple liveness probe."""
    return JSONResponse({'status': 'ok'})


# ── Serve React frontend (static files) ───────────────────────────────────────
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'

if _FRONTEND_DIR.is_dir():
    app.mount('/assets', StaticFiles(directory=_FRONTEND_DIR / 'assets'), name='assets')

    @app.get('/{full_path:path}')
    async def serve_spa(request: Request, full_path: str) -> FileResponse:
        """Catch-all: serve index.html for client-side routing."""
        file_path = _FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_FRONTEND_DIR / 'index.html')
