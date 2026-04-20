Merit Calibration Job Queue Starter

What this adds:
- Office creates many jobs
- Each job is assigned to Brandon, Hugo, or North
- Each technician can use one permanent link:
  https://your-app-name.streamlit.app/?tech=Brandon
- Technician sees only assigned jobs
- Technician enters readings and generates all certificates for a selected job
- Office can review status

Files:
- app_jobs_dashboard.py
- jobs.json

Important limitation for Streamlit Community Cloud:
- This starter saves jobs to a local JSON file.
- Streamlit docs note that Community Cloud does NOT guarantee persistence of local file storage.
- That means jobs.json is good for testing / proof of concept, but not reliable as your long-term production database.

Recommended next step after you test this:
- move jobs into SQLite, Google Sheets, Supabase, Airtable, or another hosted database

How to test locally:
python -m streamlit run app_jobs_dashboard.py

How to deploy:
1. Upload app_jobs_dashboard.py and jobs.json to your GitHub repo
2. In Streamlit, set the main file to app_jobs_dashboard.py
3. Redeploy
