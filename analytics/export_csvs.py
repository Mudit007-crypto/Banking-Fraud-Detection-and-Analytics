# analytics/export_csvs.py
import sys
import os
from pathlib import Path
import pandas as pd
from app.db import get_conn
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
EXPORT_DIR = Path("analytics/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def to_csv(df: pd.DataFrame, name: str):
    out = EXPORT_DIR / name
    df.to_csv(out, index=False)
    print(f"✓ wrote {out.resolve()}  ({len(df)} rows)")

def q(sql: str, params=None) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=params)

def export_transactions_daily():
    sql = """
        SELECT DATE(txn_time) AS day,
               COUNT(*) AS txn_count,
               SUM(amount) AS total_amount
        FROM Transaction
        GROUP BY day
        ORDER BY day;
    """
    to_csv(q(sql), "transactions_daily.csv")

def export_fraud_by_region():
    sql = """
        SELECT c.region,
               ROUND(AVG(fs.anomaly_score), 4) AS avg_fraud_prob,
               SUM(fs.flagged) AS flags,
               COUNT(*) AS scored_rows
        FROM FraudScore fs
        JOIN Transaction t ON t.txn_id = fs.txn_id
        JOIN Account a ON a.account_id = t.account_id
        JOIN Customer c ON c.customer_id = a.customer_id
        GROUP BY c.region
        ORDER BY avg_fraud_prob DESC;
    """
    to_csv(q(sql), "fraud_by_region.csv")

def export_loan_stats():
    sql = """
        SELECT status,
               COUNT(*) AS cnt,
               SUM(amount) AS total_amount
        FROM Loan
        GROUP BY status
        ORDER BY cnt DESC;
    """
    to_csv(q(sql), "loan_stats.csv")

def main():
    export_transactions_daily()
    export_fraud_by_region()
    export_loan_stats()
    print("\nAll exports done. Use these in Tableau Public (Connect → Text file).")

if __name__ == "__main__":
    main()
