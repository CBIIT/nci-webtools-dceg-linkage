import csv
import os
import sys


SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "server"))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from sumstats_normalizer import normalize_sumstats_for_ldsc


def write_text(path, content):
    path.write_text(content, encoding="utf-8")


def read_normalized(path):
    with path.open(newline="", encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file, delimiter="\t"))


def test_plink_sumstats_are_normalized(tmp_path):
    source = tmp_path / "plink.glm"
    write_text(source, "ID A1 REF OBS_CT BETA SE P\nrs1 A G 1000 0.25 0.04 0.001\n")

    result = normalize_sumstats_for_ldsc(str(source), str(tmp_path))

    assert result["valid"] is True
    assert result["detected_format"] == "PLINK"
    assert result["normalized_filename"] == "plink.ldsc.tsv"
    rows = read_normalized(tmp_path / result["normalized_filename"])
    assert rows == [{"SNP": "rs1", "A1": "A", "A2": "G", "N": "1000", "P": "0.001", "BETA": "0.25"}]


def test_regenie_log10p_is_converted(tmp_path):
    source = tmp_path / "regenie.txt"
    write_text(source, "ID ALLELE0 ALLELE1 N BETA SE LOG10P\nrs2 C T 2000 -0.1 0.03 3\n")

    result = normalize_sumstats_for_ldsc(str(source), str(tmp_path))

    assert result["valid"] is True
    assert result["detected_format"] == "REGENIE"
    assert "LOG10P was converted to P" in result["warnings"][0]
    rows = read_normalized(tmp_path / result["normalized_filename"])
    assert rows[0]["P"] == "0.001"
    assert rows[0]["A1"] == "T"
    assert rows[0]["A2"] == "C"


def test_saige_sumstats_are_normalized(tmp_path):
    source = tmp_path / "saige.tsv"
    write_text(source, "MarkerID\tAllele1\tAllele2\tN\tBETA\tSE\tp.value\nrs3\tG\tA\t3000\t0.2\t0.05\t0.02\n")

    result = normalize_sumstats_for_ldsc(str(source), str(tmp_path))

    assert result["valid"] is True
    assert result["detected_format"] == "SAIGE"
    rows = read_normalized(tmp_path / result["normalized_filename"])
    assert rows[0] == {"SNP": "rs3", "A1": "A", "A2": "G", "N": "3000", "P": "0.02", "BETA": "0.2"}


def test_ldsc_ready_is_not_rewritten(tmp_path):
    source = tmp_path / "ready.txt"
    write_text(source, "SNP A1 A2 N P Z\nrs4 A C 4000 0.5 1.2\n")

    result = normalize_sumstats_for_ldsc(str(source), str(tmp_path))

    assert result["valid"] is True
    assert result["detected_format"] == "LDSC-ready"
    assert result["normalized_filename"] == "ready.txt"
    assert not (tmp_path / "ready.ldsc.tsv").exists()


def test_unsupported_file_reports_missing_columns(tmp_path):
    source = tmp_path / "bad.txt"
    write_text(source, "foo bar baz\n1 2 3\n")

    result = normalize_sumstats_for_ldsc(str(source), str(tmp_path))

    assert result["valid"] is False
    assert result["errors"][0] == "Could not detect a supported summary statistics format."
