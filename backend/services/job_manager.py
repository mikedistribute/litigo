import asyncio
import hashlib
import io
import json
import logging
from typing import Any, AsyncGenerator, Optional
import uuid

from models.pipeline import AnalysisStatusResponse, JobStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def _jsonable(obj: Any) -> Any:
    """Sérialise récursivement pour snapshot API (Pydantic, listes, dicts)."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)):
        return obj
    return str(obj)

NODE_PROGRESS: dict[str, tuple[JobStatus, float, str]] = {
  "document_analyzer":   (JobStatus.ANALYZING_DOCUMENT,    10.0, "Analyzing the legal document…"),
  "company_sourcing":    (JobStatus.SOURCING_COMPANIES,    28.0, "Identifying potentially harmed companies…"),
  "company_research":    (JobStatus.RESEARCHING_COMPANIES, 48.0, "Running parallel financial research…"),
  "selection_agent":     (JobStatus.SELECTING_COMPANIES,   68.0, "TPLF analysis and shortlist…"),
  "report_writer":       (JobStatus.WRITING_REPORT,        82.0, "Drafting the report…"),
  "document_generator":  (JobStatus.GENERATING_DOCUMENT,  94.0, "Generating the Word document…"),
}

SNAPSHOT_NODES = frozenset(NODE_PROGRESS) | {"document_generator"}

def _extract_text(content: bytes, filename: str) -> str:
  name = (filename or "").lower()
  if name.endswith(".pdf"):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(t for t in pages if t.strip())
  if name.endswith(".docx"):
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
  return content.decode("utf-8", errors="replace")


class JobManager:
  def __init__(self):
    self._documents: dict[str, dict] = {}
    self._jobs: dict[str, dict] = {}

  # -- documents ------------------

  def store_document(self, content: bytes, filename: str) -> str:
    document_id = str(uuid.uuid4())
    content_hash = hashlib.sha256(content).hexdigest()
    self._documents[document_id] = {
      "text": _extract_text(content, filename),
      "content_hash": content_hash,
      "filename": filename
    }
    return document_id
  
  def get_document_text(self, document_id: str) -> Optional[str]:
    entry = self._documents.get(document_id)
    if entry is None:
      return None
    if isinstance(entry, str):
      return entry
    return entry.get("text")

  def get_content_hash(self, document_id: str) -> Optional[str]:
    entry = self._documents.get(document_id)
    if entry is None or isinstance(entry, str):
      return None
    return entry.get("content_hash")
  
  # -- jobs --------------------
  
  async def create_job(self, document_id: str) -> str:
    job_id = str(uuid.uuid4())
    self._jobs[job_id] = {
      "document_id": document_id,
      "status": JobStatus.QUEUED,
      "current_node": None,
      "progress_pct": 0.0,
      "message": "Queued…",
      "output_docx_path": None,
      "output_pdf_path": None,
      "pipeline_snapshot": {},
      "content_hash": None,
      "queue": asyncio.Queue(),
    }
    return job_id

  async def get_status(self, job_id: str) -> AnalysisStatusResponse:
    job = self._jobs.get(job_id)
    if not job:
      return AnalysisStatusResponse(
        status=JobStatus.FAILED,
        progress_pct=0.0,
        message="Job not found",
      )
    return AnalysisStatusResponse(
      status=job["status"],
      current_node=job["current_node"],
      progress_pct=job["progress_pct"],
      message=job["message"],
    )
  
  async def update_status( self, job_id: str, status: JobStatus, message: str = "", current_node: Optional[str] = None, progress_pct: Optional[float] = None) -> None:
    job = self._jobs.get(job_id)
    if not job:
      return
    job["status"] = status
    if message:
      job["message"] = message
    if current_node is not None:
      job["current_node"] = current_node
    if progress_pct is not None:
      job["progress_pct"] = progress_pct

    event_data = json.dumps({
      "status": status.value,
      "message": job["message"],
      "progress": job["progress_pct"],
      "node": job["current_node"],
    })
    await job["queue"].put(f"data: {event_data}\n\n")

  async def stream_events(self, job_id: str) -> AsyncGenerator[str, None]:
    job = self._jobs.get(job_id)
    if not job:
      yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
      return

    # Already finished: flush queue then send current state
    if job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
      q: asyncio.Queue = job["queue"]
      try:
        while True:
          item = q.get_nowait()
          if item is None:
              break
          yield item
      except asyncio.QueueEmpty:
        pass
      yield f"data: {json.dumps({'status': job['status'].value, 'message': job['message'], 'progress': job['progress_pct'], 'node': job['current_node']})}\n\n"
      return

    q = job["queue"]
    while True:
      item = await q.get()
      if item is None:
          break
      yield item

  # ── pipeline ──────────────────────────────────────────────────────────────

  async def run_pipeline(self, job_id: str, document_id: str) -> None:
    from pipeline.graph import build_pipeline

    job = self._jobs.get(job_id)
    if not job:
      return

    text = self.get_document_text(document_id)
    if not text or not text.strip():
      await self.update_status(
          job_id, JobStatus.FAILED, "Document text missing or empty.", progress_pct=0
      )
      await job["queue"].put(None)
      return

    log.info(f"[{job_id[:8]}] Pipeline started — {len(text)} characters extracted")
    graph = build_pipeline()
    ch = self.get_content_hash(document_id) or ""
    job["content_hash"] = ch or None
    initial_state = {
      "document_id": document_id,
      "content_hash": ch,
      "decision_full_text": text,
      "judicial_contract": {},
      "company_reports": [],
      "company_analyses": [],
      "selected_companies": [],
      "selection_rationale": "",
    }

    seen_starts: set[str] = set()
    try:
      async for event in graph.astream_events(initial_state, version="v2"):
        etype = event.get("event", "")
        name = event.get("name", "")

        if etype == "on_chain_start" and name in NODE_PROGRESS and name not in seen_starts:
          seen_starts.add(name)
          status, progress, msg = NODE_PROGRESS[name]
          log.info(f"[{job_id[:8]}] → node START : {name} ({progress:.0f}%)")
          await self.update_status(
              job_id, status, msg, current_node=name, progress_pct=progress
          )

        elif etype == "on_chain_end" and name in NODE_PROGRESS:
          log.info(f"[{job_id[:8]}] ✓ node END   : {name}")

        if etype == "on_chain_end":
          meta = event.get("metadata") or {}
          ev_name = name or meta.get("langgraph_node") or ""
          if ev_name in SNAPSHOT_NODES:
            raw_out = (event.get("data") or {}).get("output")
            if isinstance(raw_out, dict) and raw_out:
              try:
                job["pipeline_snapshot"][ev_name] = _jsonable(raw_out)
              except Exception:
                log.exception("[%s] snapshot failed for node %s", job_id[:8], ev_name)

          if etype == "on_chain_end" and name == "document_generator":
            output = (event.get("data") or {}).get("output") or {}
            docx_path = output.get("output_docx_path")
            if docx_path:
              job["output_docx_path"] = docx_path
              pdf_path = str(docx_path).replace(".docx", ".pdf")
              try:
                from docx2pdf import convert
                convert(docx_path, pdf_path)
                job["output_pdf_path"] = pdf_path
              except Exception:
                pass

          elif etype == "on_chain_error":
            err = str((event.get("data") or {}).get("error", "Unknown error"))
            await self.update_status(
              job_id, JobStatus.FAILED, f"Pipeline error: {err}", progress_pct=0
            )
            await job["queue"].put(None)
            return

      log.info(f"[{job_id[:8]}] Pipeline completed ✓")
      await self.update_status(
        job_id, JobStatus.COMPLETED, "Analysis complete.", progress_pct=100
      )

    except Exception as exc:
      log.error(f"[{job_id[:8]}] Pipeline ERROR : {exc}", exc_info=True)
      await self.update_status(
        job_id, JobStatus.FAILED, f"Error: {exc}", progress_pct=0
      )
    finally:
      await job["queue"].put(None)

job_manager = JobManager()