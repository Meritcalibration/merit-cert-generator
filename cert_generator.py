from copy import copy
from pathlib import Path
from openpyxl import load_workbook

TEMPLATE_FILES = {
    "Brandon Regular": "Cert Template Revised (Brandon).xlsx",
    "Hugo Regular": "Cert Template Revised (Hugo).xlsx",
    "North Regular": "Cert Template Revised (North).xlsx",
}

OUTPUT_DIR = Path(__file__).with_name("generated_certs")

FIELD_MAP = {
    "company": "F4",
    "address": "F5",
    "city_state_zip": "F6",
    "technician": "F7",
    "manufacturer": "E9",
    "instrument": "E10",
    "model_number": "E11",
    "size_range": "E12",
    "serial_number": "E13",
    "identification": "E14",
    "standard_1": "E16",
    "standard_2": "E17",
    "standard_3": "E18",
}

OPTIONAL_MAP = {
    "procedure": "I9",
    "rated_tolerance": "I10",
    "tolerance_as_found": "I11",
    "adjustments_made": "I12",
    "condition_as_found": "I13",
    "location": "I14",
    "temperature": "I15",
    "relative_humidity": "I16",
    "certificate_number": "I17",
    "certificate_issue_date": "I18",
}

DEFAULTS = {
    "Brandon Regular": {
        "technician": "Brandon",
    },
    "Hugo Regular": {
        "technician": "Hugo",
    },
    "North Regular": {
        "technician": "North",
    },
}

FIRST_RESULT_ROW = 23
TEMPLATE_RESULT_ROWS = 3


def get_template_path(template_name: str) -> Path:
    filename = TEMPLATE_FILES.get(template_name)
    if not filename:
        raise ValueError(f"Unknown template: {template_name}")
    return Path(__file__).with_name(filename)


def copy_row_style(ws, source_row: int, target_row: int) -> None:
    for col in range(1, ws.max_column + 1):
        src = ws.cell(source_row, col)
        dst = ws.cell(target_row, col)

        if src.has_style:
            dst._style = copy(src._style)
        if src.font:
            dst.font = copy(src.font)
        if src.fill:
            dst.fill = copy(src.fill)
        if src.border:
            dst.border = copy(src.border)
        if src.alignment:
            dst.alignment = copy(src.alignment)
        if src.number_format:
            dst.number_format = src.number_format
        if src.protection:
            dst.protection = copy(src.protection)


def calculate_error(actual_standard, uut):
    try:
        return round(float(uut) - float(actual_standard), 2)
    except (TypeError, ValueError):
        return None


def insert_result_rows(ws, results):
    extra_needed = max(0, len(results) - TEMPLATE_RESULT_ROWS)

    if extra_needed:
        insert_at = FIRST_RESULT_ROW + TEMPLATE_RESULT_ROWS
        ws.insert_rows(insert_at, amount=extra_needed)

        source_row = FIRST_RESULT_ROW + TEMPLATE_RESULT_ROWS - 1
        for i in range(extra_needed):
            copy_row_style(ws, source_row, insert_at + i)

    for offset, result in enumerate(results):
        row = FIRST_RESULT_ROW + offset

        point_no = result.get("point_no", offset + 1)
        actual_standard = result.get("actual_standard")
        as_found = result.get("as_found")
        as_left = result.get("as_left")
        error = result.get("error")

        if error is None:
            error = calculate_error(actual_standard, as_found)

        ws[f"C{row}"] = point_no
        ws[f"D{row}"] = actual_standard
        ws[f"H{row}"] = as_found
        if as_left is not None:
            ws[f"I{row}"] = as_left
        if error is not None:
            ws[f"J{row}"] = error


def fill_certificate(data: dict, template_name: str) -> Path:
    template_path = get_template_path(template_name)

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path.name}\n"
            "Make sure the Excel template is in the same folder as the Python files."
        )

    wb = load_workbook(template_path)
    ws = wb["Table 1"]

    merged = {}
    merged.update(DEFAULTS.get(template_name, {}))
    merged.update(data)

    for key, cell in FIELD_MAP.items():
        if merged.get(key) is not None:
            ws[cell] = merged[key]

    for key, cell in OPTIONAL_MAP.items():
        if merged.get(key) is not None:
            ws[cell] = merged[key]

    results = merged.get("results", [])
    if results:
        insert_result_rows(ws, results)

    OUTPUT_DIR.mkdir(exist_ok=True)

    serial = str(merged.get("serial_number", "UNKNOWN")).strip().replace("/", "-")
    cert_number = str(merged.get("certificate_number", "")).strip().replace("/", "-")
    safe_template = template_name.replace(" ", "_")

    parts = [safe_template]
    if cert_number:
        parts.append(cert_number)
    parts.append(serial)

    out_path = OUTPUT_DIR / ("_".join(parts) + ".xlsx")
    wb.save(out_path)
    return out_path


def merge_job_and_instrument(job_data: dict, instrument_data: dict) -> dict:
    merged = dict(job_data)
    merged.update(instrument_data)
    return merged


def generate_certificates_for_job(job_data: dict, instruments: list[dict], template_name: str) -> list[Path]:
    created = []
    for instrument in instruments:
        cert_data = merge_job_and_instrument(job_data, instrument)
        output = fill_certificate(cert_data, template_name=template_name)
        created.append(output)
    return created
