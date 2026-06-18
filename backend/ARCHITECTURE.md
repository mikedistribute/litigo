# Architecture — Litigo Backend

Litigo is a Python backend for automating part of the TPLF due diligence workflow
(`Third Party Litigation Funding`). The goal is to receive or analyze a legal
decision, extract structured information, identify potentially harmed companies,
research them, select the strongest opportunities, and generate a professional
report.

Reference inspiration:
https://github.com/LouisPages/2026ParisFinTech/tree/main/backend

## 1. Backend Goal

The backend exposes a FastAPI API that will gradually support this flow:

```text
Upload / receive legal decision
        ↓
Extract structured judicial data
        ↓
Run the agentic due diligence pipeline
        ↓
Research candidate companies
        ↓
Select the best TPLF opportunities
        ↓
Generate a downloadable report
```

## 2. Current Project Structure

```text
backend/
  api/v1/routes/       HTTP endpoints grouped by API version
  cache/               Runtime cache files generated during analysis
  models/              Pydantic schemas for validated data shapes
  pipeline/            LangGraph workflow and orchestration
  pipeline/nodes/      Individual agent steps
  services/            Reusable backend logic
  tools/               External helper tools and integrations
  config.py            Environment/config loading
  main.py              FastAPI app entrypoint
  requirements.txt     Python dependencies
  test_llm.py          Small Gemini connection test
```

## 3. Why These Folders Exist

`api/` contains HTTP routes. A route answers questions like: which URL exists,
which HTTP method it uses, and which response it returns.

`models/` contains schemas. A schema defines the exact shape of a piece of data.
For example, a job status response should always contain `status`,
`progress_pct`, and `message`.

`pipeline/` contains the main workflow. This is where LangGraph will connect the
steps together.

`pipeline/nodes/` contains one file per pipeline step: document analysis, company
sourcing, company research, selection, report writing, and document generation.

`services/` contains reusable backend logic that is not directly an HTTP route:
job management, text extraction, caching, and report generation.

`tools/` contains wrappers around external systems, such as Gemini Grounding,
future financial APIs, or company data providers.

`cache/` stores runtime-generated data. It is not source code, so its contents
should generally be ignored by git.

## 4. Python Package Notes

A Python folder becomes explicitly importable when it contains an `__init__.py`
file.

Example:

```text
api/v1/routes/health.py
```

can be imported with:

```py
from api.v1.routes import health
```

`__pycache__` is different. We do not create it manually. Python creates it
automatically when Python files are imported, executed, or compiled.

Useful command:

```sh
uv run python -m compileall .
```

## 5. Dependency Strategy

This backend uses `requirements.txt`, matching the reference backend.

We use `uv` as the environment and command runner:

```sh
uv venv
uv pip install -r requirements.txt
uv run python test_llm.py
uv run uvicorn main:app --reload
```

`requirements.txt` describes what the application needs. `uv` installs and runs
those dependencies quickly.

## 6. Runtime Entry Point

`main.py` is the FastAPI entrypoint.

Locally or on Railway, Uvicorn will load:

```sh
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Meaning:

```text
main.py -> the Python file
app     -> the FastAPI object inside that file
```

## 7. Target API

Endpoints should be built step by step:

```text
GET  /api/v1/health
POST /api/v1/analysis/upload
POST /api/v1/analysis/start
GET  /api/v1/analysis/{job_id}/status
GET  /api/v1/analysis/{job_id}/result
GET  /api/v1/analysis/{job_id}/stream
```

We start with `/health` because it proves the backend runs correctly before we
add complex pipeline logic.

## 8. Target Pipeline

The final pipeline will look like this:

```text
document_analyzer
        ↓
company_sourcing
        ↓
company_research
        ↓
selection_agent
        ↓
report_writer
        ↓
document_generator
```

Each step receives structured state and returns updates to that state.

## 9. Why Schemas / Models Matter

Schemas prevent random dictionaries from flowing through the backend.

Less good:

```py
return {"thing": "maybe", "data": 123}
```

Better:

```py
class AnalysisStatusResponse(BaseModel):
    status: str
    progress_pct: float
    message: str
```

Schemas help with validation, autocomplete, API documentation, frontend
integration, and debugging.

## 10. Railway Deployment

Railway should deploy the backend service from the `backend/` directory.

Expected production command:

```sh
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Variables such as `GOOGLE_API_KEY` should be configured in Railway, not
hardcoded in Python files.

## 11. Development Roadmap

1. Health endpoint `/health`
2. Document upload endpoint
3. Text extraction service
4. Job manager service
5. First pipeline state model
6. `document_analyzer` node
7. `company_sourcing` node
8. `company_research` node
9. `report_writer` node
10. Railway deployment
