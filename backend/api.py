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

import logging
import os
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

# ADAPT #1 — import your compiled graph.
from backend.graph import investmind_graph  # change if the export name differs

# Structured report type so we can turn it into markdown for the frontend.
from backend.writer.schemas import InvestmentReport

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("INVESTMIND_API_KEY")
if not API_KEY:
    # Loud warning: with no key set, the endpoints are UNAUTHENTICATED and any
    # caller can burn Groq + Tavily credits. Always set this on a deployed host.
    logger.warning(
        "INVESTMIND_API_KEY is not set — /research is OPEN and unauthenticated. "
        "Set it in the environment before deploying."
    )

app = FastAPI(title="InvestMind API")

app.add_middleware(
    CORSMiddleware,
    # For the demo this is open. Tighten to your Vercel origin before sharing,
    # e.g. allow_origins=["https://investmind-frontend.vercel.app"].
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store. Fine for v1; swap for Redis/DB if you need
# multi-worker or restart persistence. Deploy with a SINGLE worker.
SESSIONS: dict[str, dict[str, Any]] = {}


class StartReq(BaseModel):
    prompt: str


class ClarifyReq(BaseModel):
    answer: str


def _auth(authorization: str | None) -> None:
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(401, "unauthorized")


def _invoke(messages: list[BaseMessage]) -> dict[str, Any]:
    """Run the graph with a message history. ADAPT if your state key
    isn't `messages` — check backend/state.py."""
    return investmind_graph.invoke({"messages": messages})


def _report_to_markdown(report: InvestmentReport) -> str:
    """Flatten the structured InvestmentReport into markdown for display.

    Inline [N#] citation markers in the content are preserved as-is.
    """
    parts: list[str] = [f"# {report.title}", ""]

    parts.append("## Executive Summary")
    parts.append(report.executive_summary.content)
    parts.append("")

    for section in report.sections:
        parts.append(f"## {section.heading}")
        parts.append(section.analysis.content)
        parts.append("")

    if report.evidence_limitations:
        parts.append("## Evidence Limitations")
        parts.extend(f"- {item}" for item in report.evidence_limitations)
        parts.append("")

    return "\n".join(parts).strip()


def _pack_response(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """Turn a final graph state into the frontend response shape and
    keep the in-memory session in sync."""
    needs = bool(state.get("need_clarification"))
    question = state.get("clarification_question")

    if needs and question:
        # Append the assistant question to the stored history so the next
        # /clarify call can extend it with the user's answer.
        SESSIONS[session_id]["messages"].append(AIMessage(content=question))
        return {
            "status": "needs_clarification",
            "session_id": session_id,
            "clarification_question": question,
        }

    # investment_report is a structured InvestmentReport (or a dumped dict),
    # never a plain string — serialize it to markdown for the frontend.
    report_obj = state.get("investment_report")
    if isinstance(report_obj, InvestmentReport):
        report_md = _report_to_markdown(report_obj)
    elif isinstance(report_obj, dict):
        report_md = _report_to_markdown(InvestmentReport(**report_obj))
    else:
        report_md = report_obj or ""

    # PDF now comes back as base64 straight from the graph state — no disk read.
    pdf_b64 = state.get("pdf_base64")
    pdf_name = state.get("pdf_filename") or "investmind-report.pdf"

    # Report is done — free the session.
    SESSIONS.pop(session_id, None)

    return {
        "status": "report",
        "report_markdown": report_md,
        "pdf_base64": pdf_b64,
        "pdf_filename": pdf_name,
        "pdf_error": state.get("pdf_error"),
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