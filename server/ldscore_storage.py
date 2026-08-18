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
    return os.environ.get("LDSCORE_PERSIST_DIR", "/data/ldscore_runs")


def get_s3_bucket() -> Optional[str]:
    return os.environ.get("LDSCORE_S3_BUCKET") or None


def is_s3_enabled() -> bool:
    return bool(get_s3_bucket()) and boto3 is not None


def store_run_files(reference: str, source_dir: str, filenames: List[str]) -> Dict[str, object]:
    """Copies the given filenames from source_dir into persisted storage. Returns
    {"backend": "s3"|"local", "location": str, "files": [{"name", "size"}, ...]}."""
    file_infos = []
    persisted_dir = os.path.join(get_persist_dir(), reference)
    os.makedirs(persisted_dir, exist_ok=True)

    for filename in filenames:
        source_path = os.path.join(source_dir, filename)
        if not os.path.exists(source_path):
            continue
        destination_path = os.path.join(persisted_dir, filename)
        shutil.copyfile(source_path, destination_path)
        file_infos.append({"name": filename, "size": os.path.getsize(destination_path)})

    if not is_s3_enabled():
        return {"backend": "local", "location": persisted_dir, "files": file_infos}

    bucket = get_s3_bucket()
    s3_prefix = f"ldscore_runs/{reference}"
    s3_client = boto3.client("s3")
    for file_info in file_infos:
        local_path = os.path.join(persisted_dir, file_info["name"])
        s3_client.upload_file(local_path, bucket, f"{s3_prefix}/{file_info['name']}")

    return {"backend": "s3", "location": f"s3://{bucket}/{s3_prefix}", "files": file_infos}


def resolve_local_path(run_doc: Dict[str, object], filename: str) -> str:
    """Returns a readable local filesystem path for a persisted output file,
    transparently downloading it from S3 to a local cache copy first if needed."""
    backend = run_doc.get("backend", "local")
    if backend == "local":
        return os.path.join(run_doc.get("ldscore_path", ""), filename)

    bucket = get_s3_bucket()
    if not bucket or boto3 is None:
        raise RuntimeError("S3 storage is not configured but this run was persisted with an S3 backend.")

    reference = run_doc.get("reference", "")
    local_cache_dir = os.path.join(get_persist_dir(), "_s3_cache", reference)
    os.makedirs(local_cache_dir, exist_ok=True)
    local_path = os.path.join(local_cache_dir, filename)
    if not os.path.exists(local_path):
        boto3.client("s3").download_file(bucket, f"ldscore_runs/{reference}/{filename}", local_path)
    return local_path


def run_files_exist(run_doc: Dict[str, object]) -> bool:
    """Verifies every recorded output file for a run is still present in storage."""
    output_files = run_doc.get("output_files", []) or []
    if not output_files:
        return False

    backend = run_doc.get("backend", "local")
    if backend == "local":
        ldscore_path = run_doc.get("ldscore_path", "")
        return all(os.path.exists(os.path.join(ldscore_path, name)) for name in output_files)

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
    target_dir = os.path.join(get_ldsc_reference_data_dir(), subdir_name)
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
            destination_path = os.path.join(target_dir, f"{chromosome}{suffix}")
            if not os.path.exists(destination_path):
                shutil.copyfile(source_path, destination_path)

    return subdir_name
