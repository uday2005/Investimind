# InvestMind Project Documentation

## Current Goal

InvestMind is an agentic research workflow that turns a user request into an
evidence-grounded investment research PDF.

The current working path is:

```text
User Request
-> Planner Agent
-> Research Agent
-> Evidence Curator
-> Report Writer
-> PDF Renderer
```

The citation validator exists in code, but it is temporarily bypassed in the
writer graph so the end-to-end product path can produce PDFs reliably while the
validator is improved later.

## Agent Flow

### 1. Planner Agent

Purpose:

- Decide whether the user request needs clarification.
- Convert a clear request into a structured research brief.

Main outputs:

- `need_clarification`
- `clarification_question`
- `objective`
- `scope`
- `constraints`
- `required_information`

Important behavior:

- Ambiguous requests like "Tell me about Apple" should ask for clarification.
- Clear requests like "Analyze Nvidia as a long-term investment" should move
  into research.
- The planner uses the reliable model because mistakes here affect the whole
  graph.

### 2. Research Agent

Purpose:

- Generate search queries from the research brief.
- Retrieve web information with Tavily.
- Extract atomic research notes.
- Check whether the notes cover the required information.
- Generate follow-up queries only when useful and within budget.

Main nodes:

- `query_generator`
- `information_retrieval`
- `note_extractor`
- `coverage_checker`
- `follow_up_query_generator`

Main outputs:

- `queries`
- `searched_queries`
- `search_results`
- `research_notes`
- `is_sufficient`
- `missing_information`
- `coverage_assessment`

Current budget controls:

- Max initial queries: `8`
- Max follow-up queries per round: `3`
- Max total searched queries: `10`
- Max notes per source: `5`
- Max accumulated research notes: `40`

These limits are temporary safety rails for cost and debugging. Later, the note
budget should become dynamic by report depth or by required information item.

### 3. Evidence Curator

Purpose:

- Group the best research notes under each required information item.
- Keep the writer focused on relevant evidence instead of passing every note.
- Track conflicting evidence separately.

Schema:

```python
class EvidenceGroup(BaseModel):
    requirement: str
    selected_note_ids: list[int]
    conflicting_note_ids: list[int] = []
```

Why this helps:

- `requirement` keeps each group tied to one research need.
- `selected_note_ids` tells the writer which evidence to use.
- `conflicting_note_ids` lets the writer mention disagreement instead of hiding
  it.

The node also performs deterministic cleanup:

- removes invalid note IDs
- removes duplicates
- prevents selected/conflicting overlap
- limits selected notes per group
- creates one group per required information item

### 4. Report Writer

Purpose:

- Write the investment report using only curated evidence.
- Produce structured report data that can be rendered into PDF.

Main output:

- `investment_report`

Important rules:

- No web search.
- No outside knowledge.
- Every factual claim should cite note IDs like `[N1]`.
- If evidence is missing, the report should say evidence is insufficient instead
  of inventing facts.
- Conflicting evidence should be described cautiously.

The report writer uses the reliable model because weaker models produced broken
structured output for the report schema.

### 5. PDF Renderer

Purpose:

- Turn the structured investment report into a PDF.

Main outputs:

- `pdf_path`
- `pdf_error`

Current behavior:

- PDF generation runs directly after report writing.
- Citation validation is not required for PDF generation in the current v1
  graph.
- The PDF includes title, generated date, executive summary, sections, evidence
  limitations, source appendix, page header/footer, and disclaimer.

PDF output folder:

```text
output/pdf/
```

## Citation Validator Status

The citation validator node is implemented but currently bypassed.

Why it is bypassed:

- It was too strict for v1.
- It sometimes failed reports that honestly acknowledged uncertainty.
- LLM semantic validation sometimes returned invalid structured output.
- It blocked PDF generation even when the rest of the pipeline worked.

What it currently checks:

- invalid note IDs
- mismatch between inline citations and `cited_note_ids`
- missing citations
- requirement mismatch
- semantic unsupported claims
- ignored conflicts

Future improvements:

- Parse grouped citations like `[N25, N26]` correctly.
- Make semantic validation less strict.
- Separate "coverage quality" from "citation validity".
- Add a deterministic citation fixer before running semantic validation.
- Re-enable the node in the writer graph when it is stable.

## Model Routing

The project now uses model routing in:

```text
backend/llm.py
```

Current split:

```text
Scout 17B:
- query_generator
- follow_up_query_generator
- note_extractor
- coverage_checker
- evidence_curator

70B reliable model:
- clarification
- research_brief
- report_writer
- citation_validator
```

Reason:

- Scout has higher TPM and is cheaper for simpler nodes.
- 70B is more reliable for strict structured output and important reasoning.
- Scout failed on complex report/citation schemas by returning invalid tool
  shapes.

Environment overrides:

```bash
GROQ_SCOUT_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_RELIABLE_MODEL=llama-3.3-70b-versatile
```

## Token And Cost Optimizations

This was one of the biggest improvements in the research agent.

Before optimization:

- 16 queries
- 96 notes
- 27,846 tokens

After optimization:

- 5 queries
- 31 notes
- 12,504 tokens

Impact:

- About 55% token reduction.
- About 69% query reduction.
- About 68% note reduction.

Changes that reduced tokens:

- One query per requirement.
- Hard max total search budget.
- Follow-up query budget.
- Search history dedupe.
- Query dedupe before Tavily calls.
- Max notes per source.
- Max accumulated notes.
- Cross-round note dedupe.
- Non-evidence note filtering.
- Stop research when query budget is exhausted.
- Use Scout for cheaper/simple nodes.


## Real LLM And Rate Limit Notes

Groq failures seen during testing:

- Daily token limit:
  - `100,000 tokens/day` for `llama-3.3-70b-versatile` on one tested account.
- Tokens per minute:
  - `12,000 TPM` for `llama-3.3-70b-versatile`.
  - Scout model had a higher TPM in testing.

Recommended approach:

- Use fake LLMs for deterministic unit tests.
- Use real LLMs for individual node tests.
- Run the full live graph only when needed.
- Consider shared retry/backoff for every LLM node later.

## How To Run

Run the full live graph test:

```bash
cd /Users/uday/Desktop/Investimind
RUN_REAL_LLM_TESTS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -s -p no:cacheprovider test_investmind_graph_real.py
```

Run the deterministic local tests:

```bash
cd /Users/uday/Desktop/Investimind
PYTHONDONTWRITEBYTECODE=1 LANGCHAIN_TRACING_V2=false LANGSMITH_TRACING=false .venv/bin/python -m pytest -q -p no:cacheprovider
```

The live graph prints:

- clarification result
- objective
- required information
- searched queries
- research note count
- coverage status
- report content
- PDF path/error

Generated PDFs are written to:

```text
/Users/uday/Desktop/Investimind/output/pdf/
```

## Current Known Tradeoffs

### Citation Validation Is Bypassed

This is intentional for the current working version. The goal is to keep the
product path moving while citation validation is improved separately.

### Note Cap Is Temporary

The current max note cap is useful for cost control, but final report quality may
need more evidence.

Future direction:

```text
small query: 25-40 notes
normal company report: 60-100 notes
deep investment report: 120+ notes
```

Better long-term approach:

```text
max useful notes per required_information item
```

### Tavily Is The Only Retrieval Tool

Current information retrieval uses Tavily.

Future retrieval tools:

- SEC filings
- company investor relations pages
- financial market data APIs
- Yahoo Finance or similar
- MCP tools

## Future Improvements

- Re-enable citation validator after making it stable.
- Add a citation fixer node.
- Add deterministic citation parsing for grouped citations.
- Add retry/backoff for all LLM calls.
- Cache intermediate research state to avoid repeated full runs.
- Add dynamic token budgets by report depth.
- Add better source ranking before evidence curation.
- Add SEC and finance-specific retrievers.
- Add frontend/backend API integration.
- Add user-selectable report depth: quick, standard, deep.
- Add a final report quality checker.

## Current V1 Summary

InvestMind now has a complete working end-to-end flow:

```text
user prompt -> plan -> research -> curate evidence -> write report -> render PDF
```

The strongest parts today:

- structured planner output
- budgeted research graph
- Tavily retrieval
- note extraction with dedupe
- evidence grouping
- investment report writing
- PDF generation
- model routing for cost and reliability

The main thing intentionally left for later:

- strict citation validation before PDF generation
