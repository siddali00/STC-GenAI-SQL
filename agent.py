# agent_simple.py

import os
import re

import cohere
from sqlalchemy import text
from database import SessionLocal

# 1) Config & client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key=COHERE_API_KEY)

# 2) Helper: execute SQL & format markdown table
def run_sql(sql: str) -> str:
    # strip any fences
    m = re.search(r'```sql\s*(.*?)\s*```', sql, re.DOTALL)
    clean_sql = m.group(1).strip() if m else sql.strip()

    session = SessionLocal()
    try:
        result = session.execute(text(clean_sql))
        rows   = result.fetchall()
        cols   = result.keys()
    finally:
        session.close()

    if not rows:
        return "No rows returned."

    # build markdown
    header = list(cols)
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |"
    ]
    for row in rows[:10]:
        vals = [str(row._mapping[col]) for col in header]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

# 3) Agent: schema-only prompt → SQL → run
def query_assistant(user_question: str) -> str:
    schema_description = """
Tables available:
- sales(date DATE, region TEXT, product TEXT, units_sold INTEGER, revenue NUMERIC)
- churn(month DATE, segment TEXT, churned_customers INTEGER)
"""
    system_prompt = (
        "You are a SQL assistant. Given a natural-language question and a database schema, generate a valid PostgreSQL query. Return ONLY the SQL, no explanation."
    )
    user_prompt = f"{schema_description}\nQuestion: {user_question}"

    resp = co.chat(
        model="command-r-08-2024",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    sql = resp.message.content[0].text.strip()
    print("🔍 Generated SQL:\n", sql)

    try:
        results = run_sql(sql)
        return f"**SQL:**\n```sql\n{sql}\n```\n\n**Results:**\n{results}"
    except Exception as e:
        return f"Error executing SQL: {e}\n\nGenerated SQL:\n{sql}"

# 4) CLI test harness
if __name__ == "__main__":
    for q in [
        "What were the sales numbers by region last quarter?",
        "Which customer segments had the highest churn last month?",
        "ما هي نسبة النمو في الإيرادات مقارنة بالعام الماضي؟"
    ]:
        print(f"\n🔹 Question: {q}\n")
        print(query_assistant(q))
