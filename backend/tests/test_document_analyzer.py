import asyncio
import json
from pathlib import Path
import sys

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from pipeline.nodes.document_analyzer import document_analyzer

FIXTURE_TEXT = Path(__file__).parent / "fixtures" / "sample_decision_fr.txt"

async def run():
  text = FIXTURE_TEXT.read_text(encoding="utf-8")
  state = {
      "document_id": "test-doc-analyzer-001",
      "decision_full_text": text,
      "judicial_contract": {},
      "errors": [],
  }

  result = await document_analyzer(state)
  contract = result["judicial_contract"]

  print("=== judicial_contract — Node 1 ===")
  print(json.dumps(contract, ensure_ascii=False, indent=2)[:4000])
  assert "document_id" in contract
  assert contract["document_id"] == "test-doc-analyzer-001"
  assert "infraction" in contract
  
if __name__ == "__main__":
    asyncio.run(run())