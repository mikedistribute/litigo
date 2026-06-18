# Node 3 : Recherche approfondie par entreprise
# Entrée : judicial_contract (objet complet Node 1) + entreprise + company_kpis (architecture23.md §6)

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from config import GOOGLE_API_KEY, GEMINI_MODEL
from models.pipeline import CompanyResearchState, PipelineState
from models.reports import CompanyReport
from services.llm_cache import get_cached_company_research, put_cached_company_research
from tools.gemini_grounding import gemini_grounding_search

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert analyst in TPLF (Third Party Litigation Funding) due diligence. You know nothing on your own.

ABSOLUTE RULE: every data point you provide MUST come from a tool call executed in this session.
You are not allowed to use your memory or training data. If you have not called a tool
to obtain a piece of information, set it to null.

AVAILABLE TOOL: gemini_grounding_search — make as many calls as required.

MANDATORY RESEARCH PLAN (5 axes, in this order):

1. IDENTIFICATION & FINANCIAL KPIs
   → Search: "{company} revenue net income market cap 2024 annual report"
   → Search: "{company} ticker ISIN exchange listing"
   → Extract: description (1-2 sentences), countries of operation, ticker, ISIN, revenue, net income, market cap, fiscal year

2. LEGAL PROFILE
   → Search: "{company} legal department general counsel competition law antitrust"
   → Search: "{company} litigation history damages claim competition infringement"
   → Search: "{company} {cartel / infraction mentioned in the prompt} statement press release"
   → Extract: legal team size, GC name, internal antitrust expertise, past litigation, public statements on the cartel

3. EXPOSURE TO THE CARTELIZED MARKET
   → Search: "{company} {cartelized product/market} purchasing supply chain buyer"
   → Search: "{company} operations {countries affected by the infraction}"
   → Extract: role (direct/indirect buyer), active countries within the infraction zones, overlap with the cartel period, products purchased, exposure level

4. CAPACITY TO SUSTAIN A LONG LITIGATION
   → Search: "{company} credit rating Moody S&P Fitch debt"
   → Search: "{company} restructuring financial difficulties bankruptcy"
   → Extract: credit rating, net debt, financial stability, ownership structure, recent restructurings

5. CORPORATE STRUCTURE
   → Search: "{company} parent company subsidiary legal entity group structure"
   → Search: "{company} merger acquisition 2018 2019 2020 2021 2022 2023 2024"
   → Extract: exact legal entity, parent company, subsidiaries in the affected markets, recent M&A, entity continuity

REMINDER: null if not found — never make anything up."""


def _tplf_snippet(judicial_contract: dict[str, Any]) -> str:
  tplf = judicial_contract.get("tplf_structured")
  if not tplf:
    return "(absent from the contract — null or not provided by Node 1)"
  return json.dumps(tplf, ensure_ascii=False, indent=2)


def build_research_prompt(
  company_name: str,
  judicial_contract: dict[str, Any],
  company_kpis: dict[str, Any] | None = None,
) -> str:
  infraction = judicial_contract.get("infraction") or {}
  extracts = judicial_contract.get("key_extracts") or {}
  md = judicial_contract.get("metadata") or {}
  kpis = company_kpis if company_kpis is not None else {}

  buyer_profiles = "\n".join(f"  - {b}" for b in extracts.get("affected_buyer_profiles", []))
  damages = "\n".join(f"  - {d}" for d in extracts.get("damage_quantification", []))

  return f"""You are an analyst specialized in TPLF (Third Party Litigation Funding) due diligence.

TARGET COMPANY: {company_name}

CASE CONTEXT (single source: `judicial_contract` from Node 1):
- Case reference: {md.get("case_reference")}
- Infraction summary (`infraction.summary`): {infraction.get("summary")}
- Type (`infraction.type`): {infraction.get("type")}
- Affected markets (`infraction.affected_markets`): {infraction.get("affected_markets")}
- Period (`infraction.period_start` → `infraction.period_end`): {infraction.get("period_start")} — {infraction.get("period_end")}

Extracts (`key_extracts`):
- Damage quantification:
{damages or "  - (empty or unavailable list)"}
- Buyer profiles:
{buyer_profiles or "  - (empty or unavailable list)"}

TPLF business section (`tplf_structured`):
{_tplf_snippet(judicial_contract)}

KPIs already known for this company (`company_kpis`, may be empty):
{json.dumps(kpis, ensure_ascii=False, indent=2) if kpis else "{{}}"}

TASK: run the 5 research axes described in the system prompt for {company_name}.
Follow the plan in order. For each axis, perform the listed web searches by substituting the placeholders with the real values from the case context above (infraction.type, affected markets, countries, period).
Prioritize 2024 financial data. null if not found — never make anything up."""


async def _run_single_company_research(
  company_name: str,
  judicial_contract: dict[str, Any],
  company_kpis: dict[str, Any],
) -> CompanyReport:
  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  )

  agent = create_react_agent(
    model=llm,
    tools=[gemini_grounding_search],
    response_format=CompanyReport,
  )

  result = await agent.ainvoke(
    {
      "messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
          content=build_research_prompt(company_name, judicial_contract, company_kpis)
        ),
      ]
    },
    config={"recursion_limit": 50},
  )

  return result["structured_response"]


async def company_research_agent(state: CompanyResearchState) -> dict:
  """Une branche map (une entreprise)."""
  company_name = state["company"]
  judicial_contract = state["judicial_contract"]
  company_kpis = state.get("company_kpis") or {}

  report = await _run_single_company_research(company_name, judicial_contract, company_kpis)
  return {"company_reports": [report]}


async def company_research_parallel_node(state: PipelineState) -> dict:
  """Fan-in unique : parallélise les recherches puis agrège les `CompanyReport`."""
  companies = list(state.get("candidate_companies") or [])[:3]
  judicial_contract = state.get("judicial_contract") or {}
  by_name = state.get("company_kpis_by_name") or {}
  content_hash = (state.get("content_hash") or "").strip()

  if not companies:
    return {"company_reports": [], "status": "selecting_companies"}

  if content_hash:
    cached = get_cached_company_research(
      content_hash, judicial_contract, companies, by_name
    )
    if cached and isinstance(cached.get("company_reports"), list):
      raw = cached["company_reports"]
      reports = [CompanyReport.model_validate(r) for r in raw]
      log.info("company_research : cache hit (%s…)", content_hash[:16])
      hit = {
        "company_reports": reports,
        "status": cached.get("status", "selecting_companies"),
      }
      if content_hash:
        hit["content_hash"] = content_hash
      return hit

  tasks = [
    _run_single_company_research(name, judicial_contract, by_name.get(name, {}))
    for name in companies
  ]
  reports: list[CompanyReport] = list(await asyncio.gather(*tasks))
  out = {"company_reports": reports, "status": "selecting_companies"}
  if content_hash:
    out["content_hash"] = content_hash
    put_cached_company_research(
      content_hash,
      judicial_contract,
      list(companies),
      by_name,
      {
        "company_reports": [r.model_dump(mode="json") for r in reports],
        "status": out["status"],
      },
    )
  return out