"""
FastAPI Application Entry Point
────────────────────────────────
Agentic AI–Driven Workflow Automation System
PSG AI Consortium | Institutional Governance
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers  import (
    auth_router, proposals_router, approvals_router,
    vendors_router, analytics_router,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ── Lifespan: create DB tables + seed data on first launch ───────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Seed default data if DB is empty
    try:
        from seed_data import seed_all
        await seed_all()
    except Exception as exc:
        logging.warning(f"Seeding skipped: {exc}")
    yield


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Agentic AI Workflow Automation",
    description = ("Multi-agent AI system for institutional governance — "
                   "event approvals, hierarchical routing, ERP integration, "
                   "procurement intelligence."),
    version     = "1.0.0",
    lifespan    = lifespan,
)

# CORS — allow React frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(proposals_router)
app.include_router(approvals_router)
app.include_router(vendors_router)
app.include_router(analytics_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "system": "Agentic AI Workflow Automation System",
        "status": "running",
        "docs":   "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
