# InvestMind

InvestMind is an agentic investment research workflow that turns a user request
into an evidence-grounded PDF report.

The current v1 flow is:

```text
User Request
-> Planner Agent
-> Research Agent
-> Evidence Curator
-> Report Writer
-> PDF Renderer
```

## What It Does

InvestMind takes a research prompt such as:

```text
Evaluate Microsoft as a long-term investment using fiscal 2024 evidence.
Analyze revenue growth, operating income growth, Azure and AI momentum,
competitive position, and material risks.
```

Then it:

- decides whether clarification is needed
- creates a structured research brief
- generates search queries
- retrieves information with Tavily
- extracts atomic research notes
- checks coverage
- curates evidence by requirement
- writes an investment research report
- renders the report as a PDF

## Current Status

This repository contains a working v1 pipeline from prompt to PDF.

The citation validator/checker exists in code, but it is temporarily bypassed in
the active writer graph. The current product path renders the PDF directly after
report writing. Citation validation will be re-enabled after it is made less
strict and more reliable with real research output.

For deeper architecture notes, see:

[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

## Architecture

### Planner Agent

The planner decides whether the user request is clear enough to research. If it
is clear, it creates:

- `objective`
- `scope`
- `constraints`
- `required_information`

### Research Agent

The research agent is responsible for controlled web research:

- query generation
- Tavily retrieval
- note extraction
- coverage checking
- follow-up query generation

The research agent includes deterministic budget controls to avoid expensive
query and note fan-out.

### Evidence Curator

The evidence curator groups research notes by required information item. It
selects useful notes and tracks conflicting notes separately.

### Report Writer

The report writer creates a structured investment report using only curated
evidence. It does not search the web or use outside knowledge.

### PDF Renderer

The PDF renderer turns the structured report into a PDF with:

- title
- generated date
- executive summary
- report sections
- evidence limitations
- source appendix
- disclaimer

Generated PDFs are written to:

```text
output/pdf/
```

## Model Routing

InvestMind uses separate Groq models for cost and reliability.

Current split:

```text
Scout 17B:
- query generation
- follow-up query generation
- note extraction
- coverage checking
- evidence curation

70B:
- clarification
- research brief generation
- report writing
- citation validation
```

Environment overrides:

```bash
GROQ_SCOUT_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_RELIABLE_MODEL=llama-3.3-70b-versatile
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```bash
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

Optional LangSmith tracing:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=InvestMind
```

Do not commit `.env`.

## Running Tests

Run deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 LANGCHAIN_TRACING_V2=false LANGSMITH_TRACING=false .venv/bin/python -m pytest -q -p no:cacheprovider
```

Run the full live LLM integration test:

```bash
RUN_REAL_LLM_TESTS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -s -p no:cacheprovider test_investmind_graph_real.py
```

The live test uses Groq and Tavily credits.

## Token Optimization Work

The research agent was optimized to reduce uncontrolled token usage.

Before optimization:

- 16 queries
- 96 notes
- 27,846 tokens

After optimization:

- 5 queries
- 31 notes
- 12,504 tokens

Result:

- about 55% token reduction
- about 69% query reduction
- about 68% note reduction

The biggest improvements came from deterministic query budgets, dedupe, note
caps, and graph-level state controls.

## Known Limitations

- Citation validation is temporarily bypassed in the active graph.
- Tavily is currently the only retrieval tool.
- The global research note cap is a temporary cost safety rail.
- Full live graph tests can be expensive because they use multiple LLM calls.

## Roadmap

- Re-enable citation validation after improving reliability.
- Add deterministic citation parsing and citation fixing.
- Add SEC filing retrieval.
- Add finance-specific data retrieval.
- Add retry/backoff around all LLM calls.
- Add cached intermediate research states.
- Add report depth modes: quick, standard, deep.
- Build frontend and backend API surfaces.

## Disclaimer

InvestMind generates research reports for informational purposes only. It is not
financial advice and should not be treated as a buy, sell, or hold
recommendation. 
Maybe in future we can do that if we able to make it intelligent enough.
