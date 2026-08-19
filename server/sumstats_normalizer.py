import csv
import gzip
import math
import os
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple


LDSC_OUTPUT_COLUMNS = ["SNP", "A1", "A2", "N", "P", "BETA"]
NORMALIZATION_PIPELINE_VERSION = "sumstats-normalizer-v1"


@dataclass(frozen=True)
class SumstatsFormat:
    name: str
    required_any: Dict[str, Tuple[str, ...]]
    canonical_columns: Dict[str, str]
    transforms: Dict[str, str]


SUMSTATS_FORMATS = [
    SumstatsFormat(
        name="LDSC-ready",
        required_any={
            "SNP": ("SNP", "MARKERNAME", "SNPID", "RS", "RSID", "RS_NUMBER", "RS_NUMBERS"),
            "P": ("P", "PVALUE", "P_VALUE", "PVAL", "P_VAL", "GC_PVALUE"),
            "N": ("N", "N_CAS", "N_CON"),
            "SIGNED": ("Z", "ZSCORE", "Z_SCORE", "OR", "B", "BETA", "LOG_ODDS"),
        },
        canonical_columns={},
        transforms={},
    ),
    SumstatsFormat(
        name="PLINK",
        required_any={
            "SNP": ("ID",),
            "N": ("OBS_CT", "N"),
            "A1": ("A1",),
            "A2": ("REF", "A2", "ALT"),
            "P": ("P",),
            "BETA": ("BETA", "OR"),
        },
        canonical_columns={"ID": "SNP", "OBS_CT": "N", "A1": "A1", "REF": "A2", "A2": "A2", "ALT": "A2", "P": "P", "BETA": "BETA", "OR": "BETA"},
        transforms={"OR": "log_or"},
    ),
    SumstatsFormat(
        name="REGENIE",
        required_any={
            "SNP": ("ID",),
            "N": ("N",),
            "A1": ("ALLELE1", "A1"),
            "A2": ("ALLELE0", "A2"),
            "P": ("P", "LOG10P"),
            "BETA": ("BETA", "OR"),
        },
        canonical_columns={"ID": "SNP", "N": "N", "ALLELE1": "A1", "A1": "A1", "ALLELE0": "A2", "A2": "A2", "P": "P", "LOG10P": "P", "BETA": "BETA", "OR": "BETA"},
        transforms={"LOG10P": "log10p", "OR": "log_or"},
    ),
    SumstatsFormat(
        name="SAIGE",
        required_any={
            "SNP": ("MARKERID",),
            "N": ("N",),
            "A1": ("ALLELE2",),
            "A2": ("ALLELE1",),
            "P": ("P_VALUE", "P"),
            "BETA": ("BETA", "OR"),
        },
        canonical_columns={"MARKERID": "SNP", "N": "N", "ALLELE2": "A1", "ALLELE1": "A2", "P_VALUE": "P", "P": "P", "BETA": "BETA", "OR": "BETA"},
        transforms={"OR": "log_or"},
    ),
]

SELECTED_FORMATS = {
    "pre_munged": "LDSC-ready",
    "plink_raw": "PLINK",
    "regenie_raw": "REGENIE",
    "saige_raw": "SAIGE",
}


def _clean_header(header: str) -> str:
    return header.strip().upper().replace("-", "_").replace(".", "_")


def _open_text(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", newline="")
    return open(path, "r", newline="")


def _detect_delimiter(header_line: str) -> Optional[str]:
    if "," in header_line and "\t" not in header_line:
        return ","
    if "\t" in header_line:
        return "\t"
    return None


def _read_header(path: str) -> Tuple[List[str], Optional[str]]:
    with _open_text(path) as input_file:
        header_line = input_file.readline()
    if not header_line:
        return [], None
    delimiter = _detect_delimiter(header_line)
    if delimiter:
        header = next(csv.reader([header_line], delimiter=delimiter))
    else:
        header = header_line.strip().split()
    return [column.strip() for column in header if column.strip()], delimiter


def _row_reader(path: str, delimiter: Optional[str]) -> Iterable[Dict[str, str]]:
    with _open_text(path) as input_file:
        if delimiter:
            reader = csv.DictReader(input_file, delimiter=delimiter)
            for row in reader:
                yield {str(key): (value or "") for key, value in row.items() if key is not None}
        else:
            header = input_file.readline().strip().split()
            for line in input_file:
                values = line.strip().split()
                if not values:
                    continue
                yield dict(zip(header, values))


def _columns_by_clean_name(columns: List[str]) -> Dict[str, str]:
    return {_clean_header(column): column for column in columns}


def _first_present(columns_by_clean_name: Dict[str, str], aliases: Tuple[str, ...]) -> Optional[str]:
    for alias in aliases:
        if alias in columns_by_clean_name:
            return columns_by_clean_name[alias]
    return None


def _format_matches(format_spec: SumstatsFormat, columns_by_clean_name: Dict[str, str]) -> Tuple[bool, Dict[str, str], List[str]]:
    mapped_columns = {}
    missing = []
    for canonical_name, aliases in format_spec.required_any.items():
        column = _first_present(columns_by_clean_name, aliases)
        if column:
            mapped_columns[column] = canonical_name
        else:
            missing.append(f"Missing required {canonical_name} column. Expected one of: {', '.join(aliases)}")
    return not missing, mapped_columns, missing


def _detect_format(columns: List[str]) -> Tuple[Optional[SumstatsFormat], Dict[str, str], List[str]]:
    columns_by_clean_name = _columns_by_clean_name(columns)
    errors_by_format = []
    for format_spec in SUMSTATS_FORMATS:
        matched, mapped_columns, missing = _format_matches(format_spec, columns_by_clean_name)
        if matched:
            return format_spec, mapped_columns, []
        errors_by_format.append(f"{format_spec.name}: {'; '.join(missing)}")
    return None, {}, errors_by_format


def _format_by_selected_value(selected_format: Optional[str]) -> Optional[SumstatsFormat]:
    if not selected_format:
        return None
    expected_name = SELECTED_FORMATS.get(selected_format)
    if not expected_name:
        return None
    return next((format_spec for format_spec in SUMSTATS_FORMATS if format_spec.name == expected_name), None)


def _parse_float(value: str, column: str) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Column {column} contains a non-numeric value: {value}")


def _format_probability(value: str, column: str) -> str:
    parsed_value = _parse_float(value, column)
    if not 0 < parsed_value <= 1:
        raise ValueError(f"Column {column} contains a p-value outside (0, 1]: {value}")
    return format(parsed_value, ".15g")


def _transform_value(value: str, transform: Optional[str], column: str) -> str:
    if transform == "log10p":
        parsed_value = _parse_float(value, column)
        if parsed_value < 0:
            raise ValueError(f"Column {column} contains a negative -log10(p) value: {value}")
        return format(math.pow(10, -parsed_value), ".15g")
    if transform == "log_or":
        parsed_value = _parse_float(value, column)
        if parsed_value <= 0:
            raise ValueError(f"Column {column} contains a non-positive odds ratio: {value}")
        return format(math.log(parsed_value), ".15g")
    return str(value).strip()


def _normalized_filename(input_path: str) -> str:
    filename = os.path.basename(input_path)
    if filename.endswith(".gz"):
        filename = filename[:-3]
    base_name, _ = os.path.splitext(filename)
    return f"{base_name}.ldsc.tsv"


def _build_output_mapping(format_spec: SumstatsFormat, columns_by_clean_name: Dict[str, str]) -> Dict[str, str]:
    output_mapping = {}
    for source_clean_name, canonical_name in format_spec.canonical_columns.items():
        source_column = columns_by_clean_name.get(source_clean_name)
        if source_column and canonical_name not in output_mapping:
            output_mapping[canonical_name] = source_column
    return output_mapping


def _write_normalized_file(input_path: str, output_path: str, format_spec: SumstatsFormat, delimiter: Optional[str], max_error_count: int = 10) -> Tuple[int, List[str]]:
    columns, _ = _read_header(input_path)
    columns_by_clean_name = _columns_by_clean_name(columns)
    output_mapping = _build_output_mapping(format_spec, columns_by_clean_name)
    errors = []
    row_count = 0

    with open(output_path, "w", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=LDSC_OUTPUT_COLUMNS, delimiter="\t")
        writer.writeheader()
        for row_number, row in enumerate(_row_reader(input_path, delimiter), start=2):
            try:
                output_row = {}
                for canonical_name in LDSC_OUTPUT_COLUMNS:
                    source_column = output_mapping.get(canonical_name)
                    if not source_column:
                        raise ValueError(f"No source column mapped for {canonical_name}")
                    source_clean_name = _clean_header(source_column)
                    output_row[canonical_name] = _transform_value(
                        row.get(source_column, ""), format_spec.transforms.get(source_clean_name), source_column
                    )
                output_row["P"] = _format_probability(output_row["P"], "P")
                writer.writerow(output_row)
                row_count += 1
            except ValueError as error:
                if len(errors) < max_error_count:
                    errors.append(f"Row {row_number}: {error}")

    return row_count, errors


def normalize_sumstats_for_ldsc(input_path: str, output_dir: str, selected_format: Optional[str] = None) -> Dict[str, object]:
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "columns": [],
        "mapped_columns": {},
        "mappedColumns": {},
        "detected_format": None,
        "detectedFormat": None,
        "selected_format": selected_format,
        "selectedFormat": selected_format,
        "pipeline_version": NORMALIZATION_PIPELINE_VERSION,
        "pipelineVersion": NORMALIZATION_PIPELINE_VERSION,
        "normalized_filename": os.path.basename(input_path),
        "normalizedFilename": os.path.basename(input_path),
    }

    if not os.path.exists(input_path):
        result["valid"] = False
        result["errors"].append(f"File not found: {input_path}")
        return result

    columns, delimiter = _read_header(input_path)
    result["columns"] = columns
    if not columns:
        result["valid"] = False
        result["errors"].append("File is empty or missing a header row.")
        return result

    selected_format_spec = _format_by_selected_value(selected_format)
    if selected_format and selected_format_spec is None:
        result["valid"] = False
        result["errors"].append(
            "Unsupported summary statistics format selection. Select PLINK raw, REGENIE raw, SAIGE raw, or Pre-munged."
        )
        return result

    if selected_format_spec:
        columns_by_clean_name = _columns_by_clean_name(columns)
        matched, mapped_columns, missing = _format_matches(selected_format_spec, columns_by_clean_name)
        if not matched:
            result["valid"] = False
            result["detected_format"] = selected_format_spec.name
            result["detectedFormat"] = selected_format_spec.name
            result["errors"].append(
                f"Uploaded file does not match the selected {selected_format_spec.name} format. Select the correct format or upload a pre-munged LDSC-ready file."
            )
            result["errors"].extend(missing)
            return result
        format_spec = selected_format_spec
        errors_by_format = []
    else:
        format_spec, mapped_columns, errors_by_format = _detect_format(columns)

    if format_spec is None:
        result["valid"] = False
        result["errors"].append("Could not detect a supported summary statistics format.")
        result["errors"].extend(errors_by_format)
        return result

    result["detected_format"] = format_spec.name
    result["detectedFormat"] = format_spec.name
    result["mapped_columns"] = mapped_columns
    result["mappedColumns"] = mapped_columns

    if format_spec.name == "LDSC-ready":
        return result

    normalized_filename = _normalized_filename(input_path)
    normalized_path = os.path.join(output_dir, normalized_filename)
    row_count, row_errors = _write_normalized_file(input_path, normalized_path, format_spec, delimiter)
    if row_errors:
        result["valid"] = False
        result["errors"].extend(row_errors)
        return result
    if row_count == 0:
        result["valid"] = False
        result["errors"].append("No data rows were found in the uploaded summary statistics file.")
        return result

    result["normalized_filename"] = normalized_filename
    result["normalizedFilename"] = normalized_filename
    if format_spec.name == "REGENIE" and "LOG10P" in _columns_by_clean_name(columns):
        result["warnings"].append("LOG10P was converted to P for LDSC munging.")
    if any(_clean_header(column) == "OR" for column in mapped_columns):
        result["warnings"].append("OR was converted to BETA using log(OR) for LDSC munging.")
    return result
