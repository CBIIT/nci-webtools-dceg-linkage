import gzip
import os
import sys


SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from ldscore_compatibility import validate_ldscore_output, validate_ldscore_output_set


def write_valid_output(path, fileroot="22"):
    output_path = os.path.join(path, f"{fileroot}.l2.ldscore.gz")
    with gzip.open(output_path, "wt") as output_file:
        output_file.write("CHR\tSNP\tBP\tL2\n")
        output_file.write("22\trs123456\t16050075\t0.512\n")
    return output_path


def test_validate_ldscore_output_accepts_readable_variant_level_file(tmp_path):
    write_valid_output(tmp_path)

    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is True
    assert result["status"] == "validated"
    assert result["output_file"] == "22.l2.ldscore.gz"
    assert result["output_size_bytes"] > 0


def test_validate_ldscore_output_blocks_missing_file(tmp_path):
    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is False
    assert result["status"] == "failed"
    assert "was not created" in result["errors"][0]


def test_validate_ldscore_output_blocks_empty_file(tmp_path):
    output_path = os.path.join(tmp_path, "22.l2.ldscore.gz")
    open(output_path, "wb").close()

    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is False
    assert "is empty" in result["errors"][0]


def test_validate_ldscore_output_blocks_missing_header_columns(tmp_path):
    output_path = os.path.join(tmp_path, "22.l2.ldscore.gz")
    with gzip.open(output_path, "wt") as output_file:
        output_file.write("CHR\tSNP\tBP\n")
        output_file.write("22\trs123456\t16050075\n")

    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is False
    assert "missing required SNP/L2 columns" in result["errors"][0]


def test_validate_ldscore_output_blocks_header_only_file(tmp_path):
    output_path = os.path.join(tmp_path, "22.l2.ldscore.gz")
    with gzip.open(output_path, "wt") as output_file:
        output_file.write("CHR\tSNP\tBP\tL2\n")

    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is False
    assert "no variant-level data rows" in result["errors"][0]


def test_validate_ldscore_output_blocks_non_numeric_l2_value(tmp_path):
    output_path = os.path.join(tmp_path, "22.l2.ldscore.gz")
    with gzip.open(output_path, "wt") as output_file:
        output_file.write("CHR\tSNP\tBP\tL2\n")
        output_file.write("22\trs123456\t16050075\tNOT_A_NUMBER\n")

    result = validate_ldscore_output(str(tmp_path), "22", "run1")

    assert result["valid"] is False
    assert "not numeric" in result["errors"][0]


def test_validate_ldscore_output_set_requires_every_requested_chromosome(tmp_path):
    write_valid_output(tmp_path, fileroot="1")
    write_valid_output(tmp_path, fileroot="2")
    # chromosome 3 output intentionally missing

    result = validate_ldscore_output_set(str(tmp_path), ["1", "2", "3"], "run1")

    assert result["valid"] is False
    assert len(result["files"]) == 3
    assert result["files"][0]["valid"] is True
    assert result["files"][1]["valid"] is True
    assert result["files"][2]["valid"] is False


def test_validate_ldscore_output_set_passes_when_all_chromosomes_present(tmp_path):
    write_valid_output(tmp_path, fileroot="1")
    write_valid_output(tmp_path, fileroot="2")

    result = validate_ldscore_output_set(str(tmp_path), ["1", "2"], "run1")

    assert result["valid"] is True
    assert result["status"] == "validated"
