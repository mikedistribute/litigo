import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from pipeline.nodes.company_research import company_research_agent

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_contract.json"
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


async def run():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        contract = json.load(f)

    # Test sur Carrefour — entreprise française, Pappers devrait couvrir
    company_name = "Carrefour SA"
    print(f"Recherche en cours : {company_name} (Gemini grounding)...\n")

    state = {
        "company": company_name,
        "judicial_contract": contract,
        "company_reports": [],
    }

    result = await company_research_agent(state)
    report = result["company_reports"][0]

    print(f"=== RAPPORT COMPLET : {company_name} ===")
    print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUTS_DIR / f"company_research_{company_name.replace(' ', '_')}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"\nOutput sauvegarde : tests/outputs/{output_path.name}")


if __name__ == "__main__":
    asyncio.run(run())