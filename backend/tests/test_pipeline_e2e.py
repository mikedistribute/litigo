import asyncio, json, time
from datetime import datetime
from pathlib import Path

from pipeline.nodes.company_sourcing import company_sourcing_agent
from pipeline.nodes.company_research import company_research_agent
from pipeline.nodes.selection_agent import selection_agent
from pipeline.nodes.judge_agent import judge_agent
from pipeline.nodes.report_writer import report_writer
from pipeline.nodes.document_generator import generate_docx
from models.reports import FinalReport
from pipeline.judicial_from_contract import judicial_analysis_from_contract

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_contract.json"
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


def log(step: str, elapsed: float, detail: str = ""):
  print(f"  [{elapsed:5.1f}s] {step}" + (f" — {detail}" if detail else ""))


async def run():
  with open(FIXTURE_PATH, encoding="utf-8") as f:
    contract = json.load(f)

  judicial_analysis = judicial_analysis_from_contract(contract)
  case_ref = contract["metadata"]["case_reference"]

  state = {
    "document_id": case_ref,
    "judicial_contract": contract,
    "judicial_analysis": judicial_analysis,
    "candidate_companies": [],
    "company_reports": [],
    "company_analyses": [],
    "selected_companies": [],
    "selection_rationale": "",
    "report_content": None,
    "output_docx_path": "",
    "output_pdf_path": "",
    "status": "running",
    "errors": [],
  }

  t_start = time.time()
  timings = {}

  print(f"\n{'='*60}")
  print(f"  PIPELINE E2E — {case_ref}")
  print(f"{'='*60}\n")

  # ── Node 2 : Sourcing ────────────────────────────────────────
  print("Node 2 — Sourcing des entreprises...")
  t0 = time.time()
  result = await company_sourcing_agent(state)
  state.update(result)
  timings["node2_sourcing"] = time.time() - t0
  companies = state["candidate_companies"]
  log("Sourcing terminé", timings["node2_sourcing"], f"{len(companies)} entreprises trouvées")
  for c in companies:
    print(f"   - {c}")

  # ── Node 3 : Recherche KPIs (parallèle) ─────────────────────
  print(f"\nNode 3 — Recherche KPIs ({len(companies)} entreprises en parallèle)...")
  t0 = time.time()
  research_tasks = [
    company_research_agent({
      "company": name,
      "judicial_contract": contract,
      "company_reports": [],
    })
    for name in companies
  ]
  research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
  company_reports = []
  for name, r in zip(companies, research_results):
    if isinstance(r, Exception):
      print(f"   ERREUR Node 3 pour {name}: {r}")
    else:
      company_reports.extend(r["company_reports"])
  state["company_reports"] = company_reports
  timings["node3_research"] = time.time() - t0
  log("Recherche terminée", timings["node3_research"], f"{len(company_reports)} rapports")
  for r in company_reports:
    print(f"   - {r.company_name} | score: N/A | market_cap: {r.market_cap_eur}")

  # ── Node 4 : Analyse TPLF (parallèle) ───────────────────────
  print(f"\nNode 4 — Analyse TPLF ({len(company_reports)} entreprises en parallèle)...")
  t0 = time.time()
  analysis_tasks = [
    selection_agent({
      "judicial_contract": contract,
      "company_report": report,
    })
    for report in company_reports
  ]
  analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
  company_analyses = []
  for report, r in zip(company_reports, analysis_results):
    if isinstance(r, Exception):
      print(f"   ERREUR Node 4 pour {report.company_name}: {r}")
    else:
      company_analyses.extend(r["company_analyses"])
  state["company_analyses"] = company_analyses
  timings["node4_analysis"] = time.time() - t0
  log("Analyse TPLF terminée", timings["node4_analysis"], f"{len(company_analyses)} analyses")
  for a in company_analyses:
    print(f"   - {a.company_name} | tplf_score: {a.tplf_score}/100")

  # ── Node 5 : Judge ───────────────────────────────────────────
  print(f"\nNode 5 — LLM as judge (sélection top 3)...")
  t0 = time.time()
  judge_result = await judge_agent(state)
  state.update(judge_result)
  timings["node5_judge"] = time.time() - t0
  top = state["selected_companies"]
  log("Sélection terminée", timings["node5_judge"], f"{len(top)} entreprises retenues")
  for v in top:
    print(f"   #{v.rank} {v.company_name}")

  # ── Node 6 : Report Writer ───────────────────────────────────
  print(f"\nNode 6 — Rédaction du rapport...")
  t0 = time.time()
  writer_result = await report_writer(state)
  state.update(writer_result)
  timings["node6_writer"] = time.time() - t0
  log("Rapport rédigé", timings["node6_writer"])

  # ── Node 7 : Document Generator ─────────────────────────────
  print(f"\nNode 7 — Génération du fichier Word...")
  t0 = time.time()
  report: FinalReport = state["report_content"]
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  docx_path = OUTPUTS_DIR / f"rapport_tplf_e2e_{timestamp}.docx"
  json_path = OUTPUTS_DIR / f"rapport_tplf_e2e_{timestamp}.json"
  generate_docx(report, docx_path)
  with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)
  state["output_docx_path"] = str(docx_path)
  timings["node7_docx"] = time.time() - t0
  log("Word généré", timings["node7_docx"])

  # ── Résumé ───────────────────────────────────────────────────
  total = time.time() - t_start
  print(f"\n{'='*60}")
  print(f"  PIPELINE TERMINÉ EN {total:.1f}s")
  print(f"{'='*60}")
  print(f"  Node 2 (sourcing)   : {timings['node2_sourcing']:.1f}s")
  print(f"  Node 3 (research)   : {timings['node3_research']:.1f}s  (x{len(company_reports)} en parallèle)")
  print(f"  Node 4 (analysis)   : {timings['node4_analysis']:.1f}s  (x{len(company_analyses)} en parallèle)")
  print(f"  Node 5 (judge)     : {timings['node5_judge']:.1f}s")
  print(f"  Node 6 (writer)    : {timings['node6_writer']:.1f}s")
  print(f"  Node 7 (docx)      : {timings['node7_docx']:.1f}s")
  print(f"\n  Word  : tests/outputs/{docx_path.name}")
  print(f"  JSON  : tests/outputs/{json_path.name}")
  print(f"{'='*60}\n")


asyncio.run(run())