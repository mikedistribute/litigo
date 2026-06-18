from pydantic import BaseModel, Field, field_validator
from typing import Optional

class JudicialAnalysis(BaseModel):
  case_summary: str
  infraction_type: str
  affected_sectors: list[str]
  affected_value_chain: list[str]
  geographic_markets: list[str]
  damage_period: list[str]
  estimated_overcharge_pct: float
  claimant_profile: str
  key_legal_findings: list[str]
  tplf_opportunity_rationale: str


class CandidateCompany(BaseModel):
  name: str
  ticker: str
  exchange: str
  isin: str
  preliminary_rationale: str
  data_sources: list[str]
  ticker_unverified: bool = False


class CompanySourcingOutput(BaseModel):
  companies: list[str]  # jusqu'à 3 noms (recherche web / grounding au Node 3)

  @field_validator("companies")
  @classmethod
  def cap_three_companies(cls, v: list[str]) -> list[str]:
      return (v or [])[:3]


class LegalProfile(BaseModel):
  legal_team_size: Optional[str] = None                   # ex: "grand département (50+)", "équipe réduite (~10)"
  general_counsel: Optional[str] = None                   # Nom du GC si public
  antitrust_expertise_internal: Optional[bool] = None     # Avocats spécialisés concurrence en interne ?
  past_litigation_highlights: Optional[list[str]] = None  # Contentieux passés significatifs
  antitrust_claims_history: Optional[list[str]] = None    # Réclamations antitrust / dommages concurrence passées
  public_statements_on_cartel: Optional[str] = None       # Déclarations publiques sur le cartel ciblé


class MarketExposure(BaseModel):
  buyer_role: Optional[str] = None                            # "acheteur direct" | "acheteur indirect" | "non identifié"
  geographies_in_affected_markets: Optional[list[str]] = None # Pays actifs dans les zones géo de l'infraction
  activity_overlap_with_cartel_period: Optional[str] = None   # L'entité était-elle active pendant la période du cartel ?
  affected_products_purchased: Optional[list[str]] = None     # Produits/services cartelisés achetés
  exposure_level: Optional[str] = None                        # "fort" | "modéré" | "faible" | "inconnu"


class LitigationCapacity(BaseModel):
  credit_rating: Optional[str] = None                    # Notation S&P / Moody's / Fitch si disponible
  net_debt_eur: Optional[float] = None                    # Dette nette en euros
  financial_stability_assessment: Optional[str] = None   # "stable" | "restructuration en cours" | "difficultés"
  ownership_structure: Optional[str] = None               # "coté indépendant" | "filiale de X" | "fonds PE"
  recent_restructurings: Optional[list[str]] = None       # Restructurations, faillites, plans sociaux récents


class CorporateStructure(BaseModel):
  exact_legal_entity: Optional[str] = None           # Entité juridique précise qui pourrait porter le claim
  parent_company: Optional[str] = None               # Maison mère si filiale
  relevant_subsidiaries: Optional[list[str]] = None  # Filiales actives dans les marchés affectés
  recent_ma_activity: Optional[list[str]] = None     # M&A récents (acquisitions / cessions)
  entity_continuity_note: Optional[str] = None       # L'entité existe-t-elle encore sous cette forme ?


class CompanyReport(BaseModel):
  # Identification
  company_name: str
  ticker: str
  isin: str
  exchange: str
  description: Optional[str] = None        # Description courte (1-2 phrases, issue d'une source web)
  countries: Optional[list[str]] = None    # Pays d'opération vérifiés

  # KPIs financiers (dernière année dispo)
  revenue_eur: Optional[float] = None       # CA en euros
  net_income_eur: Optional[float] = None    # Résultat net en euros
  market_cap_eur: Optional[float] = None    # Capitalisation boursière
  fiscal_year: Optional[int] = None         # Année des données

  # Due diligence TPLF
  legal_profile: Optional[LegalProfile] = None
  market_exposure: Optional[MarketExposure] = None
  litigation_capacity: Optional[LitigationCapacity] = None
  corporate_structure: Optional[CorporateStructure] = None


class SelectedCompany(BaseModel):
  company: CandidateCompany
  report: CompanyReport
  rank: int
  selection_rationale: str


class TPLFPoint(BaseModel):
  titre: str        # Titre court du point
  argument: str     # Argument développé
  base: str         # Source / métrique sur laquelle s'appuie l'argument


class CompanyTPLFAnalysis(BaseModel):
  company_name: str
  ticker: str
  isin: str
  forces: list[TPLFPoint]       # Raisons pour cibler cette entreprise (6-10 points)
  faiblesses: list[TPLFPoint]   # Risques / obstacles au TPLF (4-6 points)
  tplf_score: Optional[int] = None  # Conservé pour compatibilité front — non utilisé dans l'analyse
  conclusion: str               # Synthèse détaillée (5-8 phrases)


class JudgeVerdict(BaseModel):
  company_name: str
  rank: int                           # 1 = meilleure cible
  rationale: str                      # Synthèse du choix (2-3 phrases)
  arguments_decisifs: list[str]       # Arguments précis qui ont motivé la sélection


class JudgeOutput(BaseModel):
  top_companies: list[JudgeVerdict]         # Jusqu'à 3 meilleures cibles (ordre par rank)
  eliminated: list[str]                     # Noms des entreprises écartées
  global_commentary: str                    # Synthèse de la sélection finale

  @field_validator("top_companies")
  @classmethod
  def cap_top_three(cls, v: list[JudgeVerdict]) -> list[JudgeVerdict]:
      return sorted(v or [], key=lambda x: x.rank)[:3]


class SelectionOutput(BaseModel):
  analyses: list[CompanyTPLFAnalysis]
  selection_commentary: str
  ranking_justification: str


class ReportContent(BaseModel):
  case_reference: str
  generation_date: str
  executive_summary: str
  judicial_analysis_section: str
  methodology_section: str
  company_sections: list[dict]
  annexes: list[dict]


class DecisionKPIsSection(BaseModel):
  infraction_type: str
  period: str                         # ex: "2010 - 2018"
  geographic_scope: str
  affected_markets: list[str]
  estimated_overcharge_pct: Optional[float]
  total_damage_estimate: Optional[str]  # ex: "2,3 milliards EUR"
  key_legal_findings: list[str]
  claimant_profile: str


class CompanyReportSection(BaseModel):
  rank: int
  company_name: str
  ticker: str
  isin: str
  tplf_score: Optional[int] = Field(
      default=None,
      description="Score kept for frontend compatibility; may be absent.",
  )
  key_arguments: list[str] = Field(
      description="TPLF strategic angles and legal grounds applicable to THIS company — "
      "not a restatement of the strengths above. WRITE IN ENGLISH."
  )
  significant_weaknesses: list[str] = Field(
      default_factory=list,
      description="Material risks for a funder (evidence, time-bar, claim transfer). WRITE IN ENGLISH.",
  )
  conclusion: str = Field(
      description="Decisional synthesis, 2-4 sentences (go / no-go, priority diligences). "
      "Do not copy the strengths list. WRITE IN ENGLISH."
  )


class FinalReport(BaseModel):
  case_reference: str
  generation_date: str
  exec_summary: str
  decision_kpis: DecisionKPIsSection
  company_1: CompanyReportSection
  company_2: CompanyReportSection
  company_3: CompanyReportSection