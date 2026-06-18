import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.pipeline import PipelineState
from models.reports import CompanyTPLFAnalysis, JudgeOutput
from config import GOOGLE_API_KEY, GEMINI_MODEL

SYSTEM_PROMPT = """You are an antitrust-focused TPLF (Third Party Litigation Funding) investment committee.

You are given the in-depth individual analyses of several companies that are candidates for a damages claim.
Each analysis was produced independently by an expert agent and covers 5 dimensions: exposure to the cartelized market, legal profile, capacity to sustain the litigation, corporate structure, and potential damage magnitude.

Your mission: act as an impartial judge and rank the BEST targets for TPLF (at most 3).

SELECTION CRITERIA (in order of priority):
1. Confirmed exposure — direct/indirect buyer clearly identified, geographic and temporal presence within the infraction perimeter
2. Estimable damage magnitude — financial size + exposure level = capacity to claim a significant damage
3. Solid legal standing — well-identified entity, ensured continuity, claim rights not compromised by M&A
4. Capacity to sustain the litigation — financial strength, favorable ownership structure, absence of fragility
5. Legal profile — team able to coordinate a complex action
6. Absence of absolute conflict — the company is not a co-perpetrator or accomplice of the infraction

RULE: justify every choice by quoting the precise arguments of the analyses. If two companies are comparable, explicitly state what differentiates them dimension by dimension."""


def _format_analysis(a: CompanyTPLFAnalysis) -> str:
  forces = "\n".join(
    f"  [{f.titre}] {f.argument} (base: {f.base})" for f in a.forces
  )
  faiblesses = "\n".join(
    f"  [{f.titre}] {f.argument} (base: {f.base})" for f in a.faiblesses
  )
  return f"""--- {a.company_name} ---
Ticker: {a.ticker} | ISIN: {a.isin}
Strengths:
{forces}
Weaknesses:
{faiblesses}
Conclusion: {a.conclusion}"""


def build_judge_prompt(analyses: list[CompanyTPLFAnalysis]) -> str:
  all_analyses = "\n\n".join(_format_analysis(a) for a in analyses)
  k = min(3, len(analyses))
  return f"""Here are the TPLF analyses of {len(analyses)} candidate companies:

{all_analyses}

Compare these companies along the 5 analysis dimensions and select the {k} best TPLF target(s)
(cap 3; if fewer than 3 analyses, return one entry per analysis, ranked from best to worst).
For each one:
- its rank (1 = best)
- a reasoned synthesis of the choice (rationale): 3-4 sentences
- the decisive arguments (arguments_decisifs): 5-7 precise points drawn from the analyses, with the numerical data and findings that made the difference

Also list the discarded companies (eliminated) with one main reason per company.
Provide a global commentary (global_commentary) explaining the overall logic of the selection.
"""


async def judge_agent(state: PipelineState) -> dict:
  company_analyses = state["company_analyses"]

  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  )

  structured_llm = llm.with_structured_output(JudgeOutput)

  prompt = build_judge_prompt(company_analyses)
  verdict: JudgeOutput = await structured_llm.ainvoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=prompt),
  ])

  return {
    "selected_companies": verdict.top_companies,
    "selection_rationale": verdict.global_commentary,
  }