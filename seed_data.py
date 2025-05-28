import pandas as pd
from sqlalchemy import text
from database import SessionLocal, Sales, Churn

def seed():
    # 1) Read CSVs
    sales_df = pd.read_csv("data/sales.csv", parse_dates=["date"])
    churn_df = pd.read_csv("data/churn.csv", parse_dates=["month"])

    # Remove duplicates based on the composite primary key columns
    print(f"Sales data: {len(sales_df)} rows before deduplication")
    sales_df = sales_df.drop_duplicates(subset=['date', 'region', 'product'], keep='last')
    print(f"Sales data: {len(sales_df)} rows after deduplication")
    
    print(f"Churn data: {len(churn_df)} rows before deduplication")
    churn_df = churn_df.drop_duplicates(subset=['month', 'segment'], keep='last')
    print(f"Churn data: {len(churn_df)} rows after deduplication")

    # 2) Open a session
    session = SessionLocal()

    try:
        # 3) Truncate existing data - use separate statements
        session.execute(text("TRUNCATE TABLE sales"))
        session.execute(text("TRUNCATE TABLE churn"))
        session.commit()  # Commit the truncate operations
        print("✅ Tables truncated successfully")

        # 4) Bulk-insert mappings for performance
        session.bulk_insert_mappings(Sales, sales_df.to_dict(orient="records"))
        session.bulk_insert_mappings(Churn, churn_df.to_dict(orient="records"))

        # 5) Commit & close
        session.commit()
        print("✅ Tables truncated and data re-seeded into sales & churn.")
        print(f"✅ Inserted {len(sales_df)} sales records and {len(churn_df)} churn records.")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed()
