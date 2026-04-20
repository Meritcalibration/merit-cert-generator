Merit Calibration Job-Based Starter

This version is built for field work.

Workflow:
1. Office pre-fills one job
2. Technician enters data for multiple thermometers
3. App generates one certificate per instrument

Files needed in the same folder:
- app.py
- cert_generator.py
- Cert Template Revised (Brandon).xlsx
- Cert Template Revised (Hugo).xlsx
- Cert Template Revised (North).xlsx

Run:
pip install -r requirements.txt
python -m streamlit run app.py

What is new:
- Supports Brandon, Hugo, and North regular templates
- One job can generate multiple certificates
- Shared customer/job info only entered once
- Each thermometer gets its own results section
- Download all certificates as a ZIP file

Recommended next upgrades:
- auto certificate numbering
- customer presets
- pass/fail logic
- PDF export
