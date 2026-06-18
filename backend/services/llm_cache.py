# Cache disque des sorties LLM par décision (empreinte PDF + amont).

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)

log = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
_SCHEMA_VERSION = 1


def cache_dir() -> Path:
  return _CACHE_DIR


def sha256_bytes(content: bytes) -> str:
  return hashlib.sha256(content).hexdigest()


def _stable_json(obj: Any) -> str:
  return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _judicial_contract_for_fingerprint(judicial_contract: dict[str, Any] | None) -> dict[str, Any]:
  """Le document_id change à chaque upload — ne pas l'inclure dans l'empreinte cache."""
  body = judicial_contract if isinstance(judicial_contract, dict) else {}
  out = dict(body)
  out.pop("document_id", None)
  return out


def fingerprint_judicial_contract(judicial_contract: dict[str, Any] | None) -> str:
  body = _judicial_contract_for_fingerprint(judicial_contract)
  return hashlib.sha256(_stable_json(body).encode("utf-8")).hexdigest()


def fingerprint_research_batch(
  judicial_contract: dict[str, Any] | None,
  companies: list[str] | None,
  company_kpis_by_name: dict[str, Any] | None = None,
) -> str:
  jc = _judicial_contract_for_fingerprint(judicial_contract)
  names = tuple(sorted(c for c in (companies or []) if c))
  kpis = company_kpis_by_name if isinstance(company_kpis_by_name, dict) else {}
  blob = _stable_json({"jc": jc, "companies": names, "kpis": kpis})
  return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _cache_path(content_hash: str) -> Path:
  return _CACHE_DIR / f"{content_hash}.json"


def _read_file(content_hash: str) -> dict[str, Any]:
  path = _cache_path(content_hash)
  if not path.is_file():
    return {}
  try:
    return json.loads(path.read_text(encoding="utf-8"))
  except (json.JSONDecodeError, OSError):
    log.warning("Cache illisible, ignoré : %s", path)
    return {}


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_suffix(path.suffix + ".tmp")
  tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
  tmp.replace(path)


def _merge_root(content_hash: str, mutator) -> None:
  path = _cache_path(content_hash)
  data = _read_file(content_hash)
  if data.get("schema_version") != _SCHEMA_VERSION:
    data = {"schema_version": _SCHEMA_VERSION, "content_hash": content_hash, "stages": {}}
  if "stages" not in data:
    data["stages"] = {}
  mutator(data)
  data["schema_version"] = _SCHEMA_VERSION
  data["content_hash"] = content_hash
  _atomic_write(path, data)


def get_cached_document_analyzer(content_hash: str | None) -> dict[str, Any] | None:
  if not content_hash:
    return None
  data = _read_file(content_hash)
  if data.get("schema_version") != _SCHEMA_VERSION:
    return None
  stage = (data.get("stages") or {}).get("document_analyzer")
  if not stage or not isinstance(stage, dict):
    return None
  return dict(stage)


def put_cached_document_analyzer(content_hash: str, payload: dict[str, Any]) -> None:
  def mut(data: dict[str, Any]) -> None:
    data["stages"]["document_analyzer"] = dict(payload)

  _merge_root(content_hash, mut)


def get_cached_company_sourcing(
  content_hash: str | None, judicial_contract: dict[str, Any] | None
) -> dict[str, Any] | None:
  if not content_hash:
    return None
  fp = fingerprint_judicial_contract(judicial_contract)
  data = _read_file(content_hash)
  if data.get("schema_version") != _SCHEMA_VERSION:
    return None
  stage = (data.get("stages") or {}).get("company_sourcing")
  if not stage or not isinstance(stage, dict):
    return None
  if stage.get("judicial_contract_fingerprint") != fp:
    return None
  inner = stage.get("payload")
  return dict(inner) if isinstance(inner, dict) else None


def put_cached_company_sourcing(
  content_hash: str, judicial_contract: dict[str, Any], payload: dict[str, Any]
) -> None:
  fp = fingerprint_judicial_contract(judicial_contract)

  def mut(data: dict[str, Any]) -> None:
    data["stages"]["company_sourcing"] = {
      "judicial_contract_fingerprint": fp,
      "payload": dict(payload),
    }

  _merge_root(content_hash, mut)


def get_cached_company_research(
  content_hash: str | None,
  judicial_contract: dict[str, Any] | None,
  companies: list[str] | None,
  company_kpis_by_name: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
  if not content_hash:
    return None
  fp = fingerprint_research_batch(judicial_contract, companies, company_kpis_by_name)
  data = _read_file(content_hash)
  if data.get("schema_version") != _SCHEMA_VERSION:
    return None
  stage = (data.get("stages") or {}).get("company_research")
  if not stage or not isinstance(stage, dict):
    return None
  if stage.get("fingerprint") != fp:
    return None
  inner = stage.get("payload")
  return dict(inner) if isinstance(inner, dict) else None


def put_cached_company_research(
  content_hash: str,
  judicial_contract: dict[str, Any],
  companies: list[str],
  company_kpis_by_name: dict[str, Any] | None,
  payload: dict[str, Any],
) -> None:
  fp = fingerprint_research_batch(judicial_contract, companies, company_kpis_by_name)

  def mut(data: dict[str, Any]) -> None:
    data["stages"]["company_research"] = {"fingerprint": fp, "payload": dict(payload)}

  _merge_root(content_hash, mut)


def delete_analysis_cache(content_hash: str) -> dict[str, Any]:
  """Supprime le fichier cache disque pour une empreinte PDF (SHA-256 hex, 64 caractères)."""
  if not content_hash or not _SHA256_HEX.match(content_hash.strip()):
    raise ValueError("content_hash must be a 64-character hexadecimal SHA-256")
  ch = content_hash.strip().lower()
  path = _cache_path(ch)
  if not path.is_file():
    return {"removed": False, "content_hash": ch}
  try:
    path.unlink()
  except OSError as e:
    log.warning("Impossible de supprimer le cache : %s (%s)", path, e)
    raise OSError(f"Could not delete cache file: {e}") from e
  return {"removed": True, "content_hash": ch}
