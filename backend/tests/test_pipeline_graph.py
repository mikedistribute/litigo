"""Tests sans appel LLM pour le graphe LangGraph."""

import asyncio
import json
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
  sys.path.insert(0, str(_BACKEND_ROOT))

from models.contract import JudicialContract
from pipeline.graph import build_pipeline


def test_sample_contract_matches_judicial_contract_schema():
  path = Path(__file__).parent / "fixtures" / "sample_contract.json"
  data = json.loads(path.read_text(encoding="utf-8"))
  jc = JudicialContract.model_validate(data)
  assert jc.document_id
  assert jc.infraction is not None


def test_pipeline_stops_when_node1_missing_text():
  async def _run():
    g = build_pipeline()
    return await g.ainvoke(
      {
        "document_id": "no-text",
        "decision_full_text": "",
        "judicial_contract": {},
        "errors": [],
        "company_reports": [],
      }
    )

  out = asyncio.run(_run())
  assert out.get("status") == "failed"
  assert out.get("errors")