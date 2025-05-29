import os
from sqlalchemy import (
    create_engine,
    Column,
    Date,
    DateTime,
    Integer,
    Text,
    Numeric,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. "postgresql://user:pass@host:port/db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# -------------------------------------------------------------------
# Existing Tables
# -------------------------------------------------------------------
class Sales(Base):
    __tablename__ = "sales"
    date       = Column(Date,   primary_key=True)
    region     = Column(Text,   primary_key=True)
    product    = Column(Text,   primary_key=True)
    units_sold = Column(Integer, nullable=False)
    revenue    = Column(Numeric(10, 2), nullable=False)

class Churn(Base):
    __tablename__ = "churn"
    month             = Column(Date, primary_key=True)
    segment           = Column(Text, primary_key=True)
    churned_customers = Column(Integer, nullable=False)

# -------------------------------------------------------------------
# New Tables for Use Case #1
# -------------------------------------------------------------------
class Job(Base):
    __tablename__ = "jobs"
    job_name    = Column(Text, primary_key=True)
    description = Column(Text, nullable=False)
    owner       = Column(Text, nullable=False)

class JobLog(Base):
    __tablename__ = "job_logs"
    log_id        = Column(Integer, primary_key=True, autoincrement=True)
    job_name      = Column(Text, ForeignKey("jobs.job_name"), nullable=False)
    run_timestamp = Column(DateTime, nullable=False)
    status        = Column(Text, nullable=False)  # e.g. 'SUCCESS' or 'FAILURE'
    message       = Column(Text, nullable=False)

class IncidentKB(Base):
    __tablename__ = "incident_kb"
    error_pattern = Column(Text, primary_key=True)  # SQL LIKE pattern
    root_cause_en = Column(Text, nullable=False)
    resolution_en = Column(Text, nullable=False)
    root_cause_ar = Column(Text, nullable=False)
    resolution_ar = Column(Text, nullable=False)

# -------------------------------------------------------------------
# Initialization
# -------------------------------------------------------------------
def init_db():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------------
# Script entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("✅ Tables 'sales','churn','jobs','job_logs','incident_kb' created.")
