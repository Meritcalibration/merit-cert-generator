import json
from urllib.parse import urlencode

import streamlit as st
from cert_generator import fill_certificate, TEMPLATE_FILES, get_template_defaults

st.set_page_config(page_title="Merit Calibration Certificate Generator", layout="wide")
st.title("Merit Calibration Certificate Generator")
st.caption("Regular templates: Brandon, Hugo, and North")

params = st.query_params


def qp(name: str, default=""):
    value = params.get(name, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value


def qp_float(name: str, default: float) -> float:
    try:
        return float(qp(name, default))
    except (TypeError, ValueError):
        return float(default)


def qp_int(name: str, default: int) -> int:
    try:
        return int(qp(name, default))
    except (TypeError, ValueError):
        return int(default)


template_options = list(TEMPLATE_FILES.keys())
template_default = qp("template_name", template_options[0])
template_index = template_options.index(template_default) if template_default in template_options else 0

with st.sidebar:
    st.subheader("Office Tools")
    app_base_url = st.text_input(
        "Deployed app URL",
        value=qp("app_base_url", ""),
        help="Paste your live Streamlit app URL here once. Example: https://your-app.streamlit.app",
    )

template_name = st.selectbox("Template", template_options, index=template_index)
defaults = get_template_defaults(template_name)

with st.form("certificate_form"):
    st.subheader("Customer")
    company = st.text_input("Company", value=qp("company", ""))
    address = st.text_input("Address", value=qp("address", ""))
    city_state_zip = st.text_input("City / State / Zip", value=qp("city_state_zip", ""))

    st.subheader("Certificate")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        technician = st.text_input("Technician", value=qp("technician", defaults.get("technician", "")))
        certificate_number = st.text_input("Certificate Number", value=qp("certificate_number", ""))
    with c2:
        date_calibrated = st.text_input("Date Calibrated", value=qp("date_calibrated", ""))
        calibration_interval = st.text_input("Calibration Interval", value=qp("calibration_interval", "1 YEAR"))
    with c3:
        customer_req_due = st.text_input("Customer Req. Due", value=qp("customer_req_due", ""))
        certificate_issue_date = st.text_input("Certificate Issue Date", value=qp("certificate_issue_date", ""))
    with c4:
        invoice_number = st.text_input("Invoice Number", value=qp("invoice_number", ""))
        procedure = st.text_input("Procedure", value=qp("procedure", "MCP-1"))

    st.subheader("Instrument")
    c1, c2 = st.columns(2)
    with c1:
        manufacturer = st.text_input("Manufacturer", value=qp("manufacturer", "LOGTAG"))
        instrument = st.text_input("Instrument", value=qp("instrument", "DATA LOGGER THERMOMETER"))
        model_number = st.text_input("Model Number", value=qp("model_number", ""))
        size_range = st.text_input("Size Range", value=qp("size_range", ""))
    with c2:
        serial_number = st.text_input("Serial Number", value=qp("serial_number", ""))
        identification = st.text_input("Identification #", value=qp("identification", ""))
        location = st.text_input("Location", value=qp("location", ""))
        condition_as_found = st.text_input("Condition As Found", value=qp("condition_as_found", "FAIR"))

    st.subheader("Standards Used")
    standard_1 = st.text_input("Standard 1", value=qp("standard_1", defaults.get("standard_1", "")))
    standard_2 = st.text_input("Standard 2", value=qp("standard_2", defaults.get("standard_2", "")))
    standard_3 = st.text_input("Standard 3", value=qp("standard_3", defaults.get("standard_3", "")))

    st.subheader("Tolerance / Environment")
    c1, c2, c3 = st.columns(3)
    with c1:
        rated_tolerance = st.text_input("Rated Tolerance", value=qp("rated_tolerance", "±1°F"))
        tolerance_as_found = st.text_input("Tolerance As Found", value=qp("tolerance_as_found", "IN"))
    with c2:
        adjustments_made = st.text_input("Adjustments Made", value=qp("adjustments_made", "NO"))
        temperature = st.text_input("Temperature", value=qp("temperature", ""))
    with c3:
        relative_humidity = st.text_input("Relative Humidity", value=qp("relative_humidity", ""))

    st.subheader("Results")
    st.write("Use as many rows as you need. These regular templates use one UUT reading per row.")
    results = []
    for i in range(6):
        a, b, c, d, e = st.columns(5)
        with a:
            point_no = st.number_input(
                f"Point # {i+1}",
                min_value=0,
                step=1,
                value=qp_int(f"point_no_{i+1}", i + 1),
                key=f"p{i}",
            )
        with b:
            actual_standard = st.number_input(
                f"Actual {i+1}",
                value=qp_float(f"actual_standard_{i+1}", 40.0),
                step=0.1,
                key=f"a{i}",
            )
        with c:
            as_found = st.number_input(
                f"UUT {i+1}",
                value=qp_float(f"as_found_{i+1}", 40.0),
                step=0.1,
                key=f"f{i}",
            )
        with d:
            uncertainty = st.text_input(
                f"U ± {i+1}",
                value=qp(f"uncertainty_{i+1}", "0.19"),
                key=f"u{i}",
            )
        with e:
            use_row = st.checkbox(
                f"Use row {i+1}",
                value=(qp(f"use_row_{i+1}", "1") == "1" if f"use_row_{i+1}" in params else i < 3),
                key=f"use{i}",
            )

        if use_row:
            row = {
                "point_no": point_no,
                "actual_standard": actual_standard,
                "as_found": as_found,
            }
            if uncertainty.strip():
                try:
                    row["uncertainty"] = float(uncertainty)
                except ValueError:
                    row["uncertainty"] = uncertainty
            results.append(row)

    col_link, col_cert = st.columns(2)
    build_link = col_link.form_submit_button("Generate Technician Link")
    submitted = col_cert.form_submit_button("Generate Certificate")

data = {
    "template_name": template_name,
    "company": company,
    "address": address,
    "city_state_zip": city_state_zip,
    "technician": technician,
    "date_calibrated": date_calibrated,
    "calibration_interval": calibration_interval,
    "customer_req_due": customer_req_due,
    "invoice_number": invoice_number,
    "manufacturer": manufacturer,
    "instrument": instrument,
    "model_number": model_number,
    "size_range": size_range,
    "serial_number": serial_number,
    "identification": identification,
    "standard_1": standard_1,
    "standard_2": standard_2,
    "standard_3": standard_3,
    "procedure": procedure,
    "rated_tolerance": rated_tolerance,
    "tolerance_as_found": tolerance_as_found,
    "adjustments_made": adjustments_made,
    "condition_as_found": condition_as_found,
    "location": location,
    "temperature": temperature,
    "relative_humidity": relative_humidity,
    "certificate_number": certificate_number,
    "certificate_issue_date": certificate_issue_date,
    "results": results,
}

if build_link:
    link_params = {
        "template_name": template_name,
        "company": company,
        "address": address,
        "city_state_zip": city_state_zip,
        "technician": technician,
        "date_calibrated": date_calibrated,
        "calibration_interval": calibration_interval,
        "customer_req_due": customer_req_due,
        "invoice_number": invoice_number,
        "manufacturer": manufacturer,
        "instrument": instrument,
        "model_number": model_number,
        "size_range": size_range,
        "serial_number": serial_number,
        "identification": identification,
        "standard_1": standard_1,
        "standard_2": standard_2,
        "standard_3": standard_3,
        "procedure": procedure,
        "rated_tolerance": rated_tolerance,
        "tolerance_as_found": tolerance_as_found,
        "adjustments_made": adjustments_made,
        "condition_as_found": condition_as_found,
        "location": location,
        "temperature": temperature,
        "relative_humidity": relative_humidity,
        "certificate_number": certificate_number,
        "certificate_issue_date": certificate_issue_date,
    }

    for idx, row in enumerate(results, start=1):
        link_params[f"point_no_{idx}"] = row.get("point_no", idx)
        link_params[f"actual_standard_{idx}"] = row.get("actual_standard", "")
        link_params[f"as_found_{idx}"] = row.get("as_found", "")
        link_params[f"use_row_{idx}"] = "1"
        if "uncertainty" in row:
            link_params[f"uncertainty_{idx}"] = row["uncertainty"]

    technician_query = urlencode({k: v for k, v in link_params.items() if v not in ("", None)})
    relative_link = f"?{technician_query}"
    full_link = f"{app_base_url.rstrip('/')}/{relative_link}" if app_base_url.strip() else ""

    st.success("Technician link created.")
    if full_link:
        st.text_area("Full technician link", value=full_link, height=140)
    st.text_area("Query string", value=relative_link, height=140)
    st.info("Send the full technician link if you entered the deployed app URL in the sidebar.")

if submitted:
    if not serial_number:
        st.error("Serial Number is required.")
    else:
        try:
            output_path = fill_certificate(data)
            st.success(f"Certificate created: {output_path.name}")

            with open(output_path, "rb") as f:
                st.download_button(
                    "Download Excel Certificate",
                    data=f,
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with st.expander("Show the data used"):
                st.code(json.dumps(data, indent=2), language="json")
        except Exception as e:
            st.error(str(e))
