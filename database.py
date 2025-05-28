import os
from sqlalchemy import (
    create_engine, Column, Date, Integer, Text, Numeric
)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
)

print(DATABASE_URL)


engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine  
)

Base = declarative_base()


class Sales(Base):
    __tablename__ = "sales"
    # Composite primary key to avoid duplicates
    date = Column(Date, primary_key=True)
    region = Column(Text, primary_key=True)
    product = Column(Text, primary_key=True)
    units_sold = Column(Integer, nullable=False)
    revenue = Column(Numeric(10, 2), nullable=False)

class Churn(Base):
    __tablename__ = "churn"
    month = Column(Date, primary_key=True)
    segment = Column(Text, primary_key=True)
    churned_customers = Column(Integer, nullable=False)


def init_db():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("✅ Tables 'sales' and 'churn' are created (if not already present).")
