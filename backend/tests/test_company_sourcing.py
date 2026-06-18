import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys

from pipeline.nodes.company_sourcing import company_sourcing_agent

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
  sys.path.insert(0, str(_BACKEND_ROOT))

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_contract.json"
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

async def run():
  with open(FIXTURE_PATH, encoding="utf-8") as f:
    contract = json.load(f)
  
  state = {"document_id": contract["document_id"], "judicial_contract": contract, "errors": []}
  print("Appel Gemini en cours (thinking mode)...\n")
  result = await company_sourcing_agent(state)
  companies = result["candidate_companies"]

  print("=== ENTREPRISES IDENTIFIÉES ===")
  for i, name in enumerate(companies, 1):
    print(f"{i}. {name}")

  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  output_path = OUTPUTS_DIR / f"company_sourcing_{timestamp}.json"
  with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"timestamp": timestamp, "document_id": contract["document_id"], "companies": companies},
      f, ensure_ascii=False, indent=2)

  print(f"\nOutput sauvegardé : tests/outputs/company_sourcing_{timestamp}.json")  

if __name__ == "__main__":
    asyncio.run(run())