import json
import zipfile
from pathlib import Path

import streamlit as st

from cert_generator import generate_certificates_for_job

st.set_page_config(page_title="Merit Calibration Job Generator", layout="wide")
st.title("Merit Calibration Job Certificate Generator")
st.caption("Office pre-fills one job. Technician enters readings for each thermometer.")

template_name = st.selectbox(
    "Template",
    ["Brandon Regular", "Hugo Regular", "North Regular"]
)

st.subheader("Step 1 - Job Information")
c1, c2, c3 = st.columns(3)
with c1:
    company = st.text_input("Customer / Company")
    address = st.text_input("Address")
with c2:
    city_state_zip = st.text_input("City / State / Zip")
    location = st.text_input("Location / Site")
with c3:
    technician = st.text_input("Technician")
    certificate_issue_date = st.text_input("Certificate Issue Date")

st.subheader("Step 2 - Shared Calibration Details")
c1, c2, c3 = st.columns(3)
with c1:
    procedure = st.text_input("Procedure", value="TEMP-001")
    temperature = st.text_input("Temperature", value="72°F")
with c2:
    relative_humidity = st.text_input("Relative Humidity", value="45%")
    rated_tolerance = st.text_input("Rated Tolerance", value="±1.0°F")
with c3:
    tolerance_as_found = st.text_input("Tolerance As Found", value="±1.0°F")
    adjustments_made = st.text_input("Adjustments Made", value="NONE")

condition_as_found = st.text_input("Condition As Found", value="IN TOLERANCE")

st.subheader("Step 3 - Standards Used")
s1, s2, s3 = st.columns(3)
with s1:
    standard_1 = st.text_input("Standard 1")
with s2:
    standard_2 = st.text_input("Standard 2")
with s3:
    standard_3 = st.text_input("Standard 3")

num_instruments = st.number_input("How many thermometers?", min_value=1, max_value=20, value=3, step=1)

st.subheader("Step 4 - Instrument Entry")
st.write("For each thermometer, enter the instrument info and field readings.")

job_data = {
    "company": company,
    "address": address,
    "city_state_zip": city_state_zip,
    "technician": technician,
    "procedure": procedure,
    "rated_tolerance": rated_tolerance,
    "tolerance_as_found": tolerance_as_found,
    "adjustments_made": adjustments_made,
    "condition_as_found": condition_as_found,
    "location": location,
    "temperature": temperature,
    "relative_humidity": relative_humidity,
    "certificate_issue_date": certificate_issue_date,
    "standard_1": standard_1,
    "standard_2": standard_2,
    "standard_3": standard_3,
}

instruments = []

for idx in range(int(num_instruments)):
    with st.expander(f"Thermometer {idx + 1}", expanded=(idx == 0)):
        top1, top2, top3 = st.columns(3)
        with top1:
            certificate_number = st.text_input(f"Certificate Number #{idx + 1}", key=f"cn_{idx}")
            manufacturer = st.text_input(f"Manufacturer #{idx + 1}", value="LOGTAG", key=f"mfg_{idx}")
        with top2:
            instrument = st.text_input(f"Instrument #{idx + 1}", value="DATA LOGGER THERMOMETER", key=f"inst_{idx}")
            model_number = st.text_input(f"Model Number #{idx + 1}", key=f"model_{idx}")
        with top3:
            serial_number = st.text_input(f"Serial Number #{idx + 1}", key=f"sn_{idx}")
            identification = st.text_input(f"Identification #{idx + 1}", key=f"id_{idx}")

        size_range = st.text_input(f"Size Range #{idx + 1}", key=f"range_{idx}")

        st.markdown("**Readings**")
        results = []
        for r in range(5):
            a, b, c, d, e = st.columns(5)
            with a:
                point_no = st.number_input(f"Point {r + 1} #{idx + 1}", min_value=0, step=1, value=r + 1, key=f"p_{idx}_{r}")
            with b:
                actual_standard = st.number_input(f"Actual {r + 1} #{idx + 1}", value=0.0, step=0.1, key=f"a_{idx}_{r}")
            with c:
                as_found = st.number_input(f"As Found {r + 1} #{idx + 1}", value=0.0, step=0.1, key=f"f_{idx}_{r}")
            with d:
                as_left = st.text_input(f"As Left {r + 1} #{idx + 1}", key=f"l_{idx}_{r}")
            with e:
                use_row = st.checkbox(f"Use row {r + 1}", value=(r < 3), key=f"u_{idx}_{r}")

            if use_row:
                row = {
                    "point_no": point_no,
                    "actual_standard": actual_standard,
                    "as_found": as_found,
                }
                if as_left.strip():
                    try:
                        row["as_left"] = float(as_left)
                    except ValueError:
                        row["as_left"] = as_left
                results.append(row)

        instruments.append({
            "certificate_number": certificate_number,
            "manufacturer": manufacturer,
            "instrument": instrument,
            "model_number": model_number,
            "serial_number": serial_number,
            "identification": identification,
            "size_range": size_range,
            "results": results,
        })

generate = st.button("Generate All Certificates")

if generate:
    if not company:
        st.error("Customer / Company is required.")
    elif not any(i.get("serial_number") for i in instruments):
        st.error("At least one instrument needs a serial number.")
    else:
        try:
            created = generate_certificates_for_job(job_data, instruments, template_name)

            st.success(f"Created {len(created)} certificate(s).")

            zip_path = Path("generated_certs") / "job_certificates.zip"
            zip_path.parent.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in created:
                    zf.write(path, arcname=path.name)

            with open(zip_path, "rb") as f:
                st.download_button(
                    "Download All Certificates (ZIP)",
                    data=f,
                    file_name="job_certificates.zip",
                    mime="application/zip"
                )

            for path in created:
                with open(path, "rb") as f:
                    st.download_button(
                        f"Download {path.name}",
                        data=f,
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{path.name}"
                    )

            st.subheader("Job Data")
            st.code(json.dumps(job_data, indent=2), language="json")

        except Exception as e:
            st.error(str(e))
