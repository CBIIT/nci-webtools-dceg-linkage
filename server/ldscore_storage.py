"""Storage backend abstraction for persisted custom LD score runs.

Defaults to local filesystem storage under LDSCORE_PERSIST_DIR. If LDSCORE_S3_BUCKET
is configured, persisted output files are also uploaded to S3 under that bucket.
This is intentionally a *separate* bucket/env var from the existing read-only
reference-data S3_BUCKET (see LDcommon.py/LDutilites.py) so this feature never writes
into the curated reference dataset bucket without an explicit, separate opt-in.
"""
import os
import shutil
from typing import Dict, List, Optional

try:
    import boto3
except ImportError:  # pragma: no cover - boto3 is already a project dependency
    boto3 = None


def get_persist_dir() -> str:
    default_dir = os.path.join(os.environ.get("TMP_DIR", "/data/tmp/"), "ldscore_runs")
    return os.environ.get("LDSCORE_PERSIST_DIR", default_dir)


def get_s3_bucket() -> Optional[str]:
    return os.environ.get("LDSCORE_S3_BUCKET") or None


def is_s3_enabled() -> bool:
    return bool(get_s3_bucket()) and boto3 is not None


def _is_path_confined(candidate_path: str, base_dir: str) -> bool:
    """Returns True iff the normalized candidate_path resolves inside base_dir --
    call this immediately before using a user-influenced path, in the same function
    as the file operation, so static analysis (and readers) can see the guard."""
    normalized_base = os.path.normpath(os.path.realpath(base_dir))
    normalized_candidate = os.path.normpath(os.path.realpath(candidate_path))
    return normalized_candidate == normalized_base or normalized_candidate.startswith(normalized_base + os.sep)


def store_run_files(reference: str, source_dir: str, filenames: List[str]) -> Dict[str, object]:
    """Copies the given filenames from source_dir into persisted storage. Returns
    {"backend": "s3"|"local", "location": str, "files": [{"name", "size"}, ...]}."""
    file_infos = []
    persist_root = get_persist_dir()
    os.makedirs(persist_root, exist_ok=True)
    # Resolve and check containment inline, on the exact values used by the
    # file operations below, so the guards are visible to static analysis.
    persist_base = os.path.realpath(persist_root)
    persisted_dir = os.path.realpath(os.path.join(persist_base, reference))
    if not persisted_dir.startswith(persist_base + os.sep):
        raise RuntimeError("Invalid reference parameter.")
    os.makedirs(persisted_dir, exist_ok=True)

    source_base = os.path.realpath(source_dir)
    for filename in filenames:
        if not filename or os.path.basename(filename) != filename:
            continue
        source_path = os.path.realpath(os.path.join(source_base, filename))
        if not source_path.startswith(source_base + os.sep):
            continue
        if not os.path.exists(source_path):
            continue
        destination_path = os.path.realpath(os.path.join(persisted_dir, filename))
        if not destination_path.startswith(persisted_dir + os.sep):
            continue
        shutil.copyfile(source_path, destination_path)
        file_infos.append({"name": filename, "size": os.path.getsize(destination_path)})

    if not is_s3_enabled():
        return {"backend": "local", "location": persisted_dir, "files": file_infos}

    bucket = get_s3_bucket()
    s3_prefix = f"ldscore_runs/{reference}"
    s3_client = boto3.client("s3")
    for file_info in file_infos:
        local_name = file_info["name"]
        local_path = os.path.normpath(os.path.join(persisted_dir, local_name))
        if not _is_path_confined(local_path, persisted_dir):
            continue
        s3_client.upload_file(local_path, bucket, f"{s3_prefix}/{local_name}")

    return {"backend": "s3", "location": f"s3://{bucket}/{s3_prefix}", "files": file_infos}


def resolve_local_path(run_doc: Dict[str, object], filename: str) -> str:
    """Returns a readable local filesystem path for a persisted output file,
    transparently downloading it from S3 to a local cache copy first if needed."""
    if not filename or os.path.basename(filename) != filename:
        raise RuntimeError("Invalid LD score output filename.")

    backend = run_doc.get("backend", "local")
    if backend == "local":
        ldscore_path = run_doc.get("ldscore_path", "")
        local_path = os.path.normpath(os.path.join(ldscore_path, filename))
        if not _is_path_confined(local_path, ldscore_path):
            raise RuntimeError("Invalid LD score output filename.")
        return local_path

    bucket = get_s3_bucket()
    if not bucket or boto3 is None:
        raise RuntimeError("S3 storage is not configured but this run was persisted with an S3 backend.")

    reference = run_doc.get("reference", "")
    s3_cache_root = os.path.join(get_persist_dir(), "_s3_cache")
    os.makedirs(s3_cache_root, exist_ok=True)
    local_cache_dir = os.path.normpath(os.path.join(s3_cache_root, reference))
    if not _is_path_confined(local_cache_dir, s3_cache_root):
        raise RuntimeError("Invalid reference parameter.")
    os.makedirs(local_cache_dir, exist_ok=True)
    local_path = os.path.normpath(os.path.join(local_cache_dir, filename))
    if not _is_path_confined(local_path, local_cache_dir):
        raise RuntimeError("Invalid LD score output filename.")
    if not os.path.exists(local_path):
        boto3.client("s3").download_file(bucket, f"ldscore_runs/{reference}/{filename}", local_path)
    return local_path


def get_local_path_base(run_doc: Dict[str, object]) -> str:
    """Returns the base directory that resolve_local_path()'s return value must
    resolve inside for the given run's backend. Callers that go on to use that
    path in a file operation (open/zipf.write/send_file/...) should redundantly
    re-check confinement against this base, inline in their own function, since a
    boolean/path check performed only inside resolve_local_path() itself is not a
    visible barrier for static analysis of the caller."""
    backend = run_doc.get("backend", "local")
    if backend == "local":
        return run_doc.get("ldscore_path", "")
    reference = run_doc.get("reference", "")
    return os.path.normpath(os.path.join(get_persist_dir(), "_s3_cache", reference))


def run_files_exist(run_doc: Dict[str, object]) -> bool:
    """Verifies every recorded output file for a run is still present in storage."""
    output_files = run_doc.get("output_files", []) or []
    if not output_files:
        return False

    backend = run_doc.get("backend", "local")
    if backend == "local":
        ldscore_path = run_doc.get("ldscore_path", "")
        for name in output_files:
            if not name or os.path.basename(name) != name:
                return False
            candidate = os.path.normpath(os.path.join(ldscore_path, name))
            if not _is_path_confined(candidate, ldscore_path) or not os.path.exists(candidate):
                return False
        return True

    bucket = get_s3_bucket()
    if not bucket or boto3 is None:
        return False
    reference = run_doc.get("reference", "")
    s3_client = boto3.client("s3")
    for name in output_files:
        try:
            s3_client.head_object(Bucket=bucket, Key=f"ldscore_runs/{reference}/{name}")
        except Exception:
            return False
    return True


def get_ldsc_reference_data_dir() -> str:
    # Must match the (hardcoded) fallExampleDir in the external ldsc.ldsc_utils
    # package, which builds ld_scores_dir as f"{fallExampleDir}/{value.lower()}/".
    return os.environ.get("LDSC_REFERENCE_DATA_DIR", "/data/ldscore")


def prepare_ldsc_ref_dir(run_doc: Dict[str, object]) -> str:
    """Materializes a persisted custom LD score run into the per-chromosome-numbered
    directory layout run_herit_command/run_correlation_command expect (e.g.
    /data/ldscore/<name>/<chr>.l2.ldscore.gz, mirroring the built-in population
    directories such as /data/ldscore/eur/). Returns the directory name to pass as
    their ld_scores_dir argument in place of a population code."""
    chromosome_numbers = run_doc.get("chromosome_numbers") or []
    if not chromosome_numbers:
        raise RuntimeError(
            "Unable to determine which chromosome(s) this custom LD score run covers; it cannot be used for this analysis."
        )

    reference = run_doc.get("reference", "")
    subdir_name = f"custom_{reference}".lower()
    ldsc_reference_root = get_ldsc_reference_data_dir()
    os.makedirs(ldsc_reference_root, exist_ok=True)
    target_dir = os.path.normpath(os.path.join(ldsc_reference_root, subdir_name))
    if not _is_path_confined(target_dir, ldsc_reference_root):
        raise RuntimeError("Invalid reference parameter.")
    os.makedirs(target_dir, exist_ok=True)

    fileroot = run_doc.get("fileroot", "")
    output_files = set(run_doc.get("output_files") or [])
    for chromosome in chromosome_numbers:
        for suffix in (".l2.ldscore.gz", ".l2.M", ".l2.M_5_50"):
            source_filename = f"{fileroot}{suffix}"
            if source_filename not in output_files:
                continue
            source_path = resolve_local_path(run_doc, source_filename)
            if not os.path.exists(source_path):
                continue
            destination_name = f"{chromosome}{suffix}"
            destination_path = os.path.normpath(os.path.join(target_dir, destination_name))
            if not _is_path_confined(destination_path, target_dir):
                continue
            if not os.path.exists(destination_path):
                shutil.copyfile(source_path, destination_path)

    return subdir_name
