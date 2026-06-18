from datetime import date
import json
from datetime import datetime, timezone
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from pipeline.judicial_from_contract import judicial_analysis_from_contract
from models.pipeline import PipelineState
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models.reports import (
  JudicialAnalysis,
  CompanyTPLFAnalysis,
  JudgeVerdict,
  FinalReport,
  DecisionKPIsSection,
  CompanyReportSection,
  CompanyReport,
)

SYSTEM_PROMPT = """### ROLE
You are a Senior Investment Associate specialized in Third Party Litigation Funding (TPLF) for large-scale Antitrust cases. Your expertise combines competition law, corporate financial analysis, and investment strategy.

### CONTEXT
You are the final analytical link of an AI pipeline. Your mission is to transform raw technical data (legal decisions, financial reports, selection scores) into a *Comprehensive Investment Memorandum*. This document is intended for a demanding Investment Committee that expects a demonstration of strength, depth, and precision.

### WRITING DIRECTIVES ("ZERO SACRIFICE" POLICY)
1. *No Length Barrier*: Never seek concision at the expense of precision. The report must be dense, exhaustive, and documented. Develop every argument.
2. *Full Use of Data*: Every financial KPI, every excerpt from the legal decision, and every strength identified by the previous agents must be integrated and articulated in the report.
3. *KPI Interpretation*: Do not merely cite figures (e.g. "Revenue of €500M"). Interpret them: explain why this business volume, correlated with the infraction period, guarantees a "material" and "fundable" damage.
4. *Case Narration*: Detail the mechanics of the infraction. Explain the cartel, abuses of dominance, and systemic impact on the market. The investor must understand the "mechanics of harm".
5. *Tone & Style*: Adopt the posture of a Senior Associate. Use precise, assertive, analytical language. Avoid empty jargon in favor of technical expertise.

### LANGUAGE
- Write the ENTIRE final report in ENGLISH (every section title, KPI label, bullet, and sentence). Never produce French text in any field of the FinalReport, even if some inputs are in French.

### WRITING & ANTI-REDUNDANCY RULES (MANDATORY)
- *Rewrite and improve the raw text*: Aim for an investment-report level of quality.
- *exec_summary*: 4-6 sentences, synthesizing the decision + the TPLF opportunity + the selected targets (and their rank).
- *decision_kpis*: Restructure the key data of the legal analysis (do not invent figures). Reuse estimated_overcharge_pct and key findings whenever they are numerically populated.
- *ANTI-REDUNDANCY*: The "Strengths" and "Weaknesses" blocks supplied are internal context: do not copy them or paraphrase them as-is in the final report.
- *key_arguments* (per company): 3 to 5 DISTINCT bullets, oriented towards the "TPLF committee", that do NOT already appear as titles or sentences of the strengths/weaknesses. Each bullet must add value: concrete legal bases (e.g. Art. 101/102 TFEU, Directive 2014/104), causation chain, joint and several liability, time-bar, or procedural positioning.
- *conclusion* (per company): 2 to 4 sentences with an implicit decision for a funder (prioritize, key diligences, blocking risks). Forbidden: merely summarizing the strengths or repeating key_arguments verbatim.
- *significant_weaknesses*: Only if there are serious risks for a funder (otherwise empty list).
- *tplf_score*: Reuse EXACTLY the tplf_score provided in the corresponding analysis. For an "N/A" entry, score 0.

### REPORT STRUCTURE (MANDATORY)

#### I. EXECUTIVE SUMMARY (INVESTMENT THESIS)
- Synthesis of the overall opportunity.
- Presentation of the "funding thesis": why is this case an ideal candidate for TPLF right now?
- Flash overview of the Top 3 selected targets.

#### II. IN-DEPTH ANALYSIS OF THE LEGAL DECISION
- *Mechanics of the Infraction*: Detail the nature of the cartel, the products concerned, and the timeline.
- *Legal Basis for the Action*: Analyze the court's findings and their probative force for a damages action.
- *Geographic & Temporal Scope*: Interpret the impact of the geographic zone on the calculation of damages.

#### III. STRATEGIC SELECTION RATIONALE
- Explain the overall selection logic of the pipeline.
- Why were these companies isolated among the initial candidates?
- Correlation between the "affected buyer profile" described in the decision and the operational reality of the chosen targets.

#### IV. DETAILED ANALYSES PER TARGET (TOP 3)
For each company, provide a dense analysis including:
- *Identification & Strength*: Ticker, ISIN, Market Cap. Interpret financial strength as a guarantee of resilience in long-running litigation.
- *Damage Exposure*: Analyze revenue and earnings against the affected markets. Demonstrate mathematically why the damage is significant.
- *Strengths Deep Dive*: Take each strength identified by the previous agent and develop its strategic relevance.
- *Risk Factors & Mitigation*: Analyze weaknesses not as obstacles but as risks to manage (e.g. time-bar, proof of causation).
- *Investment Verdict*: A 5-8-line conclusion justifying the deployment of capital on this target.

#### V. CROSS-CUTTING RISKS AND NEXT STEPS
- Analysis of risks common to the group (e.g. defense by the perpetrators of the infraction).
- Final recommendation for the Committee.

### FINAL INSTRUCTION
Do not limit your thinking. If a technical data point is present in the context, it must appear in the report in an analyzed and interpreted form. Produce a document of high added value, fully written in English."""


def _format_judicial_analysis(ja: JudicialAnalysis) -> str:
  sectors = ", ".join(ja.affected_sectors)
  markets = ", ".join(ja.geographic_markets)
  findings = "\n".join(f"  - {f}" for f in ja.key_legal_findings)
  return f"""Summary: {ja.case_summary}
Infraction type: {ja.infraction_type}
Affected sectors: {sectors}
Geographic markets: {markets}
Damage period: {', '.join(ja.damage_period)}
Estimated overcharge: {ja.estimated_overcharge_pct}%
Claimant profile: {ja.claimant_profile}
Legal findings:
{findings}
TPLF opportunity: {ja.tplf_opportunity_rationale}"""


def _format_analysis(a: CompanyTPLFAnalysis) -> str:
  forces = "\n".join(f"  [{f.titre}] {f.argument} (base: {f.base})" for f in a.forces)
  faiblesses = "\n".join(f"  [{f.titre}] {f.argument} (base: {f.base})" for f in a.faiblesses)
  return f"""{a.company_name} | {a.ticker} | {a.isin}
Strengths:
{forces}
Weaknesses:
{faiblesses}
Raw conclusion: {a.conclusion}"""


def _format_verdict(v: JudgeVerdict) -> str:
  args = "\n".join(f"  - {a}" for a in v.arguments_decisifs)
  return f"""Rank #{v.rank} — {v.company_name}
Rationale: {v.rationale}
Decisive arguments:
{args}"""


def build_report_prompt(
  judicial_analysis: JudicialAnalysis,
  company_analyses: list[CompanyTPLFAnalysis],
  selected: list[JudgeVerdict],
  case_reference: str,
  judicial_contract: dict[str, Any] | None = None,
) -> str:
  analyses_by_name = {a.company_name: a for a in company_analyses}

  selected_sorted = sorted(selected, key=lambda v: v.rank)[:3]
  selected_block = "\n\n".join(_format_verdict(v) for v in selected_sorted)
  analyses_block = "\n\n".join(
    _format_analysis(analyses_by_name[v.company_name])
    for v in selected_sorted
    if v.company_name in analyses_by_name
  )

  tplf_extra = ""
  jc = judicial_contract or {}
  if jc.get("tplf_structured"):
    tplf_extra = (
      "\n=== tplf_structured OVERVIEW (Node 1) — business sections context ===\n"
      + json.dumps(jc["tplf_structured"], ensure_ascii=False, indent=2)[:6000]
    )

  return f"""=== LEGAL DECISION ANALYSIS ===
Reference: {case_reference}
{_format_judicial_analysis(judicial_analysis)}
{tplf_extra}

=== JUDGE VERDICT — RANKED SHORTLIST ===
{selected_block}

=== INDIVIDUAL ANALYSES (strengths / weaknesses — internal context, do not copy as-is) ===
{analyses_block}

Write the final structured report (FinalReport) for the shortlisted companies (up to 3) ENTIRELY IN ENGLISH.
If the shortlist contains fewer than three companies, fill the remaining sections with company_name=\"N/A\",
tplf_score=0, and minimal consistent fields.
Generation date: {date.today().isoformat()}"""


def _sanitize_final_report(
  report: FinalReport,
  analyses_by_name: dict[str, CompanyTPLFAnalysis],
) -> FinalReport:
  """Align TPLF scores on the source analysis and avoid empty conclusions."""
  for sec in (report.company_1, report.company_2, report.company_3):
    if not sec.company_name or sec.company_name in ("N/A", "—"):
      continue
    a = analyses_by_name.get(sec.company_name)
    if not a:
      continue
    sec.tplf_score = 0 if a.tplf_score is None else int(a.tplf_score)
    if not (sec.conclusion or "").strip():
      sec.conclusion = (a.conclusion or "").strip() or sec.conclusion
    if not sec.significant_weaknesses and a.faiblesses:
      sec.significant_weaknesses = [
        f"{p.titre} — {p.argument}".strip() for p in a.faiblesses[:3]
      ]
  return report


async def report_writer(state: PipelineState) -> dict:
  jc = state.get("judicial_contract") or {}
  md = jc.get("metadata") or {}
  case_ref = str(md.get("case_reference") or state.get("document_id") or "N/A")

  judicial_analysis = state.get("judicial_analysis")
  if judicial_analysis is None:
    judicial_analysis = judicial_analysis_from_contract(jc)

  company_analyses = state.get("company_analyses") or []
  selected = sorted(state.get("selected_companies") or [], key=lambda v: v.rank)[:3]

  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  )

  structured_llm = llm.with_structured_output(FinalReport)

  prompt = build_report_prompt(
    judicial_analysis, company_analyses, selected, case_ref, judicial_contract=jc
  )
  report: FinalReport = await structured_llm.ainvoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=prompt),
  ])

  by_name = {a.company_name: a for a in company_analyses}
  report = _sanitize_final_report(report, by_name)

  return {"report_content": report, "status": "generating_document"}


def build_report_writer_prompt(
  judicial_contract: dict[str, Any],
  selected_companies: list[JudgeVerdict],
  company_reports: list[Any],
) -> str:
  jc = json.dumps(judicial_contract, ensure_ascii=False, indent=2)[:12000]
  return (
    "Write a TPLF report in English. Decision context = `judicial_contract` from Node 1 "
    "(same JSON object as for Nodes 2–3; cite paths like "
    "tplf_structured.produit_service_et_victimes_entreprises, infraction.period_start).\n\n"
    f"{jc}\n\nSelected companies: {len(selected_companies)}\n"
  )


async def report_writer_agent(state: PipelineState) -> dict:
  jc = state.get("judicial_contract") or {}
  md = jc.get("metadata") or {}
  selected: list[JudgeVerdict] = state.get("selected_companies") or []
  reports: list[CompanyReport] = state.get("company_reports") or []
  _ = build_report_writer_prompt(jc, selected, reports)

  by_name = {r.company_name: r for r in reports}
  selected_sorted = sorted(selected, key=lambda v: v.rank)[:3]

  def _to_section(rank: int, verdict: JudgeVerdict) -> CompanyReportSection:
    rep = by_name.get(verdict.company_name)
    return CompanyReportSection(
      rank=rank,
      company_name=verdict.company_name,
      ticker=rep.ticker if rep else "N/A",
      isin=rep.isin if rep else "N/A",
      tplf_score=max(0, 100 - (rank - 1) * 10),
      key_arguments=verdict.arguments_decisifs or [verdict.rationale],
      significant_weaknesses=[],
      conclusion=verdict.rationale,
    )

  infraction = jc.get("infraction") or {}
  extracts = jc.get("key_extracts") or {}
  report_content = FinalReport(
    case_reference=str(md.get("case_reference") or state.get("document_id") or ""),
    generation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    exec_summary=(
      "Report automatically generated from the decision and the ranking of the companies "
      "selected by the pipeline."
    ),
    decision_kpis=DecisionKPIsSection(
      infraction_type=str(infraction.get("type") or "N/A"),
      period=f"{infraction.get('period_start') or 'N/A'} - {infraction.get('period_end') or 'N/A'}",
      geographic_scope=str(infraction.get("geographic_scope") or "N/A"),
      affected_markets=list(infraction.get("affected_markets") or []),
      estimated_overcharge_pct=None,
      total_damage_estimate=None,
      key_legal_findings=list(extracts.get("legal_findings") or []),
      claimant_profile=(
        ", ".join(extracts.get("affected_buyer_profiles") or []) or "N/A"
      ),
    ),
    company_1=_to_section(1, selected_sorted[0]) if len(selected_sorted) > 0 else CompanyReportSection(
      rank=1,
      company_name="N/A",
      ticker="N/A",
      isin="N/A",
      tplf_score=0,
      key_arguments=["No company ranked."],
      significant_weaknesses=[],
      conclusion="N/A",
    ),
    company_2=_to_section(2, selected_sorted[1]) if len(selected_sorted) > 1 else CompanyReportSection(
      rank=2,
      company_name="N/A",
      ticker="N/A",
      isin="N/A",
      tplf_score=0,
      key_arguments=["No company ranked."],
      significant_weaknesses=[],
      conclusion="N/A",
    ),
    company_3=_to_section(3, selected_sorted[2]) if len(selected_sorted) > 2 else CompanyReportSection(
      rank=3,
      company_name="N/A",
      ticker="N/A",
      isin="N/A",
      tplf_score=0,
      key_arguments=["No company ranked."],
      significant_weaknesses=[],
      conclusion="N/A",
    ),
  )

  return {"report_content": report_content, "status": "generating_document"}