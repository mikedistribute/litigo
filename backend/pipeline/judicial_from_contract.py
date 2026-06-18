from __future__ import annotations

import re
from typing import Any

from models.reports import JudicialAnalysis


def judicial_analysis_from_contract(contract: dict[str, Any]) -> JudicialAnalysis:
  """Build a JudicialAnalysis from `judicial_contract` (Node 1)."""
  infraction = contract.get("infraction") or {}
  extracts = contract.get("key_extracts") or {}
  tplf = contract.get("tplf_structured") or {}

  overcharge = 0.0
  for d in extracts.get("damage_quantification", []) or []:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(d))
    if m:
      overcharge = float(m.group(1).replace(",", "."))
      break

  findings = list(extracts.get("legal_findings") or [])
  types_inf = tplf.get("types_infraction") if isinstance(tplf, dict) else None
  if isinstance(types_inf, dict):
    arts = types_inf.get("legal_articles_explicit_in_decision") or []
    if isinstance(arts, list) and arts:
      findings = findings + [f"Decision text — articles / bases: {', '.join(str(a) for a in arts)}"]

  geo_extra = extracts.get("geographic_scope_details") or []
  geo_list = [g for g in [infraction.get("geographic_scope")] + list(geo_extra) if g]

  tplf_rationale_parts: list[str] = []
  if isinstance(tplf, dict):
    duree = tplf.get("duree_infraction")
    if isinstance(duree, dict) and duree.get("full_calendar_years_count") is not None:
      tplf_rationale_parts.append(
        f"Duration documented in the decision: ~{duree['full_calendar_years_count']} calendar years."
      )
    montant = tplf.get("montant_amende")
    if isinstance(montant, dict) and montant.get("total_fines_eur_aggregate") is not None:
      tplf_rationale_parts.append(
        f"Aggregated fine(s) mentioned: {montant['total_fines_eur_aggregate']} EUR."
      )
  tplf_opportunity = " ".join(tplf_rationale_parts) if tplf_rationale_parts else (
    "Decision context extracted from the contract: infraction and victims to be cross-referenced with the buyer portfolio."
  )

  return JudicialAnalysis(
    case_summary=str(infraction.get("summary") or ""),
    infraction_type=str(infraction.get("type") or ""),
    affected_sectors=list(infraction.get("affected_markets") or []),
    affected_value_chain=list(extracts.get("affected_buyer_profiles") or []),
    geographic_markets=[str(x) for x in geo_list if x],
    damage_period=[
      str(infraction.get("period_start") or "")[:4],
      str(infraction.get("period_end") or "")[:4],
    ],
    estimated_overcharge_pct=overcharge,
    claimant_profile=" | ".join(extracts.get("affected_buyer_profiles") or []) or "N/A",
    key_legal_findings=findings or ["(no structured legal finding in key_extracts.legal_findings)"],
    tplf_opportunity_rationale=tplf_opportunity,
  )