# Litigo

### Agentic AI pipeline for Third-Party Litigation Funding

Litigo turns public competition-law decisions into litigation funding intelligence: it reads a legal decision, identifies affected markets, sources potential claimants, ranks the opportunity, and generates an investment memo for fund review.

Project inspired by the Paris Fintech Hackathon 2026 TPLF workflow.

---

## Live app

| Service | URL |
| --- | --- |
| Marketing site | https://litigo-frontend.mikebuilder22.workers.dev |
| Product app | https://litigo-frontend.mikebuilder22.workers.dev/app |
| Backend API | https://litigo-production.up.railway.app |
| API health | https://litigo-production.up.railway.app/api/v1/health |
| FastAPI docs | https://litigo-production.up.railway.app/docs |

---

## Overview

Litigo is a web platform for Third-Party Litigation Funding (TPLF) teams.

Starting from a court, regulator, or competition-authority decision, the pipeline:

1. Extracts a structured judicial contract: jurisdiction, infraction, sanctioned entities, affected markets, buyer profiles, appeal status, and legal findings.
2. Sources companies that may have been harmed by the conduct described in the decision.
3. Runs company research with grounded LLM search.
4. Ranks the opportunity from a litigation-funding perspective.
5. Writes an investment memo and exposes download endpoints for `.docx` and `.pdf` outputs.

Main frontend pages:

| Route | Purpose |
| --- | --- |
| `/` | Marketing and value proposition page. |
| `/app` | Upload a decision, run the analysis, track progress, preview output, and download the memo. |

---

## How to use the live app

1. Open the product app: https://litigo-frontend.mikebuilder22.workers.dev/app
2. Upload a decision file.
   - Supported formats: `.pdf`, `.docx`, `.txt`
   - For a quick demo, use `backend/tests/fixtures/sample_decision_fr.txt`.
3. Click **Start analysis**.
4. Watch the pipeline progress:
   - Read decision
   - Find companies
   - Research targets
   - Rank opportunity
   - Write memo
   - Prepare export
5. Review the memo snapshot.
6. Download the generated `.docx` or `.pdf` when ready.

> Current MVP note: jobs and generated files are stored by the backend process. This is enough for the first demo, but a production fund workflow should move files, jobs, and audit history to durable storage.

---

## Tech stack

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, lucide-react.
- **Backend:** Python 3.12, FastAPI, LangGraph, LangChain, Google Gemini, Pydantic v2.
- **Document processing:** pypdf, python-docx, docx2pdf.
- **Deployment:** Cloudflare Workers for the frontend via OpenNext; Railway for the FastAPI backend.

---

## Quick start

### 1. Clone the repository

```bash
git clone <repository-url>
cd litigo
```

### 2. Run the backend

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

Set your Gemini API key in `backend/.env`:

```bash
GOOGLE_API_KEY=your_gemini_api_key
```

Start FastAPI:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Local backend services:

| Service | URL |
| --- | --- |
| API | http://127.0.0.1:8000 |
| Health | http://127.0.0.1:8000/api/v1/health |
| Swagger | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

### 3. Run the frontend

Open a second terminal:

```bash
cd frontend
bun install
cp .env.example .env.local
bun run dev
```

By default, `frontend/.env.example` points to the deployed Railway backend:

```bash
NEXT_PUBLIC_API_BASE_URL=https://litigo-production.up.railway.app
```

For local backend development, change `frontend/.env.local` to:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Open:

| Page | URL |
| --- | --- |
| Marketing site | http://localhost:3000 |
| Product app | http://localhost:3000/app |

---

## Minimal API flow

You can test the backend without the frontend.

### Upload a decision

```bash
curl -s -F "file=@backend/tests/fixtures/sample_decision_fr.txt" \
  https://litigo-production.up.railway.app/api/v1/analysis/upload
```

The response includes a `document_id`.

### Start an analysis

```bash
curl -s -X POST https://litigo-production.up.railway.app/api/v1/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"document_id":"<document_id>"}'
```

The response includes a `job_id`.

### Stream progress

```bash
curl -N https://litigo-production.up.railway.app/api/v1/analysis/<job_id>/stream
```

### Get result metadata

```bash
curl -s https://litigo-production.up.railway.app/api/v1/analysis/<job_id>/result
```

### Download outputs

```bash
curl -L -o memo.docx \
  https://litigo-production.up.railway.app/api/v1/analysis/<job_id>/download/docx

curl -L -o memo.pdf \
  https://litigo-production.up.railway.app/api/v1/analysis/<job_id>/download/pdf
```

---

## Useful scripts

### Frontend

Run from `frontend/`.

| Command | Description |
| --- | --- |
| `bun run dev` | Start Next.js dev server on port 3000. |
| `bun run build` | Build the production Next.js app. |
| `bun run lint` | Run ESLint. |
| `bun run typecheck` | Run TypeScript checks. |
| `bun run preview` | Build and preview with OpenNext Cloudflare. |
| `bun run deploy` | Build and deploy the frontend to Cloudflare Workers. |

### Backend

Run from `backend/`.

| Command | Description |
| --- | --- |
| `uvicorn main:app --reload --port 8000` | Start the FastAPI dev server. |
| `python -m pytest tests` | Run all backend tests. |
| `python -m tests.test_document_analyzer` | Run one learning-oriented test module directly. |

---

## Repository structure

```text
litigo/
├── backend/
│   ├── api/v1/routes/
│   │   ├── analysis.py
│   │   └── health.py
│   ├── models/
│   │   ├── contract.py
│   │   ├── pipeline.py
│   │   └── reports.py
│   ├── pipeline/
│   │   ├── graph.py
│   │   ├── judicial_from_contract.py
│   │   └── nodes/
│   ├── services/
│   │   ├── job_manager.py
│   │   └── llm_cache.py
│   ├── tests/
│   ├── config.py
│   ├── main.py
│   ├── railway.json
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── app/page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   ├── lib/
│   ├── open-next.config.ts
│   ├── package.json
│   └── wrangler.jsonc
└── README.md
```

---

## Deployment

### Frontend: Cloudflare Workers

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=https://litigo-production.up.railway.app bun run deploy
```

Current deployed app:

```text
https://litigo-frontend.mikebuilder22.workers.dev
```

### Backend: Railway

Railway uses `backend/railway.json`:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Required Railway environment variable:

```bash
GOOGLE_API_KEY=your_gemini_api_key
```

---

## Notes

- `backend/.env` and `frontend/.env.local` are ignored and should never be committed.
- The backend currently keeps jobs in memory and writes generated files to local backend storage.
- PDF generation can depend on OS-level document conversion support; DOCX output is the safer MVP export.
- The product roadmap for a fund-grade version is documented in `backend/PRODUCT_ROADMAP.md`.

---

## Credits

Litigo - agentic legal finance intelligence for TPLF workflows.
