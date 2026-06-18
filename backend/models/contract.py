from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
  model_config = ConfigDict(extra="ignore")

  jurisdiction: str | None = None
  court: str | None = None
  decision_date: str | None = None
  case_reference: str | None = None
  document_language: str | None = None


class SanctionedParty(BaseModel):
  model_config = ConfigDict(extra="ignore")

  name: str | None = None
  role: str | None = None
  fine_amount_eur: float | None = None
  sector: str | None = None


class Infraction(BaseModel):
  model_config = ConfigDict(extra="ignore")

  type: str | None = None
  affected_markets: list[str] = Field(default_factory=list)
  geographic_scope: str | None = None
  period_start: str | None = None
  period_end: str | None = None
  summary: str | None = None


class KeyExtracts(BaseModel):
  model_config = ConfigDict(extra="ignore")

  damage_quantification: list[str] = Field(default_factory=list)
  affected_buyer_profiles: list[str] = Field(default_factory=list)
  geographic_scope_details: list[str] = Field(default_factory=list)
  legal_findings: list[str] = Field(default_factory=list)


class TplfTypesInfraction(BaseModel):
  model_config = ConfigDict(extra="ignore")

  category: str | None = None
  subtype: str | None = None
  legal_articles_explicit_in_decision: list[str] = Field(default_factory=list)
  presumptions_and_burden_notes: str | None = None


class TplfDureeInfraction(BaseModel):
  model_config = ConfigDict(extra="ignore")

  period_start: str | None = None
  period_end: str | None = None
  full_calendar_years_count: int | None = None
  methodology_notes: str | None = None


class TplfMontantAmende(BaseModel):
  model_config = ConfigDict(extra="ignore")

  total_fines_eur_aggregate: float | None = None
  legal_cap_reference_text: str | None = None
  reiteration_or_recidivism_flag: bool | None = None
  fine_magnitude_band: str | None = None
  fine_magnitude_band_justification: str | None = None


class TplfProduitServiceVictimes(BaseModel):
  model_config = ConfigDict(extra="ignore")

  produit_cartelise_precis: str | None = None
  marche_produit_definition: str | None = None
  marche_geographique_definition: str | None = None
  acheteurs_directs_types: list[str] = Field(default_factory=list)
  victims_are_identifiable_enterprises: bool | None = None
  victim_identification_branch: str | None = None
  notes_scope_b2b_vs_consumers: str | None = None


class TplfMarcheGeographiqueCompetence(BaseModel):
  model_config = ConfigDict(extra="ignore")

  affects_only_france: bool | None = None
  affects_trade_between_member_states: bool | None = None
  competent_authority: str | None = None
  follow_on_forum_summary: str | None = None


class TplfStatutAppel(BaseModel):
  model_config = ConfigDict(extra="ignore")

  status: str | None = None
  court_level_summary: str | None = None
  tplf_process_warning: str | None = None


class TplfSecteurEconomique(BaseModel):
  model_config = ConfigDict(extra="ignore")

  nace_codes_in_decision: list[str] = Field(default_factory=list)
  sector_cluster: str | None = None
  sector_notes: str | None = None


class TplfPrecedentFollowOn(BaseModel):
  model_config = ConfigDict(extra="ignore")

  case_or_cartel_name: str | None = None
  jurisdiction: str | None = None
  outcome_summary: str | None = None
  source_hint: str | None = None


class TplfStructured(BaseModel):
  model_config = ConfigDict(extra="ignore")

  types_infraction: TplfTypesInfraction | None = None
  duree_infraction: TplfDureeInfraction | None = None
  montant_amende: TplfMontantAmende | None = None
  produit_service_et_victimes_entreprises: TplfProduitServiceVictimes | None = None
  marche_geographique_et_competence: TplfMarcheGeographiqueCompetence | None = None
  statut_appel: TplfStatutAppel | None = None
  secteur_economique: TplfSecteurEconomique | None = None
  precedents_follow_on_documentes: list[TplfPrecedentFollowOn] = Field(default_factory=list)


class JudicialContract(BaseModel):
  """Only output of node 1"""

  model_config = ConfigDict(extra="ignore")

  document_id: str
  metadata: DocumentMetadata | None = None
  sanctioned_parties: list[SanctionedParty] = Field(default_factory=list)
  infraction: Infraction | None = None
  key_extracts: KeyExtracts | None = None
  tplf_structured: TplfStructured | None = None