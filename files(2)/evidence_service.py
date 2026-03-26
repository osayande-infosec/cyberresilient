"""
cyberresilient/services/evidence_service.py

Evidence Artifact Service — file upload, storage, retrieval, and linkage
to risks and controls.

Storage layout:
  evidence/
    risks/<risk_id>/<uuid><ext>
    controls/<control_id>/<uuid><ext>

Each artifact is recorded in the DB (with JSON sidecar fallback).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

from cyberresilient.config import DATA_DIR

EVIDENCE_DIR: Path = DATA_DIR.parent / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".docx",
    ".xlsx", ".csv", ".txt", ".eml", ".msg", ".zip",
}
MAX_FILE_SIZE_MB = 25


def _db_available() -> bool:
    try:
        from cyberresilient.database import get_engine
        from sqlalchemy import inspect
        return inspect(get_engine()).has_table("evidence_artifacts")
    except Exception:
        return False


def _artifact_dir(entity_type: str, entity_id: str) -> Path:
    d = EVIDENCE_DIR / entity_type / entity_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def upload_artifact(
    entity_type: str,
    entity_id: str,
    filename: str,
    file_bytes: bytes,
    description: str = "",
    uploaded_by: str = "system",
) -> dict:
    """
    Store an evidence artifact and record metadata.
    entity_type: 'risk' | 'control'
    Raises ValueError for bad type/size.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File type '{suffix}' not allowed. "
            f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File {size_mb:.1f} MB exceeds limit of {MAX_FILE_SIZE_MB} MB.")

    artifact_id = str(uuid.uuid4())
    safe_name = f"{artifact_id}{suffix}"
    dest = _artifact_dir(entity_type, entity_id) / safe_name
    dest.write_bytes(file_bytes)

    meta = {
        "id": artifact_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "original_filename": filename,
        "stored_filename": safe_name,
        "description": description,
        "size_bytes": len(file_bytes),
        "sha256": _sha256(file_bytes),
        "uploaded_by": uploaded_by,
        "uploaded_at": date.today().isoformat(),
    }

    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import EvidenceArtifactRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            session.add(EvidenceArtifactRow(**meta))
            log_action(session, action="upload_artifact",
                       entity_type=entity_type, entity_id=entity_id,
                       user=uploaded_by, after=meta)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        dest.with_suffix(".json").write_text(json.dumps(meta, indent=2))

    return meta


def list_artifacts(entity_type: str, entity_id: str) -> list[dict]:
    """Return all artifacts for an entity, newest first."""
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import EvidenceArtifactRow
        session = get_session()
        try:
            rows = (
                session.query(EvidenceArtifactRow)
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .order_by(EvidenceArtifactRow.uploaded_at.desc())
                .all()
            )
            return [r.to_dict() for r in rows]
        finally:
            session.close()
    d = _artifact_dir(entity_type, entity_id)
    results = []
    for m in sorted(d.glob("*.json"), reverse=True):
        try:
            results.append(json.loads(m.read_text()))
        except Exception:
            pass
    return results


def get_artifact_bytes(entity_type: str, entity_id: str, artifact_id: str) -> tuple[bytes, str]:
    """Return (bytes, original_filename) for download."""
    meta = next(
        (a for a in list_artifacts(entity_type, entity_id) if a["id"] == artifact_id),
        None,
    )
    if not meta:
        raise FileNotFoundError(f"Artifact {artifact_id} not found.")
    stored = _artifact_dir(entity_type, entity_id) / meta["stored_filename"]
    return stored.read_bytes(), meta["original_filename"]


def delete_artifact(
    entity_type: str, entity_id: str, artifact_id: str, deleted_by: str = "system"
) -> None:
    meta = next(
        (a for a in list_artifacts(entity_type, entity_id) if a["id"] == artifact_id),
        None,
    )
    if not meta:
        raise FileNotFoundError(f"Artifact {artifact_id} not found.")
    d = _artifact_dir(entity_type, entity_id)
    for f in [d / meta["stored_filename"], (d / meta["stored_filename"]).with_suffix(".json")]:
        if f.exists():
            f.unlink()
    if _db_available():
        from cyberresilient.database import get_session
        from cyberresilient.models.db_models import EvidenceArtifactRow
        from cyberresilient.services.audit_service import log_action
        session = get_session()
        try:
            row = session.query(EvidenceArtifactRow).filter_by(id=artifact_id).first()
            if row:
                session.delete(row)
                log_action(session, action="delete_artifact",
                            entity_type=entity_type, entity_id=entity_id,
                            user=deleted_by, before=meta)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def artifact_count(entity_type: str, entity_id: str) -> int:
    return len(list_artifacts(entity_type, entity_id))


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 ** 2):.1f} MB"
