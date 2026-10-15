import json
import os
import sys


SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from ldscore_compatibility import validate_bfile_compatibility, validate_sumstats_preanalysis


def make_resolver(root):
    def resolve_upload_file_path(filename, reference=None):
        upload_dir = root / (reference or "")
        return filename, str(upload_dir / filename), str(upload_dir)

    return resolve_upload_file_path


def test_bfile_compatibility_blocks_missing_components(tmp_path):
    reference_dir = tmp_path / "run1"
    reference_dir.mkdir()
    (reference_dir / "custom.bed").write_text("bed", encoding="utf-8")

    result = validate_bfile_compatibility(
        "custom",
        "run1",
        make_resolver(tmp_path),
        lambda _path: {"valid": True, "errors": [], "warnings": []},
        genome_build="grch37",
    )

    assert result["valid"] is False
    assert "custom.bim" in result["errors"][0]
    assert result["status"] == "failed"


def test_bfile_compatibility_records_schema_failure(tmp_path):
    reference_dir = tmp_path / "run1"
    reference_dir.mkdir()
    for extension in ("bed", "bim", "fam"):
        (reference_dir / f"22.{extension}").write_text(extension, encoding="utf-8")

    result = validate_bfile_compatibility(
        "22",
        "run1",
        make_resolver(tmp_path),
        lambda _path: {"valid": False, "errors": ["Invalid bfile schema"], "warnings": []},
        genome_build="grch37",
    )

    assert result["valid"] is False
    assert "Invalid bfile schema" in result["errors"]
    assert result["schema_validation"]["valid"] is False


def test_bfile_compatibility_blocks_unknown_chromosome_coverage(tmp_path):
    reference_dir = tmp_path / "run1"
    reference_dir.mkdir()
    for extension in ("bed", "bim", "fam"):
        (reference_dir / f"custom.{extension}").write_text(extension, encoding="utf-8")

    result = validate_bfile_compatibility(
        "custom",
        "run1",
        make_resolver(tmp_path),
        lambda _path: {"valid": True, "errors": [], "warnings": []},
        genome_build="grch37",
    )

    assert result["valid"] is False
    assert "Chromosome coverage could not be inferred" in result["errors"][0]


def test_summary_statistics_preanalysis_blocks_failed_validation(tmp_path):
    upload_dir = tmp_path / "run1"
    upload_dir.mkdir()
    metadata = {
        "analysis_run_id": "run1",
        "validations": [
            {
                "source_file": "trait.ldsc.tsv",
                "status": "failed",
                "validation_result": {"valid": False},
            }
        ],
    }
    (upload_dir / "sumstats_validation_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    result = validate_sumstats_preanalysis(["trait.ldsc.tsv"], "run1", str(upload_dir))

    assert result["valid"] is False
    assert "validation failed" in result["errors"][0]


def test_summary_statistics_preanalysis_allows_validated_files(tmp_path):
    upload_dir = tmp_path / "run1"
    upload_dir.mkdir()
    metadata = {
        "analysis_run_id": "run1",
        "validations": [
            {
                "source_file": "trait.ldsc.tsv",
                "status": "validated",
                "validation_result": {"valid": True},
            }
        ],
    }
    (upload_dir / "sumstats_validation_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    result = validate_sumstats_preanalysis(["trait.ldsc.tsv"], "run1", str(upload_dir))

    assert result["valid"] is True
    assert result["status"] == "validated"


def test_summary_statistics_preanalysis_allows_normalized_output_file(tmp_path):
    upload_dir = tmp_path / "run1"
    upload_dir.mkdir()
    metadata = {
        "analysis_run_id": "run1",
        "validations": [
            {
                "source_file": "plink.glm",
                "output_location": "plink.ldsc.tsv",
                "status": "validated",
                "validation_result": {"valid": True},
            }
        ],
    }
    (upload_dir / "sumstats_validation_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    result = validate_sumstats_preanalysis(["plink.ldsc.tsv"], "run1", str(upload_dir))

    assert result["valid"] is True
