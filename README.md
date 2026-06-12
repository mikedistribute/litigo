# Litigo

**An agentic AI pipeline that turns competition-law decisions into ranked, fundable litigation investment opportunities.**

Litigo ingests antitrust and competition-authority decisions, extracts the key investment variables, and delivers an investment score for follow-on litigation opportunities — producing a senior-grade investment memorandum in minutes instead of weeks.

---

## Inspiration

Antitrust and competition-law decisions published every year by the European Commission, national authorities, and courts often reveal that thousands of companies — especially SMEs — were overcharged by cartels or abusive market practices. Most of these victims never claim the damages they are entitled to, simply because identifying themselves in a 200-page legal decision, building a case, and funding a multi-year litigation is out of reach.

On the other side of the table, Third-Party Litigation Funding (TPLF) funds are constantly looking for solid follow-on cases to invest in, but their sourcing process is still painfully manual: read the decision, extract the cartel's perimeter, list candidate buyers, run financial due diligence, and finally write an investment memo.

We wanted to bridge that gap. Litigo was born from a simple idea: **an antitrust decision is a structured signal** — an AI agent should be able to read it, understand who was harmed, and turn it into a ranked, fundable investment shortlist.

## What it does

Litigo is an agentic AI pipeline for TPLF due diligence. From a single competition-law decision (PDF or text), it produces a complete investment memorandum in a few minutes:

1. **Reads the decision** and extracts a strict, schema-validated `judicial_contract` (infraction type, affected markets, geographic scope, damage period, sanctioned parties, buyer profiles, legal findings, NACE codes, appeal status, etc.).
2. **Sources candidate companies** that match the affected buyer profile described in the decision.
3. **Runs parallel deep research** on each candidate (revenue, market cap, ticker/ISIN, credit rating, legal team, exposure to the cartelized market, corporate continuity) using grounded web search.
4. **Scores and ranks** each company on its TPLF attractiveness (exposure, financial resilience, legal standing, procedural risks).
5. **Writes a senior-grade investment memorandum** — executive summary, legal mechanics of the infraction, top-3 targets, risk factors, and a final recommendation — and exports it as a clean `.docx` ready for an investment committee.

The user just uploads a decision; Litigo returns a shortlist of fundable claimants and the memo to back it up.

## How it's built

- **Backend:** Python, FastAPI, LangGraph and LangChain. The pipeline is modeled as a stateful graph of agentic nodes (`document_analyzer`, `company_sourcing`, `company_research`, `judge`, `report_writer`) communicating through a strongly-typed `PipelineState`.
- **LLM layer:** Google Gemini via `langchain-google-genai`, used both with structured outputs (Pydantic schemas like `JudicialContract`, `CompanyReport`, `FinalReport`) and as a ReAct agent with a custom Gemini grounding search tool for live, citable web research.
- **Caching:** A content-hash-based LLM cache so that re-running an analysis on the same decision is instant and free.
- **Document generation:** A `.docx` builder that turns the `FinalReport` Pydantic object into a polished investment memo.
- **Frontend:** Next.js 16 (App Router) + React 19 + TypeScript, Tailwind CSS 4, and shadcn/ui components. The architecture page visualizes the pipeline graph live, and the analysis page streams the agents' progress to the user.
- **Deployment:** Frontend ships to the edge on **Cloudflare**; the backend runs on **Railway** via **Docker Compose** (FastAPI app + worker + datastore), so the whole pipeline is reproducible from a single `docker compose up`.

## Architecture

```
            ┌─────────────────────────────┐
 Decision   │   Next.js (Cloudflare)      │   live agent
 PDF / text │   upload · stream · memo dl │◀── progress stream
   ──────▶  └──────────────┬──────────────┘
                           │ REST / SSE
                           ▼
            ┌─────────────────────────────┐
            │   FastAPI (Railway · Docker)│
            │                             │
            │   LangGraph PipelineState   │
            │   ┌───────────────────────┐ │
            │   │ document_analyzer     │ │  → judicial_contract
            │   │ company_sourcing      │ │  → candidate buyers
            │   │ company_research  ×N  │ │  → grounded deep research (parallel)
            │   │ judge                 │ │  → TPLF score & ranking
            │   │ report_writer         │ │  → FinalReport → .docx
            │   └───────────────────────┘ │
            │   Gemini · structured out   │
            │   content-hash LLM cache    │
            └─────────────────────────────┘
```

---

## Repository layout

```
litigo/
├── frontend/   # Next.js 16 · React 19 · Tailwind 4 · shadcn/ui  → Cloudflare
└── backend/    # FastAPI · LangGraph · Gemini                    → Railway (Docker Compose)
```

> **Status:** Frontend scaffold in place. Backend scaffolding in progress.
