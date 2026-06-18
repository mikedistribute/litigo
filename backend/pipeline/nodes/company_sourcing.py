import json
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from tools import gemini_grounding_search
from models.reports import CompanySourcingOutput
from models.pipeline import PipelineState
from config import GEMINI_MODEL, GOOGLE_API_KEY
from services.llm_cache import get_cached_company_sourcing, put_cached_company_sourcing


log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior analyst specialized in antitrust litigation and Third Party Litigation Funding (TPLF).

INPUT: you receive the JSON object `judicial_contract` produced by Node 1 (`document_analyzer`). This JSON is the only source of factual truth about the decision: metadata, sanctioned parties, infraction, key extracts, and the `tplf_structured` section (infraction types, duration, fines, products/victims, geographic market, appeal, sector, follow-on precedents) when present.

Your mission: identify the 3 European publicly listed companies most likely to have suffered a direct economic harm from the infraction described in THIS JSON — relying on the relevant fields (e.g. `infraction`, `key_extracts`, `tplf_structured.produit_service_et_victimes_entreprises`, `tplf_structured.marche_geographique_et_competence`, periods, buyer profiles), and not on external knowledge that is not sourced in this document.

You have access to a web search tool. Run at most 2 to 5 searches to verify that your picks are listed and active on the affected markets. This is a simple task — no need to search further.

RULES:
- Real companies listed on a European stock exchange only
- Never include companies listed in `sanctioned_parties` of the JSON
- Max 1-2 searches, then return the list
- Return only the 3 names (structured field `companies`), nothing else"""


def build_sourcing_prompt(judicial_contract: dict) -> str:
  """Inject the full JSON output of Node 1 (canonical contract)."""
  payload = json.dumps(judicial_contract, ensure_ascii=False, indent=2)
  return f"""Here is the `judicial_contract` (JSON output of Node 1) which you must rely on exclusively for the factual context of the case:

```json
{payload}
```

Using this JSON only for the legal and economic context of the infraction, identify 3 European listed companies that are potential victims (excluding sanctioned parties). Run at most 2-5 web searches to validate listing status and sector relevance, then respond with the requested structured format."""

async def company_sourcing_agent(state: PipelineState) -> dict:
  content_hash = (state.get("content_hash") or "").strip()
  jc = state.get("judicial_contract") or {}
  cached = get_cached_company_sourcing(content_hash, jc) if content_hash else None
  if cached:
    log.info("company_sourcing : cache hit (%s…)", content_hash[:16])
    merged = dict(cached)
    if content_hash:
      merged["content_hash"] = content_hash
    return merged

  llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=1,
    thinking_budget=-1,
  )

  agent = create_react_agent(
    model=llm,
    tools=[gemini_grounding_search],
    response_format=CompanySourcingOutput,
  )

  result = await agent.ainvoke(
    {
      "messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_sourcing_prompt(jc)),
      ]
    },
    config={"recursion_limit": 10},
  )

  output: CompanySourcingOutput = result["structured_response"]
  companies = list(output.companies or [])[:3]

  out = {
    "candidate_companies": companies,
    "status": "researching_companies",
  }
  if content_hash:
    out["content_hash"] = content_hash
    put_cached_company_sourcing(content_hash, jc, out)
  return out