import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
from database import (
    SessionLocal,
    Sales,
    Churn,
    Job,
    JobLog,
    IncidentKB
)

def seed():
    session = SessionLocal()

    try:
        # ── 1) Truncate all tables ──────────────────────────
        session.execute(text("TRUNCATE TABLE job_logs, incident_kb, jobs, sales, churn RESTART IDENTITY CASCADE"))
        session.commit()
        print("✅ All tables truncated.")

        # ── 2) Seed sales & churn (as before) ──────────────
        sales_df = pd.read_csv("data/sales.csv", parse_dates=["date"])
        churn_df = pd.read_csv("data/churn.csv", parse_dates=["month"])

        # Deduplicate if needed
        sales_df = sales_df.drop_duplicates(subset=["date","region","product"])
        churn_df = churn_df.drop_duplicates(subset=["month","segment"])

        session.bulk_insert_mappings(Sales, sales_df.to_dict(orient="records"))
        session.bulk_insert_mappings(Churn, churn_df.to_dict(orient="records"))
        session.commit()
        print(f"✅ Seeded {len(sales_df)} sales rows and {len(churn_df)} churn rows.")

        # ── 3) Seed jobs metadata ───────────────────────────
        jobs = [
            {"job_name":"daily_load",      "description":"Ingest raw data daily",     "owner":"data_eng"},
            {"job_name":"aggregate_sales", "description":"Aggregate sales metrics",    "owner":"analytics"},
            {"job_name":"churn_calc",      "description":"Compute monthly churn",     "owner":"analytics"},
        ]
        session.bulk_insert_mappings(Job, jobs)
        session.commit()
        print(f"✅ Seeded {len(jobs)} jobs.")

        # ── 4) Seed incident knowledge base ─────────────────
        kb = [
            {
                "error_pattern": "%Connection refused%",
                "root_cause_en":"Database connection refused",
                "resolution_en":"Verify DB credentials and network access",
                "root_cause_ar":"تم رفض اتصال قاعدة البيانات",
                "resolution_ar":"تحقق من بيانات الاعتماد والشبكة"
            },
            {
                "error_pattern": "%timeout%",
                "root_cause_en":"Operation timed out",
                "resolution_en":"Increase timeout settings or optimize query",
                "root_cause_ar":"انتهت مهلة العملية",
                "resolution_ar":"قم بزيادة إعداد المهلة أو تحسين الاستعلام"
            },
            {
                "error_pattern": "%NullPointerException%",
                "root_cause_en":"Null pointer dereference",
                "resolution_en":"Check for missing data or initialize variables",
                "root_cause_ar":"إشارة إلى مؤشر خالي",
                "resolution_ar":"تحقق من البيانات المفقودة أو قم بتهيئة المتغيرات"
            }
        ]
        session.bulk_insert_mappings(IncidentKB, kb)
        session.commit()
        print(f"✅ Seeded {len(kb)} incident knowledge entries.")

        # ── 5) Seed synthetic job logs ───────────────────────
        job_logs = []
        now = datetime.utcnow()
        for job in jobs:
            # 20 runs over the past 7 days
            for i in range(20):
                ts = now - timedelta(hours= i * 8 )
                # 80% success, 20% failure
                status  = np.random.choice(["SUCCESS","FAILURE"], p=[0.8,0.2])
                if status == "SUCCESS":
                    msg = f"Job {job['job_name']} completed successfully at {ts.isoformat()}."
                else:
                    # pick one of the KB patterns
                    err = np.random.choice([kb[0]["error_pattern"],
                                            kb[1]["error_pattern"],
                                            kb[2]["error_pattern"]])
                    # make a concrete message
                    sample_err = err.strip("%") + " encountered"
                    msg = f"Error in {job['job_name']}: {sample_err}"
                job_logs.append({
                    "job_name": job["job_name"],
                    "run_timestamp": ts,
                    "status": status,
                    "message": msg
                })

        session.bulk_insert_mappings(JobLog, job_logs)
        session.commit()
        print(f"✅ Seeded {len(job_logs)} job log entries.")

    except Exception as e:
        session.rollback()
        print("❌ Error during seeding:", e)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed()
