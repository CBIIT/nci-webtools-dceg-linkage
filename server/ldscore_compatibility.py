import json
import os
import time
from typing import Callable, Dict, Iterable, Optional


REQUIRED_BFILE_EXTENSIONS = (".bed", ".bim", ".fam")
SUPPORTED_LDSC_GENOME_BUILDS = {"grch37", "grch38", "grch38_high_coverage"}


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


def _detect_chromosome_coverage(fileroot: str) -> str:
    basename = os.path.basename(fileroot)
    if any(token in basename for token in ("{chr}", "{chrom}", "@")):
        return "template"
    parts = basename.replace("_", ".").replace("-", ".").split(".")
    chromosomes = {str(chromosome) for chromosome in range(1, 23)}
    if any(part in chromosomes for part in parts):
        return "single_chromosome"
    return "unknown"


def _normalize_valid_bfile_result(raw_validity: object) -> Dict[str, object]:
    if isinstance(raw_validity, dict):
        return {
            "valid": bool(raw_validity.get("valid")),
            "errors": raw_validity.get("errors", []),
            "warnings": raw_validity.get("warnings", []),
        }
    return {"valid": bool(raw_validity), "errors": [] if raw_validity else ["Bfile schema validation failed."], "warnings": []}
