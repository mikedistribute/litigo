import asyncio, json
from datetime import datetime
from pathlib import Path
from pipeline.nodes.report_writer import report_writer
from pipeline.nodes.document_generator import generate_docx
from models.reports import (
  JudicialAnalysis,
  CompanyTPLFAnalysis,
  TPLFPoint,
  JudgeVerdict,
  FinalReport,
)

OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

MOCK_JUDICIAL_ANALYSIS = JudicialAnalysis(
  case_summary="Entente horizontale sur les prix des produits laitiers en GMS France entre 2010 et 2018, sanctionnée par l'Autorité de la concurrence.",
  infraction_type="Entente sur les prix (art. 101 TFUE)",
  affected_sectors=["Grande distribution alimentaire", "Restauration collective"],
  affected_value_chain=["Distributeurs GMS", "Grossistes", "Centrales d'achat"],
  geographic_markets=["France", "Belgique", "Luxembourg"],
  damage_period=["2010", "2018"],
  estimated_overcharge_pct=15.0,
  claimant_profile="Entreprises ayant acheté des produits laitiers en GMS France entre 2010 et 2018",
  key_legal_findings=[
    "Entente horizontale sur les prix qualifiée (art. 101 TFUE)",
    "Période d'infraction de 8 ans — prescription suspendue par l'enquête",
    "Préjudice agrégé estimé à 2,3 milliards EUR sur la période",
    "Surcoût moyen de 15% sur les prix pratiqués",
  ],
  tplf_opportunity_rationale="Recours en dommages-intérêts solide : décision définitive, surcoût documenté à 15%, grands distributeurs français parfaitement identifiés comme victimes directes.",
)

MOCK_ANALYSES = [
  CompanyTPLFAnalysis(
    company_name="Carrefour SA",
    ticker="CA",
    isin="FR0000120172",
    tplf_score=88,
    forces=[
      TPLFPoint(titre="Présence GMS France", argument="Carrefour est le premier distributeur français avec +5000 points de vente.", base="Description entreprise"),
      TPLFPoint(titre="Volume d'achats", argument="CA de 88,7 Mrd EUR implique des achats laitiers massifs sur la période.", base="revenue_eur=88.7B"),
      TPLFPoint(titre="Pays couverts", argument="Présent en France, Belgique, Luxembourg — exactement les marchés de l'infraction.", base="countries"),
    ],
    faiblesses=[
      TPLFPoint(titre="Prescription partielle", argument="Certaines années (2010-2012) peuvent être prescrites selon la juridiction.", base="damage_period"),
    ],
    conclusion="Carrefour est la cible prioritaire : volume d'achats maximal, présence exacte sur les marchés affectés, solidité financière garantissant un litige long.",
  ),
  CompanyTPLFAnalysis(
    company_name="Sodexo SA",
    ticker="SW",
    isin="FR0000121220",
    tplf_score=74,
    forces=[
      TPLFPoint(titre="Restauration collective", argument="Sodexo est un acheteur massif de produits laitiers via sa branche restauration.", base="Description entreprise"),
      TPLFPoint(titre="Présence France", argument="Sodexo opère massivement en France, marché principal de l'infraction.", base="countries"),
      TPLFPoint(titre="Solidité financière", argument="Market cap 9,8 Mrd EUR et résultat net 612M EUR garantissent la capacité à porter le recours.", base="market_cap_eur, net_income_eur"),
    ],
    faiblesses=[
      TPLFPoint(titre="Lien indirect", argument="Sodexo achète via des intermédiaires — le lien de causalité direct est plus difficile à établir.", base="Analyse juridique"),
    ],
    conclusion="Sodexo représente une cible solide grâce à son profil d'acheteur institutionnel de produits laitiers, avec une réserve sur la preuve du préjudice direct.",
  ),
  CompanyTPLFAnalysis(
    company_name="Casino Guichard-Perrachon SA",
    ticker="CO",
    isin="FR0000125585",
    tplf_score=61,
    forces=[
      TPLFPoint(titre="GMS France", argument="Casino opère en GMS France avec les enseignes Casino, Monoprix, Franprix.", base="Description entreprise"),
      TPLFPoint(titre="Présence Belgique/Luxembourg", argument="Présence dans les 3 pays couverts par la décision.", base="countries"),
    ],
    faiblesses=[
      TPLFPoint(titre="Fragilité financière", argument="Résultat net négatif (-1,5 Mrd EUR) et market cap faible (430M EUR) fragilisent la viabilité d'un litige long.", base="net_income_eur=-1.5B, market_cap_eur=430M"),
    ],
    conclusion="Casino est une cible viable sur le fond juridique mais sa situation financière difficile constitue un risque opérationnel significatif pour un funder.",
  ),
]

MOCK_VERDICTS = [
  JudgeVerdict(
    company_name="Carrefour SA",
    rank=1,
    rationale="Carrefour cumule le plus grand volume d'achats, une présence exacte sur les marchés affectés et une solidité financière maximale.",
    arguments_decisifs=[
      "CA 88,7 Mrd EUR — préjudice à 15% estimable entre 500M et 1 Mrd EUR",
      "Présence confirmée France, Belgique, Luxembourg — périmètre exact de l'infraction",
      "Market cap 11,7 Mrd EUR — capacité à financer un litige multi-années sans risque de défaillance",
    ],
  ),
  JudgeVerdict(
    company_name="Sodexo SA",
    rank=2,
    rationale="Sodexo présente un profil d'acheteur institutionnel idéal avec une solidité financière de premier ordre.",
    arguments_decisifs=[
      "Restauration collective — acheteur direct de produits laitiers sur la période 2010-2018",
      "Présence France confirmée — marché principal de l'infraction",
      "Market cap 9,8 Mrd EUR et profitabilité positive — funder attractif",
    ],
  ),
  JudgeVerdict(
    company_name="Casino Guichard-Perrachon SA",
    rank=3,
    rationale="Casino est retenu pour sa position GMS France malgré ses difficultés financières actuelles.",
    arguments_decisifs=[
      "Enseignes Casino, Monoprix, Franprix — achats laitiers GMS France documentés",
      "Présence Belgique et Luxembourg — couvre l'extension géographique de l'infraction",
    ],
  ),
]


async def run():
  print("Node 6 — Rédaction du rapport...\n")

  state = {
    "document_id": "18/D/10",
    "judicial_contract": {},
    "judicial_analysis": MOCK_JUDICIAL_ANALYSIS,
    "candidate_companies": [],
    "company_reports": [],
    "company_analyses": MOCK_ANALYSES,
    "selected_companies": MOCK_VERDICTS,
    "selection_rationale": "",
    "report_content": None,
    "output_docx_path": "",
    "output_pdf_path": "",
    "status": "running",
    "errors": [],
  }

  result = await report_writer(state)
  report: FinalReport = result["report_content"]

  print("=== RAPPORT JSON ===")
  print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))

  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  json_path = OUTPUTS_DIR / f"report_json_{timestamp}.json"
  with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)
  print(f"\nJSON sauvegarde : tests/outputs/{json_path.name}")

  print("\nNode 7 — Génération du fichier Word...")
  docx_path = OUTPUTS_DIR / f"rapport_tplf_{timestamp}.docx"
  generate_docx(report, docx_path)
  print(f"Word sauvegarde : tests/outputs/{docx_path.name}")


asyncio.run(run())