from enum import Enum
import operator
from typing import Annotated, Any, NotRequired, Optional, TypedDict

from pydantic import BaseModel

from models.reports import (
  CompanyReport, 
  CompanyTPLFAnalysis, 
  FinalReport, 
  JudgeVerdict, 
  JudicialAnalysis, 
  ReportContent, 
  SelectedCompany
)

class JobStatus(str, Enum):
  QUEUED = "queued"
  ANALYZING_DOCUMENT = "analyzing_document"
  SOURCING_COMPANIES = "sourcing_companies"
  RESEARCHING_COMPANIES = "researching_companies"
  SELECTING_COMPANIES = "selecting_companies"
  WRITING_REPORT = "writing_report"
  GENERATING_DOCUMENT = "generating_document"
  COMPLETED = "completed"
  FAILED = "failed"


class AnalysisStartRequest(BaseModel):
  document_id: str


class AnalysisStartResponse(BaseModel):
  job_id: str
  status: str


class AnalysisStatusResponse(BaseModel):
  status: JobStatus
  current_node: Optional[str] = None
  progress_pct: float
  message: str


class AnalysisResultResponse(BaseModel):
  report_url_docx: Optional[str] = None
  report_url_pdf: Optional[str] = None
  summary: Optional[str] = None
  snapshot: Optional[dict[str, Any]] = None
  content_hash: Optional[str] = None
  
class PipelineState(TypedDict):
  # Entrée pipeline (ARCHITECTURE (2).md + architecture23.md)
  document_id: str
  # Empreinte SHA-256 du fichier uploadé (cache LLM par PDF)
  content_hash: NotRequired[str]
  # Texte intégral décision — obligatoire pour Node 1 (architecture23.md §5.1)
  decision_full_text: NotRequired[str]
  # Sortie Node 1 et entrée unique Node 2 / 3 (architecture23.md)
  judicial_contract: dict
  # Synthèse KPI dérivée du contrat (optionnel ; sinon dérivée dans report_writer)
  judicial_analysis: NotRequired[JudicialAnalysis]

  # Node 2
  candidate_companies: NotRequired[list[str]]

  # Node 3 — fan-out/fan-in, merge via operator.add
  company_reports: Annotated[list[CompanyReport], operator.add]

  # Node 4 — fan-out/fan-in, une analyse par entreprise
  company_analyses: Annotated[list[CompanyTPLFAnalysis], operator.add]

  # KPIs optionnels par entreprise pour Node 3 (architecture23.md §6)
  company_kpis_by_name: NotRequired[dict[str, dict]]

  # Node 5 — LLM as judge, sélection finale top 3
  selected_companies: list[JudgeVerdict]
  selection_rationale: str

  # Compat legacy (anciens tests/scripts)
  selected_companies_legacy: NotRequired[list[SelectedCompany]]
  report_content_legacy: NotRequired[ReportContent]

  # Node 6 / 7
  report_content: FinalReport

  # Node 6
  output_docx_path: NotRequired[str]
  output_pdf_path: NotRequired[str]

  # Metadata
  status: NotRequired[str]
  errors: NotRequired[list[str]]


class CompanyResearchState(TypedDict):
  company: str
  judicial_contract: dict
  company_kpis: NotRequired[dict]
  company_reports: Annotated[list[CompanyReport], operator.add]