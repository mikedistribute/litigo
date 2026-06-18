from __future__ import annotations

import asyncio
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from models.pipeline import PipelineState
from config import GOOGLE_API_KEY, GEMINI_MODEL
from models.reports import CompanyReport, CompanyTPLFAnalysis
from .judge_agent import judge_agent

SYSTEM_PROMPT = """You are a Third Party Litigation Funding (TPLF) expert specialized in antitrust damages claims.

Your mission: produce an in-depth, documented analysis of ONE company as a potential claimant in an antitrust action.

ABSOLUTE RULE: every argument MUST cite its base (data extracted from the research report or excerpts from the legal decision). Do not produce any argument without an explicit source.

THE ANALYSIS MUST COVER 5 MANDATORY DIMENSIONS (strengths AND weaknesses for each when relevant):

1. EXPOSURE TO THE CARTELIZED MARKET
   - Is the company a direct or indirect buyer of the cartelized product/service?
   - Geographic presence in the infraction zones during the relevant period?
   - Do the products purchased correspond to the cartelized products?
   - Estimated exposure level (strong / moderate / weak / unknown)

2. LEGAL PROFILE
   - Ability of the in-house legal team to bring or coordinate a complex action
   - Existence of internal antitrust expertise or proven recourse to specialized counsel
   - History of significant litigation (experience with long and complex disputes)
   - Public statements or actions already taken on this cartel or similar cases

3. CAPACITY TO SUSTAIN A LONG LITIGATION (3-7 years)
   - Financial strength: credit rating, net debt, profitability, stability
   - Ownership structure: decision-making independence to start a claim
   - Absence of restructuring or fragility that could jeopardize litigation continuity

4. CORPORATE STRUCTURE & LEGAL STANDING
   - Precise legal entity that could carry the claim (holding vs. operating subsidiary)
   - Recent M&A possibly affecting claim rights (asset sales, absorption)
   - Continuity of the entity from the infraction period to today

5. POTENTIAL DAMAGE MAGNITUDE
   - Financial size (revenue, market cap) → order of magnitude of the overcharge potentially borne
   - Fit with the buyer profile described in the legal decision
   - Qualitative damage estimate where the data allows

EXPECTED OUTPUT FORMAT:
- forces: 6 to 10 points (TPLFPoint: short title, developed argument, precise base)
- faiblesses: 4 to 6 points (TPLFPoint: short title, developed argument, precise base)
- conclusion: 5 to 8 sentences delivering a clear, reasoned judgment on the overall viability of the claim"""


def _format_report(r: CompanyReport) -> str:
  lines = [
    f"Name: {r.company_name}",
    f"Ticker / ISIN: {r.ticker} / {r.isin}",
    f"Exchange: {r.exchange}",
  ]
  if r.description:
    lines.append(f"Description: {r.description}")
  if r.countries:
    lines.append(f"Countries of operation: {', '.join(r.countries)}")
  if r.revenue_eur is not None:
    lines.append(f"Revenue: {r.revenue_eur:,.0f} EUR ({r.fiscal_year})")
  if r.net_income_eur is not None:
    lines.append(f"Net income: {r.net_income_eur:,.0f} EUR ({r.fiscal_year})")
  if r.market_cap_eur is not None:
    lines.append(f"Market cap: {r.market_cap_eur:,.0f} EUR")

  if r.legal_profile:
    lp = r.legal_profile
    lines.append("\n[LEGAL PROFILE]")
    if lp.legal_team_size:
      lines.append(f"  Legal team size: {lp.legal_team_size}")
    if lp.general_counsel:
      lines.append(f"  General Counsel: {lp.general_counsel}")
    if lp.antitrust_expertise_internal is not None:
      lines.append(f"  Internal antitrust expertise: {'Yes' if lp.antitrust_expertise_internal else 'No'}")
    if lp.past_litigation_highlights:
      lines.append("  Past litigation: " + " ; ".join(lp.past_litigation_highlights))
    if lp.antitrust_claims_history:
      lines.append("  Antitrust claims history: " + " ; ".join(lp.antitrust_claims_history))
    if lp.public_statements_on_cartel:
      lines.append(f"  Statements on the cartel: {lp.public_statements_on_cartel}")

  if r.market_exposure:
    me = r.market_exposure
    lines.append("\n[EXPOSURE TO THE CARTELIZED MARKET]")
    if me.buyer_role:
      lines.append(f"  Buyer role: {me.buyer_role}")
    if me.geographies_in_affected_markets:
      lines.append(f"  Geographies within infraction zones: {', '.join(me.geographies_in_affected_markets)}")
    if me.activity_overlap_with_cartel_period:
      lines.append(f"  Overlap with cartel period: {me.activity_overlap_with_cartel_period}")
    if me.affected_products_purchased:
      lines.append("  Cartelized products purchased: " + ", ".join(me.affected_products_purchased))
    if me.exposure_level:
      lines.append(f"  Exposure level: {me.exposure_level}")

  if r.litigation_capacity:
    lc = r.litigation_capacity
    lines.append("\n[LITIGATION CAPACITY]")
    if lc.credit_rating:
      lines.append(f"  Credit rating: {lc.credit_rating}")
    if lc.net_debt_eur is not None:
      lines.append(f"  Net debt: {lc.net_debt_eur:,.0f} EUR")
    if lc.financial_stability_assessment:
      lines.append(f"  Financial stability: {lc.financial_stability_assessment}")
    if lc.ownership_structure:
      lines.append(f"  Ownership structure: {lc.ownership_structure}")
    if lc.recent_restructurings:
      lines.append("  Recent restructurings: " + " ; ".join(lc.recent_restructurings))

  if r.corporate_structure:
    cs = r.corporate_structure
    lines.append("\n[CORPORATE STRUCTURE]")
    if cs.exact_legal_entity:
      lines.append(f"  Exact legal entity: {cs.exact_legal_entity}")
    if cs.parent_company:
      lines.append(f"  Parent company: {cs.parent_company}")
    if cs.relevant_subsidiaries:
      lines.append("  Relevant subsidiaries: " + ", ".join(cs.relevant_subsidiaries))
    if cs.recent_ma_activity:
      lines.append("  Recent M&A: " + " ; ".join(cs.recent_ma_activity))
    if cs.entity_continuity_note:
      lines.append(f"  Entity continuity: {cs.entity_continuity_note}")

  return "\n".join(lines)


def _format_contract(judicial_contract: dict) -> str:
  infraction = judicial_contract.get("infraction", {})
  extracts = judicial_contract.get("key_extracts", {})
  metadata = judicial_contract.get("metadata", {})

  damage = "\n".join(f"  - {d}" for d in extracts.get("damage_quantification", []))
  buyers = "\n".join(f"  - {b}" for b in extracts.get("affected_buyer_profiles", []))
  geo = "\n".join(f"  - {g}" for g in extracts.get("geographic_scope_details", []))

  return f"""Reference: {metadata.get('case_reference', 'N/A')} — {metadata.get('court', 'N/A')} ({metadata.get('decision_date', 'N/A')})
Infraction: {infraction.get('type', 'N/A')}
Affected markets: {', '.join(infraction.get('affected_markets', []))}
Geographic scope: {infraction.get('geographic_scope', 'N/A')}
Period: {infraction.get('period_start', 'N/A')} - {infraction.get('period_end', 'N/A')}
Summary: {infraction.get('summary', 'N/A')}

Damage quantification:
{damage}

Affected buyer profiles:
{buyers}

Detailed geographic scope:
{geo}"""


def build_analysis_prompt(judicial_contract: dict, company_report: CompanyReport) -> str:
  return f"""=== LEGAL DECISION ===
{_format_contract(judicial_contract)}

=== COMPANY DATA (from web research) ===
{_format_report(company_report)}

Produce the in-depth TPLF analysis for this company by covering the 5 dimensions in the system prompt.
Strengths (6-10 points), weaknesses (4-6 points), detailed conclusion (5-8 sentences delivering a clear judgment on viability).
Every argument must cite its precise base in the data above."""


class CompanySelectionState(dict):
  """Minimal state for a per-company run."""
  pass


async def _analyze_single_company(state: dict) -> dict:
  """TPLF analysis for a single company (compat with legacy tests)."""
  judicial_contract = state["judicial_contract"]
  company_report: CompanyReport = state["company_report"]

  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  )

  structured_llm = llm.with_structured_output(CompanyTPLFAnalysis)

  prompt = build_analysis_prompt(judicial_contract, company_report)
  analysis: CompanyTPLFAnalysis = await structured_llm.ainvoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=prompt),
  ])

  return {"company_analyses": [analysis]}


JUDGE_SYSTEM_PROMPT = """You are a senior investment manager at a TPLF (Third Party Litigation Funding) fund specialized in European antitrust litigation. You decide which potential claimants deserve to be funded.

You are given individual analyses of N companies that are candidates for an antitrust damages claim (follow-on action, after a decision by the European Commission or a national competition authority).

━━━ MISSION ━━━
Select the 3 best funding targets among the analyzed companies.
Reason like an investment committee: each decision commits millions of euros and several years of litigation. Be rigorous, comparative, and discriminating.

━━━ PRE-SCREEN — ABSOLUTE DISQUALIFIERS ━━━
Eliminate up-front any company presenting one of the following situations:
  DQ1 — Membership in the group of perpetrators of the infraction (absolute conflict of interest)
  DQ2 — Certain time-bar under the applicable jurisdiction, with no possibility of a late discovery date
  DQ3 — Claim rights fully transferred to a third party via M&A (the current target has no standing)
  DQ4 — Total absence of exposure: neither geographies, nor period, nor products match

━━━ SCORING GRID — 100 POINTS MAXIMUM ━━━

  A. CARTEL EXPOSURE (30 pts)
   • Direct buyer of the cartelized products/services in the relevant geographies → 30 pts max
   • Indirect buyer (passing-on defense possible) → -8 pts penalty
   • Activity period covering the infraction period → required for any score > 15
   • Products purchased matching the cartelized products exactly → +5 pts bonus
   • Exposure level rated "strong" in the analysis → required for score A > 22

  B. ESTIMABLE DAMAGE MAGNITUDE (25 pts)
   • Revenue or purchase volume in affected markets × estimated overcharge from the decision → potential ticket
   • Potential ticket > 50M EUR → 25 pts ; 10-50M EUR → 15 pts ; 1-10M EUR → 8 pts ; < 1M EUR → 0 pt
   • Explicit fit with the buyer profile described in the decision → +3 pts bonus
   • Financial data insufficient to estimate damage → -10 pts penalty

  C. FINANCIAL STRENGTH & FUNDER ATTRACTIVENESS (20 pts)
   • Market cap or revenues allowing a 3-7-year litigation without weakening the entity → 20 pts max
   • Confirmed financial stability (no restructuring, decent rating) → required for score C > 12
   • Independent ownership structure (autonomous decision-making) → +3 pts bonus
   • Proven financial fragility, restructuring under way → -8 pts penalty

  D. LEGAL STANDING & FEASIBILITY (15 pts)
   • Precise legal entity clearly identified, able to carry the claim → 15 pts max
   • Claim rights not compromised by M&A, divestitures, or absorption → required for score D > 8
   • Confirmed entity continuity from the infraction period to today → +3 pts bonus
   • Uncertain time-bar (discovery date to be argued) → -3 pts

  E. ENGAGEMENT PROFILE (10 pts)
   • History of significant litigation showing appetite for disputes → 10 pts max
   • Internal antitrust expertise or proven recourse to specialized counsel → +3 pts bonus
   • No known litigation history → 3 pts max

━━━ COMPARISON METHOD ━━━
1. Pre-screen: identify disqualified companies (DQ1-DQ4) and put them in `eliminated`.
2. Scoring: for each non-disqualified company, mentally compute A+B+C+D+E.
3. Ranking: the 3 highest scores form the top 3.
4. Tie-break: priority to criterion A (exposure), then B (damage), then D (standing).

━━━ OUTPUT FORMAT ━━━
For each selected company (rank 1 to 3):
  • rationale: 3-4 sentences — why this company is fundable, which criteria set it apart
  • arguments_decisifs: 5-7 precise points, quantified when possible, pulled directly from the analyses
  — at least 1 point on exposure (A), 1 on estimated damage (B), 1 on financial strength (C)
  — if two companies are close, include 1 point that explicitly differentiates them

global_commentary: selection synthesis (4-6 sentences) — overall logic, companies discarded and the main reason for each, remarks on the quality of the case."""


def _build_judge_prompt(judicial_contract: dict, analyses: list[CompanyTPLFAnalysis]) -> str:
  infraction = judicial_contract.get("infraction", {})
  extracts = judicial_contract.get("key_extracts", {})
  metadata = judicial_contract.get("metadata", {})

  overcharge = extracts.get("estimated_overcharge_pct") or infraction.get("estimated_overcharge_pct")
  buyers = extracts.get("affected_buyer_profiles", [])
  damage_q = extracts.get("damage_quantification", [])
  geo_details = extracts.get("geographic_scope_details", [])

  decision_block = (
    f"Reference: {metadata.get('case_reference', 'N/A')} | "
    f"Court: {metadata.get('court', 'N/A')} ({metadata.get('decision_date', 'N/A')})\n"
    f"Infraction type: {infraction.get('type', 'N/A')}\n"
    f"Affected markets: {', '.join(infraction.get('affected_markets', []))}\n"
    f"Geographic scope: {infraction.get('geographic_scope', 'N/A')}\n"
    f"Infraction period: {infraction.get('period_start', 'N/A')} → {infraction.get('period_end', 'N/A')}\n"
    f"Estimated overcharge: {overcharge if overcharge else 'not quantified in the decision'}\n"
    f"Buyer profiles targeted by the decision: {'; '.join(buyers) if buyers else 'N/A'}\n"
    f"Damage quantification (decision): {'; '.join(damage_q) if damage_q else 'N/A'}\n"
    f"Geographic detail: {'; '.join(geo_details) if geo_details else 'N/A'}"
  )

  analyses_text = []
  for a in analyses:
    forces = "\n".join(f"   + [{f.titre}] {f.argument}  →  base: {f.base}" for f in a.forces)
    faiblesses = "\n".join(f"   - [{f.titre}] {f.argument}  →  base: {f.base}" for f in a.faiblesses)
    analyses_text.append(
      f"┌─ {a.company_name} ({a.ticker} | {a.isin}) — analyst score: {a.tplf_score}/100\n"
      f"│  Strengths:\n{forces}\n"
      f"│  Weaknesses:\n{faiblesses}\n"
      f"│  Analyst conclusion: {a.conclusion}\n"
      f"└────────────────────────────"
    )

  analyses_block = "\n\n".join(analyses_text) if analyses_text else "(no analysis available)"

  return (
    f"━━━ REFERENCE LEGAL DECISION ━━━\n{decision_block}\n\n"
    f"━━━ INDIVIDUAL ANALYSES ({len(analyses)} candidate companies) ━━━\n{analyses_block}\n\n"
    "━━━ INSTRUCTION ━━━\n"
    "1. Apply the pre-screen (DQ1-DQ4) — list disqualified companies in `eliminated`.\n"
    "2. For the remaining companies, apply the A+B+C+D+E grid and pick the top 3.\n"
    "3. Produce a structured verdict for each selected company (rationale + arguments_decisifs).\n"
    "4. Write the global_commentary: selection logic, discarded companies and main reason for each.\n"
    "Your arguments_decisifs must be anchored in the analyses above, never invented."
  )


async def selection_agent(state: PipelineState) -> dict:
  # Legacy mode: a single company report -> output `company_analyses`
  if state.get("company_report") is not None:
    return await _analyze_single_company(state)

  # Graph mode: LLM TPLF analysis for each researched company (≤3), then judge top 3
  reports: list[CompanyReport] = state.get("company_reports") or []
  jc = state.get("judicial_contract") or {}

  if not reports:
    return {
      "company_analyses": [],
      "selected_companies": [],
      "selection_rationale": "No candidate company after research.",
      "status": "writing_report",
    }

  tasks = [
    _analyze_single_company({"judicial_contract": jc, "company_report": r})
    for r in reports
  ]
  parts = await asyncio.gather(*tasks)
  all_analyses: list[CompanyTPLFAnalysis] = []
  for p in parts:
    all_analyses.extend(p["company_analyses"])

  judge_state: dict[str, Any] = {**dict(state), "company_analyses": all_analyses}
  judge_result = await judge_agent(judge_state)  # type: ignore[arg-type]

  return {
    "company_analyses": all_analyses,
    "selected_companies": judge_result["selected_companies"],
    "selection_rationale": judge_result["selection_rationale"],
    "status": "writing_report",
  }