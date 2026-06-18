# Litigo Product Roadmap

This file lists improvements that would turn the current MVP backend into a real TPLF product.

## Current MVP Scope

The current backend is good enough for a first demo if the goal is to prove the core workflow:

1. Upload a legal decision.
2. Extract structured legal context.
3. Run the agentic TPLF pipeline.
4. Generate a DOCX investment memo.
5. Expose job status, SSE progress, result URLs, and download endpoints.

Known MVP limits:

- Jobs are stored in memory, so they disappear on server restart.
- Uploaded documents and generated reports are local/ephemeral on Railway.
- There is no authentication, account model, or workspace separation.
- No persistent database exists for analysis history.
- PDF conversion may not work in Railway Linux without a LibreOffice-based conversion path.
- The pipeline depends on external LLM calls, so jobs can be slow and may hit provider limits.

## Phase 1 — MVP Hardening

- Add `GET /api/v1/health` checks for required environment variables and runtime dependencies.
- Add structured error responses for failed pipeline steps.
- Persist uploaded files and generated reports in object storage such as Cloudflare R2, S3, or Supabase Storage.
- Persist jobs in Postgres instead of process memory.
- Store pipeline snapshots after each node so users can refresh the page without losing state.
- Add request size limits and accepted file type validation.
- Add background worker execution for long-running analyses instead of in-process background tasks.
- Add retry/backoff handling for Gemini and grounding calls.
- Add deterministic integration tests with mocked LLM responses.

## Phase 2 — Accounts And Workspaces

- Add authentication with Clerk, Auth0, Supabase Auth, or NextAuth.
- Add organizations/workspaces for funds, law firms, and analysts.
- Add roles such as owner, admin, analyst, reviewer, and read-only viewer.
- Scope every document, job, report, and source to a workspace.
- Add audit logs for uploads, analysis starts, report downloads, and user actions.
- Add per-workspace usage limits for documents, tokens, and monthly analyses.

## Phase 3 — TLPF / TPLF Case Workspace

- Add a dossier model for each potential claim opportunity.
- Track case stages: intake, screened, diligence, committee review, outreach, active, rejected.
- Add candidate-company cards with financial KPIs, legal exposure, ranking, and confidence.
- Allow analysts to manually edit candidate companies before running expensive research.
- Add notes, comments, and reviewer approvals.
- Add saved filters for jurisdiction, sector, claim size, limitation risk, and confidence level.
- Add a committee-ready dashboard summarizing top opportunities.

## Phase 4 — Evidence And Auditability

- Store every source used by each agent: decision excerpts, URLs, annual reports, Pappers records, and search results.
- Attach citations to each material claim in company reports and final memos.
- Add a `/citations` endpoint per job or dossier.
- Add source confidence levels and extraction timestamps.
- Add a claim-to-source viewer in the frontend.
- Add hallucination checks that fail the pipeline when required fields have no evidence.
- Add human review status for each key claim.

## Phase 5 — Damages Modeling

- Add configurable damages assumptions: overcharge rate, affected purchase volume, pass-on, limitation period, and interest.
- Add scenario modeling: conservative, base case, aggressive.
- Add estimated claim value ranges per company.
- Add funding economics: expected budget, adverse costs, success probability, funder return, and settlement scenarios.
- Add exportable damages appendix for the investment memo.

## Phase 6 — Data Integrations

- Add official decision feeds from EU and national competition authorities.
- Add Pappers or equivalent company registry integrations.
- Add market data provider integration for ticker, ISIN, exchange, market cap, and financial statements.
- Add document ingestion from annual reports and court decisions.
- Add scheduled monitoring for new antitrust decisions.
- Add duplicate detection across documents and cases.

## Phase 7 — Production Infrastructure

- Move background work to a queue such as Redis Queue, Celery, Dramatiq, or Cloudflare Queues.
- Add Postgres migrations with Alembic.
- Add object storage lifecycle policies for uploaded documents and generated reports.
- Add observability: structured logs, traces, job duration metrics, LLM cost tracking, and alerting.
- Add rate limiting and abuse protection.
- Add CI checks for tests, formatting, import validation, and deployment smoke tests.
- Add staging and production environments.

## Phase 8 — Security And Compliance

- Encrypt sensitive documents at rest.
- Add access-control checks to every report and download endpoint.
- Add signed URLs or authenticated download endpoints.
- Add data retention controls per workspace.
- Add export/delete workflows for customer data.
- Add secrets scanning and dependency vulnerability checks.
- Add legal disclaimers and human-review requirements before external use.

## Suggested Next Product Milestones

1. Frontend MVP: upload, progress view, result page, DOCX download.
2. Persistent jobs and reports in Postgres/object storage.
3. Auth and single-workspace support.
4. Citation capture in company research.
5. Dossier workspace for analysts.
