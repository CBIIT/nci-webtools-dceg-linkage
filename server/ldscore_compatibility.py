import gzip
import json
import os
import time
from typing import Callable, Dict, Iterable, List, Optional

from ldscore_storage import run_files_exist

REQUIRED_BFILE_EXTENSIONS = (".bed", ".bim", ".fam")
SUPPORTED_LDSC_GENOME_BUILDS = {"grch37", "grch38", "grch38_high_coverage"}
LDSCORE_OUTPUT_SUFFIX = ".l2.ldscore.gz"


def _empty_validation(analysis_run_id: str, validation_type: str) -> Dict[str, object]:
    return {
        "analysis_run_id": analysis_run_id,
        "validation_type": validation_type,
        "valid": True,
        "status": "validated",
        "errors": [],
        "warnings": [],
        "validated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def validate_bfile_compatibility(
    fileroot: str,
    reference: str,
    resolve_upload_file_path: Callable[..., tuple],
    valid_bfile: Callable[[str], object],
    genome_build: Optional[str] = None,
) -> Dict[str, object]:
    result = _empty_validation(reference or "", "ldscore_bfile")
    result["fileroot"] = fileroot
    result["genome_build"] = genome_build or ""

    if genome_build and genome_build not in SUPPORTED_LDSC_GENOME_BUILDS:
        result["valid"] = False
        result["errors"].append(f"Unsupported genome build for LD score compatibility validation: {genome_build}")

    missing_files = []
    resolved_paths = {}
    for extension in REQUIRED_BFILE_EXTENSIONS:
        component_name = f"{fileroot}{extension}"
        try:
            _, component_path, _ = resolve_upload_file_path(component_name, reference)
        except ValueError as validation_error:
            result["valid"] = False
            result["errors"].append(str(validation_error))
            continue
        resolved_paths[extension] = component_path
        if not os.path.exists(component_path):
            missing_files.append(component_name)

    if missing_files:
        result["valid"] = False
        result["errors"].append(f"Missing files: {', '.join(missing_files)}")

    result["chromosome_coverage"] = _detect_chromosome_coverage(fileroot)
    if result["chromosome_coverage"] == "unknown":
        result["valid"] = False
        result["errors"].append(
            "Chromosome coverage could not be inferred from the LD score file name. Use chromosome-specific files such as 22.bed/22.bim/22.fam or an approved chromosome template."
        )

    if result["valid"] and ".bed" in resolved_paths:
        raw_validity = valid_bfile(os.path.splitext(resolved_paths[".bed"])[0])
        normalized_validity = _normalize_valid_bfile_result(raw_validity)
        result["schema_validation"] = normalized_validity
        if not normalized_validity["valid"]:
            result["valid"] = False
            result["errors"].extend(normalized_validity["errors"])
            result["warnings"].extend(normalized_validity["warnings"])

    result["status"] = "validated" if result["valid"] else "failed"
    return result


def validate_ldscore_source_compatibility(
    run_doc: Optional[Dict[str, object]],
    reference: str,
    requesting_session_id: str,
    requested_genome_build: Optional[str] = None,
) -> Dict[str, object]:
    """Validates that a persisted custom LD score run (see server/ldscore_runs.py) is
    owned by the requesting browser session, matches the requested genome build, and
    still has its output files on disk, before it is used as input to Heritability or
    Genetic Correlation. Also warns when a single-chromosome LD score is reused for
    what is otherwise a genome-wide analysis."""
    result = _empty_validation(reference or "", "ldscore_source_reuse")

    if not run_doc:
        result["valid"] = False
        result["errors"].append("The selected LD score run was not found or has expired.")
        result["status"] = "failed"
        return result

    result["chromosome_coverage"] = run_doc.get("chromosome_coverage", "unknown")
    result["genome_build"] = run_doc.get("genome_build", "")

    if not requesting_session_id or run_doc.get("session_id") != requesting_session_id:
        result["valid"] = False
        result["errors"].append("You are not authorized to reuse this LD score run.")

    if requested_genome_build and run_doc.get("genome_build") != requested_genome_build:
        result["valid"] = False
        result["errors"].append(
            f"Selected LD score run was computed for genome build {run_doc.get('genome_build')}, but this analysis requested {requested_genome_build}."
        )

    output_files = run_doc.get("output_files", []) or []
    if not output_files or not run_files_exist(run_doc):
        result["valid"] = False
        result["errors"].append("The persisted LD score output files are no longer available.")

    if result["chromosome_coverage"] == "single_chromosome":
        result["warnings"].append(
            "The selected LD score run only covers a single chromosome; results from a genome-wide analysis using it may be incomplete."
        )

    result["status"] = "validated" if result["valid"] else "failed"
    return result


def validate_sumstats_preanalysis(
    filenames: Iterable[str],
    reference: str,
    upload_dir: str,
) -> Dict[str, object]:
    result = _empty_validation(reference or "", "summary_statistics_preanalysis")
    result["files"] = [filename for filename in filenames if filename]

    metadata_path = os.path.join(upload_dir, "sumstats_validation_metadata.json")
    if not os.path.exists(metadata_path):
        result["valid"] = False
        result["errors"].append("Summary statistics validation metadata was not found. Re-upload and validate the summary statistics file before starting analysis.")
        result["status"] = "failed"
        return result

    try:
        with open(metadata_path) as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError) as metadata_error:
        result["valid"] = False
        result["errors"].append(f"Summary statistics validation metadata is unreadable: {metadata_error}")
        result["status"] = "failed"
        return result

    validations = metadata.get("validations", [])
    result["validation_count"] = len(validations)
    validations_by_file = {}
    for record in validations:
        for filename_key in (record.get("source_file"), record.get("output_location")):
            if filename_key:
                validations_by_file[filename_key] = record

    for filename in result["files"]:
        validation = validations_by_file.get(filename)
        if not validation:
            result["valid"] = False
            result["errors"].append(f"No completed summary statistics validation was found for {filename}.")
            continue
        if validation.get("status") != "validated" or not validation.get("validation_result", {}).get("valid"):
            result["valid"] = False
            result["errors"].append(f"Summary statistics validation failed for {filename}.")

    result["status"] = "validated" if result["valid"] else "failed"
    return result


def write_compatibility_metadata(upload_dir: str, record: Dict[str, object]) -> None:
    metadata_path = os.path.join(upload_dir, "ldscore_compatibility_metadata.json")
    existing_records = []
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path) as metadata_file:
                metadata = json.load(metadata_file)
            existing_records = metadata.get("validations", [])
        except (OSError, json.JSONDecodeError):
            existing_records = []
    existing_records.append(record)
    with open(metadata_path, "w") as metadata_file:
        json.dump({"analysis_run_id": record.get("analysis_run_id", ""), "validations": existing_records}, metadata_file, sort_keys=True, indent=2)


def validate_ldscore_output(file_dir: str, fileroot: str, reference: str) -> Dict[str, object]:
    """Validates that an LD score calculation actually produced a readable, non-empty,
    well-formed variant-level output file (header + SNP identifier + L2 value) before
    the run is reported as successful. A missing/empty/malformed output blocks success."""
    result = _empty_validation(reference or "", "ldscore_output")
    result["fileroot"] = fileroot

    output_filename = f"{fileroot}{LDSCORE_OUTPUT_SUFFIX}"
    output_path = os.path.join(file_dir, output_filename)
    result["output_file"] = output_filename

    if not os.path.exists(output_path):
        result["valid"] = False
        result["errors"].append(f"Expected LD score output file was not created: {output_filename}")
        result["status"] = "failed"
        return result

    output_size_bytes = os.path.getsize(output_path)
    result["output_size_bytes"] = output_size_bytes
    if output_size_bytes == 0:
        result["valid"] = False
        result["errors"].append(f"LD score output file is empty: {output_filename}")
        result["status"] = "failed"
        return result

    try:
        with gzip.open(output_path, "rt") as output_file:
            header_line = output_file.readline()
            data_line = output_file.readline()
    except OSError as read_error:
        result["valid"] = False
        result["errors"].append(f"LD score output file is not readable: {read_error}")
        result["status"] = "failed"
        return result

    header_columns = header_line.strip().split()
    if not header_columns or "SNP" not in header_columns or "L2" not in header_columns:
        result["valid"] = False
        result["errors"].append(f"LD score output file header is missing required SNP/L2 columns: {output_filename}")
        result["status"] = "failed"
        return result

    if not data_line or not data_line.strip():
        result["valid"] = False
        result["errors"].append(f"LD score output file has a header but no variant-level data rows: {output_filename}")
        result["status"] = "failed"
        return result

    data_columns = data_line.strip().split()
    snp_index = header_columns.index("SNP")
    l2_index = header_columns.index("L2")
    if len(data_columns) <= max(snp_index, l2_index) or not data_columns[snp_index]:
        result["valid"] = False
        result["errors"].append(f"LD score output data row does not contain a valid variant identifier: {output_filename}")
        result["status"] = "failed"
        return result

    try:
        float(data_columns[l2_index])
    except ValueError:
        result["valid"] = False
        result["errors"].append(f"LD score output L2 value is not numeric: {output_filename}")
        result["status"] = "failed"
        return result

    result["status"] = "validated"
    return result


LDSCORE_IMPORT_REQUIRED_SUFFIXES = (".l2.ldscore.gz", ".l2.M", ".l2.M_5_50")


def validate_ldscore_import_files(file_dir: str, fileroot: str) -> Dict[str, object]:
    """Validates that a directly-imported LD score (uploaded as pre-computed output,
    bypassing this tool's bed/bim/fam + LDSC compute step) has its required companion
    SNP-count files alongside .l2.ldscore.gz. Unlike a fresh compute, there is no
    reliable way to derive .l2.M/.l2.M_5_50 (the reference-panel variant counts LDSC's
    regression is normalized against) from the ldscore file's row count alone -- LDSC
    often restricts .l2.ldscore.gz to a smaller regression SNP list than the M/M_5_50
    counts cover -- so an estimate could silently bias heritability/genetic correlation
    results. These files must be supplied by the caller instead."""
    result = _empty_validation(fileroot, "ldscore_import_files")
    missing_files = [
        f"{fileroot}{suffix}"
        for suffix in LDSCORE_IMPORT_REQUIRED_SUFFIXES
        if not os.path.exists(os.path.join(file_dir, f"{fileroot}{suffix}"))
    ]
    if missing_files:
        result["valid"] = False
        result["errors"].append(f"Missing required file(s): {', '.join(missing_files)}")
    result["status"] = "validated" if result["valid"] else "failed"
    return result


def validate_ldscore_output_set(file_dir: str, filerootlist: List[str], reference: str) -> Dict[str, object]:
    """Validates a set of per-chromosome LD score outputs (e.g. a requested 22-autosome
    run). Aggregates individual validate_ldscore_output results; the set is only valid
    if every requested chromosome produced a valid output."""
    result = _empty_validation(reference or "", "ldscore_output_set")
    result["filerootlist"] = list(filerootlist)
    result["files"] = []

    for fileroot in filerootlist:
        file_result = validate_ldscore_output(file_dir, fileroot, reference)
        result["files"].append(file_result)
        if not file_result["valid"]:
            result["valid"] = False
            result["errors"].extend(file_result["errors"])

    result["status"] = "validated" if result["valid"] else "failed"
    return result


def _detect_chromosome_coverage(fileroot: str) -> str:
    basename = os.path.basename(fileroot)
    if any(token in basename for token in ("{chr}", "{chrom}", "@")):
        return "template"
    parts = basename.replace("_", ".").replace("-", ".").split(".")
    chromosomes = {str(chromosome) for chromosome in range(1, 23)}
    if any(part in chromosomes for part in parts):
        return "single_chromosome"
    return "unknown"


def extract_chromosome_tokens(fileroot: str) -> List[str]:
    """Returns the chromosome number token(s) (e.g. ["20"]) found in a bfile/LD score
    fileroot name, using the same tokenization as _detect_chromosome_coverage. Used to
    map a custom LD score run onto the per-chromosome-numbered directory layout LDSC
    expects (e.g. /data/ldscore/<pop>/<chr>.l2.ldscore.gz)."""
    basename = os.path.basename(fileroot)
    parts = basename.replace("_", ".").replace("-", ".").split(".")
    chromosomes = {str(chromosome) for chromosome in range(1, 23)}
    return [part for part in parts if part in chromosomes]


def _normalize_valid_bfile_result(raw_validity: object) -> Dict[str, object]:
    if isinstance(raw_validity, dict):
        return {
            "valid": bool(raw_validity.get("valid")),
            "errors": raw_validity.get("errors", []),
            "warnings": raw_validity.get("warnings", []),
        }
    return {"valid": bool(raw_validity), "errors": [] if raw_validity else ["Bfile schema validation failed."], "warnings": []}
