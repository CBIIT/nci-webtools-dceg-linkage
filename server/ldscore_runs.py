"""Persistent registry of successfully computed custom LD scores.

Lets a browser session reuse an LD score it previously computed (via the `ldscore`
endpoint) as input to a later Heritability or Genetic Correlation analysis, beyond
the 1-hour lifetime of the ephemeral tmp/uploads/{reference} working directory.
Entries are scoped to the session_id derived from the caller's signed browser
session cookie (see LDlink.py internal_auth_guard) so one session can never list
or reuse another session's LD score run.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ldscore_compatibility import extract_chromosome_tokens
from ldscore_storage import store_run_files

RETENTION_DAYS = 7
PERSISTED_OUTPUT_SUFFIXES = (".l2.ldscore.gz", ".l2.M", ".l2.M_5_50", ".log")


def get_persist_dir() -> str:
    return os.environ.get("LDSCORE_PERSIST_DIR", "/data/ldscore_runs")


def ensure_indexes(db) -> None:
    """Self-expiring TTL index so expired runs are dropped from Mongo automatically."""
    db.ldscore_runs.create_index("expires_at", expireAfterSeconds=0)
    db.ldscore_runs.create_index("session_id")


def persist_ldscore_run(
    db,
    reference: str,
    session_id: str,
    file_dir: str,
    fileroot: str,
    genome_build: str,
    chromosome_coverage: str,
    source_filenames: List[str],
    label: Optional[str] = None,
) -> Optional[Dict[str, object]]:
    """Stores computed LD score output files (local disk, or S3 when configured via
    LDSCORE_S3_BUCKET) and records a registry entry. Anonymous requests (no
    session_id) are not eligible for reuse and are silently skipped -- they simply
    fall back to the existing 1-hour tmp behavior with no reuse capability."""
    if not session_id:
        return None

    candidate_filenames = [f"{fileroot}{suffix}" for suffix in PERSISTED_OUTPUT_SUFFIXES]
    storage_result = store_run_files(reference, file_dir, candidate_filenames)
    output_files = [file_info["name"] for file_info in storage_result["files"]]
    file_sizes = {file_info["name"]: file_info["size"] for file_info in storage_result["files"]}
    total_size_bytes = sum(file_sizes.values())

    if not output_files:
        return None

    now = datetime.now(timezone.utc)
    doc = {
        "reference": reference,
        "session_id": session_id,
        "fileroot": fileroot,
        "genome_build": genome_build,
        "chromosome_coverage": chromosome_coverage,
        "chromosome_numbers": extract_chromosome_tokens(fileroot),
        "source_filenames": list(source_filenames or []),
        "backend": storage_result["backend"],
        "ldscore_path": storage_result["location"],
        "output_files": output_files,
        "file_sizes": file_sizes,
        "total_size_bytes": total_size_bytes,
        "label": label or fileroot,
        "status": "ready",
        "created_at": now,
        "expires_at": now + timedelta(days=RETENTION_DAYS),
    }
    db.ldscore_runs.update_one({"reference": reference}, {"$set": doc}, upsert=True)
    return doc


def list_ldscore_runs(db, session_id: str) -> List[Dict[str, object]]:
    if not session_id:
        return []
    now = datetime.now(timezone.utc)
    cursor = db.ldscore_runs.find(
        {"session_id": session_id, "expires_at": {"$gt": now}, "status": "ready"},
        sort=[("created_at", -1)],
    )
    return [public_run_view(doc) for doc in cursor]


def get_ldscore_run(db, reference: str) -> Optional[Dict[str, object]]:
    if not reference:
        return None
    return db.ldscore_runs.find_one({"reference": reference})


def public_run_view(doc: Dict[str, object]) -> Dict[str, object]:
    created_at = doc.get("created_at")
    file_sizes = doc.get("file_sizes", {}) or {}
    return {
        "reference": doc.get("reference"),
        "createdAt": created_at.isoformat() if isinstance(created_at, datetime) else None,
        "genomeBuild": doc.get("genome_build"),
        "chromosomeCoverage": doc.get("chromosome_coverage"),
        "sourceFilenames": doc.get("source_filenames", []),
        "outputFiles": [{"name": name, "size": file_sizes.get(name, 0)} for name in doc.get("output_files", [])],
        "totalSizeBytes": doc.get("total_size_bytes", 0),
        "backend": doc.get("backend", "local"),
        "label": doc.get("label"),
    }
