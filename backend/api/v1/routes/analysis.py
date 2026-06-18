from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.services import llm_cache
from models.pipeline import AnalysisResultResponse, AnalysisStartRequest, AnalysisStartResponse, AnalysisStatusResponse
from services.job_manager import job_manager


router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
  content = await file.read()
  if not content:
    raise HTTPException(status_code=400, detail="Empty file")
  document_id = job_manager.store_document(content, file.filename or "")
  ch = job_manager.get_content_hash(document_id)
  return {"document_id": document_id, "filename": file.filename, "content_hash": ch}

@router.post("/start", response_model=AnalysisStartResponse)
async def start_analysis(req: AnalysisStartRequest, background_tasks: BackgroundTasks):
  if job_manager.get_document_text(req.document_id) is None:
    raise HTTPException(status_code=404, detail="document_id not found - upload the file first")
  job_id = await job_manager.create_job(req.document_id)
  background_tasks.add_task(job_manager.run_pipeline, job_id, req.document_id)
  return AnalysisStartResponse(job_id=job_id, status="queued")

@router.get("/{job_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(job_id: str):
  return await job_manager.get_status(job_id)

@router.get("/{job_id}/result", response_model=AnalysisResultResponse)
async def get_analysis_result(job_id: str):
  job = job_manager._jobs.get(job_id)
  if not job:
    raise HTTPException(status_code=404, detail="Job not found")

  docx_path = job.get("output_docx_path")
  pdf_path = job.get("output_pdf_path")

  snap = job.get("pipeline_snapshot")
  return AnalysisResultResponse(
      report_url_docx=f"/files/{Path(docx_path).name}" if docx_path else None,
      report_url_pdf=f"/files/{Path(pdf_path).name}" if pdf_path else None,
      summary=job.get("message"),
      snapshot=snap if isinstance(snap, dict) and snap else None,
      content_hash=job.get("content_hash"),
  )
  
@router.get("/{job_id}/stream")
async def stream_analysis(job_id: str):
  async def event_generator():
    async for chunk in job_manager.stream_events(job_id):
      yield chunk

  return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  )
  
@router.delete("/cache/{content_hash}")
async def delete_analysis_cache_entry(content_hash: str):
  """Supprime l'entrée disque `analysis_cache/{content_hash}.json` (sorties LLM mémorisées)."""
  try:
    return llm_cache.delete_analysis_cache(content_hash)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e)) from e
  except OSError as e:
    raise HTTPException(status_code=500, detail=str(e)) from e