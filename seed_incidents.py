import pandas as pd
from sqlalchemy import text
from database import SessionLocal, Job, JobLog, IncidentKB

def seed_incidents():
    session = SessionLocal()
    try:
        # Truncate existing
        session.execute(text("TRUNCATE TABLE job_logs, incident_kb, jobs RESTART IDENTITY CASCADE"))
        session.commit()

        # Read CSVs
        jobs_df = pd.read_csv("data/jobs.csv")
        kb_df   = pd.read_csv("data/incident_kb.csv")
        logs_df = pd.read_csv("data/job_logs.csv", parse_dates=["run_timestamp"])

        # Bulk insert
        session.bulk_insert_mappings(Job,       jobs_df.to_dict(orient="records"))
        session.bulk_insert_mappings(IncidentKB, kb_df.to_dict(orient="records"))
        session.bulk_insert_mappings(JobLog,    logs_df.to_dict(orient="records"))

        session.commit()
        print("✅ Seeded jobs, incident_kb, and job_logs.")
    except Exception as e:
        session.rollback()
        print("❌ Error during seeding incidents data:", e)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_incidents()
