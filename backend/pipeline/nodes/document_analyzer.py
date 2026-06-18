import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from services.llm_cache import get_cached_document_analyzer, put_cached_document_analyzer
from models.contract import JudicialContract
from config import GEMINI_MODEL, GOOGLE_API_KEY
from models.pipeline import PipelineState

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a legal expert in EU/French compatition market law and an experienced reader of antitrust enforcement decisions.

You receive the FULL TEXT of a decision(national competition authority, European Commision, national courts, etc.).

Task: produce ONE single JSON object, strictly conformant to the application schema `judicial_contract` (document_id, metadata, sanctioned_parties, infraction, key_extracts, tplf_structured, etc.).

ABSOLUTE RULE — INFORMATION ABSENT FROM THE DOCUMENT:
- You must NEVER invent, guess, or "complete" a value to fill the schema (no fabricated names, amounts, dates, percentages, NACE codes, appeal statuses, precedents, or generic but unsourced wording).
- If a piece of information is NOT explicitly present, or cannot be UNAMBIGUOUSLY inferred from the supplied text, set the JSON value to **null** for that scalar field or sub-object (consistent with the schema: optional fields).
- FORBIDDEN as filler: empty string "", a fake numeric zero, placeholder text, an enum value picked "at random", or a paraphrase of general knowledge not written in the decision.

Enum distinction:
- Use the literal value **"unknown"** ONLY when the text DOES address the topic but does not allow classification (e.g. sector discussed but undecidable between two clusters). If the text does NOT address the topic at all → **null** for that field (not "unknown").

Lists (key_extracts, tables, etc.):
- Every list item must be a quotation or summary strictly anchored in the document.
- If no verifiable item is available: empty list []. Do not add generic items just to "look complete".

tplf_structured (business sections):
1. INFRACTION TYPES — category / subtype / articles: only from the decision; presumptions_and_burden_notes = null if not addressed.
2. INFRACTION DURATION — dates and full_calendar_years_count only if explicitly inferable; otherwise null; methodology_notes factual or null.
3. FINE AMOUNT — total_fines_eur_aggregate and flags only when quantified or stated; fine_magnitude_band null if it cannot be grounded in the text; no "score" or attractiveness vocabulary.
4. PRODUCT/SERVICE AND CORPORATE VICTIMS — strictly populate from the relevant market and buyer profiles as described by the decision; otherwise null / [].
5. GEOGRAPHIC MARKET AND COMPETENT AUTHORITY — booleans and competent authority only if the text supports the conclusion; otherwise null; no investment recommendation.
6. APPEAL STATUS — null sub-fields if the decision says nothing about appeals / finality.
7. ECONOMIC SECTOR — nace_codes_in_decision only if NACE codes appear in the text; otherwise [] or null per schema.
8. FOLLOW-ON PRECEDENTS — only entries sourced from the decision; otherwise [].

FORBIDDEN in any output: ★ symbols, scores, "fundability", "TPLF attractiveness", marks out of 10.

Respond only with a valid JSON object, with no markdown and no commentary outside of JSON."""


def build_document_analyzer_user_prompt(document_id: str, decision_full_text: str) -> str:
  return f"""document_id: {document_id}

Decision text:
---
{decision_full_text}
---"""

async def document_analyzer(state: PipelineState) -> dict:
  text = state.get("decision_full_text")
  if not text or not str(text).strip():
    errs = list(state.get("errors", []))
    errs.append("decision_full_text missing: Node 1 requires the full text of the decision (architecture23.md §5.1).")
    return {"errors": errs, "status": "failed"}
  
  content_hash = (state.get("content_hash") or "").strip()
  cached = get_cached_document_analyzer(content_hash) if content_hash else None
  if cached:
    jc = dict(cached.get("judicial_contract") or {})
    jc["document_id"] = state["document_id"]
    log.info("document_analyzer : cache hit (%s…)", content_hash[:16])
    return {
      "judicial_contract": jc,
      "status": cached.get("status", "sourcing_companies"),
      "content_hash": content_hash,
    }
    
  if not (GOOGLE_API_KEY or "").strip():
    errs = list(state.get("errors", []))
    errs.append("GOOGLE_API_KEY missing: set it in backend/.env or in the environment.")
    return {"errors": errs, "status": "failed"}

  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  ).with_structured_output(JudicialContract)

  doc_id = state["document_id"]
  messages = [
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=build_document_analyzer_user_prompt(doc_id, str(text).strip())),
  ]

  parsed: JudicialContract = await llm.ainvoke(messages)

  # Post-traitement Node 1 (architecture23.md §5.4) : ancrage document_id + validation stricte
  dumped = parsed.model_dump(mode="python")
  dumped["document_id"] = doc_id
  validated = JudicialContract.model_validate(dumped)

  out = {
    "judicial_contract": validated.model_dump(mode="json"),
    "status": "sourcing_companies",
  }
  if content_hash:
    out["content_hash"] = content_hash
    put_cached_document_analyzer(content_hash, {k: v for k, v in out.items() if k != "content_hash"})
  return out