import asyncio, json
from datetime import datetime
from pathlib import Path
from pipeline.nodes.selection_agent import selection_agent
from pipeline.nodes.judge_agent import judge_agent
from models.reports import CompanyReport

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_contract.json"
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

MOCK_REPORTS = [
  CompanyReport(
    company_name="Carrefour SA",
    ticker="CA",
    isin="FR0000120172",
    exchange="Euronext Paris",
    description="Carrefour est le deuxième distributeur alimentaire mondial, présent en France via plus de 5000 points de vente GMS.",
    countries=["France", "Belgique", "Espagne", "Italie", "Brésil"],
    revenue_eur=88_700_000_000,
    net_income_eur=1_080_000_000,
    market_cap_eur=11_700_000_000,
    fiscal_year=2024,
  ),
  CompanyReport(
    company_name="Casino Guichard-Perrachon SA",
    ticker="CO",
    isin="FR0000125585",
    exchange="Euronext Paris",
    description="Casino est un groupe de distribution alimentaire français opérant en GMS via les enseignes Casino, Monoprix, Franprix.",
    countries=["France", "Belgique", "Luxembourg"],
    revenue_eur=8_200_000_000,
    net_income_eur=-1_500_000_000,
    market_cap_eur=430_000_000,
    fiscal_year=2024,
  ),
  CompanyReport(
    company_name="Leclerc (Galec)",
    ticker="N/A",
    isin="N/A",
    exchange="Non coté",
    description="Leclerc est la première enseigne de grande distribution française, coopérative non cotée.",
    countries=["France", "Espagne", "Portugal"],
    revenue_eur=51_000_000_000,
    net_income_eur=None,
    market_cap_eur=None,
    fiscal_year=2024,
  ),
  CompanyReport(
    company_name="Sodexo SA",
    ticker="SW",
    isin="FR0000121220",
    exchange="Euronext Paris",
    description="Sodexo est un groupe de services dont la restauration collective, actif dans plus de 45 pays.",
    countries=["France", "Royaume-Uni", "États-Unis", "Allemagne"],
    revenue_eur=23_800_000_000,
    net_income_eur=612_000_000,
    market_cap_eur=9_800_000_000,
    fiscal_year=2024,
  ),
  CompanyReport(
    company_name="Danone SA",
    ticker="BN",
    isin="FR0000120644",
    exchange="Euronext Paris",
    description="Danone est un producteur de produits laitiers et agroalimentaires — potentiellement auteur de l'entente.",
    countries=["France", "Belgique", "Espagne", "Pays-Bas"],
    revenue_eur=27_400_000_000,
    net_income_eur=1_840_000_000,
    market_cap_eur=31_500_000_000,
    fiscal_year=2024,
  ),
]


async def run():
  with open(FIXTURE_PATH, encoding="utf-8") as f:
    contract = json.load(f)

  # --- Node 4 : analyse individuelle en parallèle ---
  print(f"Node 4 — Analyse individuelle de {len(MOCK_REPORTS)} entreprises en parallèle...\n")

  tasks = [
    selection_agent({
      "judicial_contract": contract,
      "company_report": report,
    })
    for report in MOCK_REPORTS
  ]
  results = await asyncio.gather(*tasks)

  all_analyses = []
  for r in results:
    analysis = r["company_analyses"][0]
    all_analyses.append(analysis)
    print(f"  {analysis.company_name} — score: {analysis.tplf_score}/100")

  # --- Node 5 : LLM as judge ---
  print(f"\nNode 5 — LLM as judge sur {len(all_analyses)} analyses...\n")

  judge_state = {
    "company_analyses": all_analyses,
    # champs PipelineState requis
    "document_id": "test-001",
    "judicial_contract": contract,
    "judicial_analysis": None,
    "candidate_companies": [],
    "company_reports": [],
    "selected_companies": [],
    "selection_rationale": "",
    "report_content": None,
    "output_docx_path": "",
    "output_pdf_path": "",
    "status": "running",
    "errors": [],
  }
  judge_result = await judge_agent(judge_state)

  top = judge_result["selected_companies"]
  print("=== TOP 3 ENTREPRISES RETENUES ===")
  for v in top:
    print(f"  #{v.rank} {v.company_name} — {v.rationale[:100]}...")

  print(f"\nCommentaire global : {judge_result['selection_rationale'][:200]}...")

  # Sauvegarde
  output = {
    "node4_analyses": [a.model_dump() for a in all_analyses],
    "node5_verdict": {
      "top_companies": [v.model_dump() for v in top],
      "eliminated": judge_result["selected_companies"],
      "global_commentary": judge_result["selection_rationale"],
    },
  }
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  output_path = OUTPUTS_DIR / f"selection_judge_{timestamp}.json"
  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

  print(f"\nOutput sauvegarde : tests/outputs/{output_path.name}")


asyncio.run(run())