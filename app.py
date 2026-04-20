import json
from datetime import datetime
from pathlib import Path
import zipfile

import streamlit as st
from cert_generator import generate_certificates_for_job

APP_DIR = Path(__file__).parent
JOBS_FILE = APP_DIR / "jobs.json"

TECHNICIANS = ["Brandon", "Hugo", "North"]
TEMPLATE_OPTIONS = ["Brandon Regular", "Hugo Regular", "North Regular"]


def load_jobs():
    if not JOBS_FILE.exists():
        return []
    try:
        return json.loads(JOBS_FILE.read_text())
    except Exception:
        return []


def save_jobs(jobs):
    JOBS_FILE.write_text(json.dumps(jobs, indent=2))


def next_job_id(jobs):
    nums = []
    for job in jobs:
        job_id = str(job.get("job_id", ""))
        if job_id.startswith("JOB-"):
            try:
                nums.append(int(job_id.split("-")[1]))
            except Exception:
                pass
    return f"JOB-{(max(nums) + 1) if nums else 1001}"


def normalize_tech(value):
    value = (value or "").strip()
    for tech in TECHNICIANS:
        if tech.lower() == value.lower():
            return tech
    return value


def job_summary(job):
    return f"{job.get('job_id','')} • {job.get('company','')} • {job.get('status','assigned')} • {len(job.get('instruments', []))} instrument(s)"


def build_job_zip(created_paths):
    zip_path = APP_DIR / "generated_certs" / "job_certificates.zip"
    zip_path.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in created_paths:
            zf.write(path, arcname=path.name)
    return zip_path


st.set_page_config(page_title="Merit Calibration Jobs", layout="wide")
st.title("Merit Calibration Job Queue")
st.caption("Office creates jobs. Technicians open one link and work their assigned jobs.")

params = st.query_params
tech_from_url = normalize_tech(params.get("tech", ""))

jobs = load_jobs()

tab1, tab2, tab3 = st.tabs(["Office - Create Job", "Technician Dashboard", "Office - Review / Status"])

with tab1:
    st.subheader("Create a New Job")
    with st.form("create_job_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            assigned_technician = st.selectbox("Assign Technician", TECHNICIANS)
            template_name = st.selectbox("Template", TEMPLATE_OPTIONS)
            company = st.text_input("Customer / Company")
            address = st.text_input("Address")
        with c2:
            city_state_zip = st.text_input("City / State / Zip")
            location = st.text_input("Location / Site")
            certificate_issue_date = st.text_input("Certificate Issue Date")
            procedure = st.text_input("Procedure", value="MCP-1")
        with c3:
            temperature = st.text_input("Temperature")
            relative_humidity = st.text_input("Relative Humidity")
            rated_tolerance = st.text_input("Rated Tolerance", value="±1°F")
            tolerance_as_found = st.text_input("Tolerance As Found", value="IN")

        st.markdown("**Standards Used**")
        s1, s2, s3 = st.columns(3)
        with s1:
            standard_1 = st.text_input("Standard 1")
        with s2:
            standard_2 = st.text_input("Standard 2")
        with s3:
            standard_3 = st.text_input("Standard 3")

        instrument_count = st.number_input("How many thermometers?", min_value=1, max_value=20, value=3, step=1)

        instruments = []
        st.markdown("**Instrument List**")
        for idx in range(int(instrument_count)):
            with st.expander(f"Instrument {idx + 1}", expanded=(idx == 0)):
                a, b, c = st.columns(3)
                with a:
                    certificate_number = st.text_input(f"Certificate Number #{idx + 1}", key=f"off_cn_{idx}")
                    manufacturer = st.text_input(f"Manufacturer #{idx + 1}", value="LOGTAG", key=f"off_mfg_{idx}")
                with b:
                    instrument = st.text_input(f"Instrument #{idx + 1}", value="DATA LOGGER THERMOMETER", key=f"off_inst_{idx}")
                    model_number = st.text_input(f"Model Number #{idx + 1}", key=f"off_model_{idx}")
                with c:
                    serial_number = st.text_input(f"Serial Number #{idx + 1}", key=f"off_sn_{idx}")
                    identification = st.text_input(f"Identification #{idx + 1}", key=f"off_id_{idx}")
                size_range = st.text_input(f"Size Range #{idx + 1}", key=f"off_rng_{idx}")

                instruments.append({
                    "certificate_number": certificate_number,
                    "manufacturer": manufacturer,
                    "instrument": instrument,
                    "model_number": model_number,
                    "serial_number": serial_number,
                    "identification": identification,
                    "size_range": size_range,
                    "results": []
                })

        submitted = st.form_submit_button("Save Job")

    if submitted:
        job_id = next_job_id(jobs)
        new_job = {
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat(),
            "technician": assigned_technician,
            "template_name": template_name,
            "company": company,
            "address": address,
            "city_state_zip": city_state_zip,
            "location": location,
            "certificate_issue_date": certificate_issue_date,
            "procedure": procedure,
            "temperature": temperature,
            "relative_humidity": relative_humidity,
            "rated_tolerance": rated_tolerance,
            "tolerance_as_found": tolerance_as_found,
            "adjustments_made": "NO",
            "condition_as_found": "FAIR",
            "standard_1": standard_1,
            "standard_2": standard_2,
            "standard_3": standard_3,
            "status": "assigned",
            "instruments": instruments
        }
        jobs.append(new_job)
        save_jobs(jobs)
        st.success(f"Saved {job_id} for {assigned_technician}")

    st.markdown("**How to send this to a technician**")
    st.code("https://your-app-name.streamlit.app/?tech=Brandon", language="text")
    st.info("Replace Brandon with Hugo or North. Each technician can have one permanent link.")

with tab2:
    st.subheader("Technician Dashboard")
    selected_tech = st.selectbox(
        "Technician",
        TECHNICIANS,
        index=TECHNICIANS.index(tech_from_url) if tech_from_url in TECHNICIANS else 0,
    )

    tech_jobs = [j for j in jobs if normalize_tech(j.get("technician")) == selected_tech and j.get("status") != "reviewed"]

    st.write(f"Open jobs for **{selected_tech}**: {len(tech_jobs)}")

    if not tech_jobs:
        st.info("No jobs assigned.")
    else:
        selected_job_summary = st.selectbox("Select Job", [job_summary(j) for j in tech_jobs])
        selected_job = next(j for j in tech_jobs if job_summary(j) == selected_job_summary)

        st.markdown(f"**Customer:** {selected_job.get('company','')}")
        st.markdown(f"**Location:** {selected_job.get('location','')}")
        st.markdown(f"**Template:** {selected_job.get('template_name','')}")
        st.markdown(f"**Status:** {selected_job.get('status','assigned')}")

        updated_instruments = []

        for idx, instrument in enumerate(selected_job.get("instruments", [])):
            with st.expander(f"Instrument {idx + 1} - {instrument.get('serial_number','') or 'No Serial'}", expanded=(idx == 0)):
                st.write(f"Model: {instrument.get('model_number','')}")
                st.write(f"Identification: {instrument.get('identification','')}")
                st.write(f"Certificate #: {instrument.get('certificate_number','')}")

                results = []
                existing_results = instrument.get("results", [])
                for r in range(5):
                    existing = existing_results[r] if r < len(existing_results) else {}
                    a, b, c, d = st.columns(4)
                    with a:
                        point_no = st.number_input(
                            f"Point #{r + 1} / Instrument {idx + 1}",
                            min_value=0,
                            step=1,
                            value=int(existing.get("point_no", r + 1)),
                            key=f"tech_p_{idx}_{r}",
                        )
                    with b:
                        actual_standard = st.number_input(
                            f"Actual {r + 1} / Instrument {idx + 1}",
                            value=float(existing.get("actual_standard", 40.0)),
                            step=0.1,
                            key=f"tech_a_{idx}_{r}",
                        )
                    with c:
                        as_found = st.number_input(
                            f"UUT {r + 1} / Instrument {idx + 1}",
                            value=float(existing.get("as_found", 40.0)),
                            step=0.1,
                            key=f"tech_f_{idx}_{r}",
                        )
                    with d:
                        use_row = st.checkbox(
                            f"Use row {r + 1} / Instrument {idx + 1}",
                            value=bool(existing) if existing else (r < 3),
                            key=f"tech_use_{idx}_{r}",
                        )

                    if use_row:
                        results.append({
                            "point_no": point_no,
                            "actual_standard": actual_standard,
                            "as_found": as_found,
                        })

                updated = dict(instrument)
                updated["results"] = results
                updated_instruments.append(updated)

        c1, c2, c3 = st.columns(3)
        save_progress = c1.button("Save Progress")
        generate_certs = c2.button("Generate Certificates")
        mark_completed = c3.button("Mark Job Completed")

        if save_progress or generate_certs or mark_completed:
            for job in jobs:
                if job.get("job_id") == selected_job.get("job_id"):
                    job["instruments"] = updated_instruments
                    if save_progress and job.get("status") == "assigned":
                        job["status"] = "in_progress"
                    if mark_completed:
                        job["status"] = "completed"
            save_jobs(jobs)

        if save_progress:
            st.success("Progress saved.")

        if mark_completed:
            st.success("Job marked completed.")

        if generate_certs:
            job_for_generation = next(j for j in jobs if j.get("job_id") == selected_job.get("job_id"))
            job_data = {
                "company": job_for_generation.get("company"),
                "address": job_for_generation.get("address"),
                "city_state_zip": job_for_generation.get("city_state_zip"),
                "technician": job_for_generation.get("technician"),
                "procedure": job_for_generation.get("procedure"),
                "rated_tolerance": job_for_generation.get("rated_tolerance"),
                "tolerance_as_found": job_for_generation.get("tolerance_as_found"),
                "adjustments_made": job_for_generation.get("adjustments_made"),
                "condition_as_found": job_for_generation.get("condition_as_found"),
                "location": job_for_generation.get("location"),
                "temperature": job_for_generation.get("temperature"),
                "relative_humidity": job_for_generation.get("relative_humidity"),
                "certificate_issue_date": job_for_generation.get("certificate_issue_date"),
                "standard_1": job_for_generation.get("standard_1"),
                "standard_2": job_for_generation.get("standard_2"),
                "standard_3": job_for_generation.get("standard_3"),
            }
            created = generate_certificates_for_job(
                job_data=job_data,
                instruments=job_for_generation.get("instruments", []),
                template_name=job_for_generation.get("template_name"),
            )
            zip_path = build_job_zip(created)
            st.success(f"Created {len(created)} certificate(s).")
            with open(zip_path, "rb") as f:
                st.download_button("Download All Certificates (ZIP)", data=f, file_name=zip_path.name, mime="application/zip")

with tab3:
    st.subheader("Review / Status")
    if not jobs:
        st.info("No jobs yet.")
    else:
        status_filter = st.selectbox("Filter by Status", ["all", "assigned", "in_progress", "completed", "reviewed"])
        filtered = jobs if status_filter == "all" else [j for j in jobs if j.get("status") == status_filter]

        for job in filtered:
            with st.expander(job_summary(job)):
                st.write(json.dumps(job, indent=2))
                col1, col2 = st.columns(2)
                if col1.button(f"Mark Reviewed - {job.get('job_id')}", key=f"review_{job.get('job_id')}"):
                    for j in jobs:
                        if j.get("job_id") == job.get("job_id"):
                            j["status"] = "reviewed"
                    save_jobs(jobs)
                    st.success(f"{job.get('job_id')} marked reviewed.")
                if col2.button(f"Delete Job - {job.get('job_id')}", key=f"delete_{job.get('job_id')}"):
                    jobs = [j for j in jobs if j.get("job_id") != job.get("job_id")]
                    save_jobs(jobs)
                    st.success(f"{job.get('job_id')} deleted.")
