"""FastAPI wrapper for the InvestMind LangGraph app.

Endpoints:
  POST /research
      body: { "prompt": str }
      -> { "status": "needs_clarification", "session_id": str,
            "clarification_question": str }
         or { "status": "report", "report_markdown": str,
              "pdf_base64": str, "pdf_filename": str }

  POST /research/{session_id}/clarify
      body: { "answer": str }
      -> same shape as above (may ask again or return the report)
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

# ADAPT #1 — import your compiled graph.
from backend.graph import investmind_graph  # change if the export name differs

load_dotenv()

API_KEY = os.environ.get("INVESTMIND_API_KEY")

app = FastAPI(title="InvestMind API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store. Fine for v1; swap for Redis/DB if you need
# multi-worker or restart persistence.
SESSIONS: dict[str, dict[str, Any]] = {}


class StartReq(BaseModel):
    prompt: str


class ClarifyReq(BaseModel):
    answer: str


def _auth(authorization: str | None) -> None:
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(401, "unauthorized")


def _invoke(messages: list[BaseMessage]) -> dict[str, Any]:
    """Run the graph with a message history. ADAPT #2 if your state key
    isn't `messages` — check backend/state.py."""
    return investmind_graph.invoke({"messages": messages})


def _pack_response(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """Turn a final graph state into the frontend response shape and
    keep the in-memory session in sync."""
    needs = bool(
        state.get("need_clarification")
        or state.get("needs_clarification")
        or state.get("requires_clarification")
    )
    question = (
        state.get("clarification_question")
        or state.get("clarifying_question")
        or state.get("planner_question")
    )

    if needs and question:
        # Append the assistant question to the stored history so the next
        # /clarify call can extend it with the user's answer.
        SESSIONS[session_id]["messages"].append(AIMessage(content=question))
        return {
            "status": "needs_clarification",
            "session_id": session_id,
            "clarification_question": question,
        }

    report_md = (
        state.get("investment_report")
        or state.get("report_markdown")
        or state.get("final_report")
        or ""
    )
    pdf_b64: str | None = None
    pdf_name = "investmind-report.pdf"
    pdf_path_str = state.get("pdf_path") or state.get("report_pdf_path")
    if pdf_path_str and Path(pdf_path_str).exists():
        p = Path(pdf_path_str)
        pdf_b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        pdf_name = p.name

    # Report is done — free the session.
    SESSIONS.pop(session_id, None)

    return {
        "status": "report",
        "report_markdown": report_md,
        "pdf_base64": pdf_b64,
        "pdf_filename": pdf_name,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/research")
def research(req: StartReq, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not req.prompt.strip():
        raise HTTPException(400, "prompt is required")

    session_id = uuid4().hex
    messages: list[BaseMessage] = [HumanMessage(content=req.prompt)]
    SESSIONS[session_id] = {"messages": messages}

    try:
        state = _invoke(messages)
    except Exception as e:
        SESSIONS.pop(session_id, None)
        raise HTTPException(500, f"graph error: {e}") from e

    return _pack_response(session_id, state)


@app.post("/research/{session_id}/clarify")
def clarify(
    session_id: str,
    req: ClarifyReq,
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(404, "session not found or already completed")
    if not req.answer.strip():
        raise HTTPException(400, "answer is required")

    session["messages"].append(HumanMessage(content=req.answer))

    try:
        state = _invoke(session["messages"])
    except Exception as e:
        raise HTTPException(500, f"graph error: {e}") from e

    return _pack_response(session_id, state)
