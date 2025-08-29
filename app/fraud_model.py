import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from app.db import get_conn

def fetch_recent_txns(limit=20000):
    with get_conn() as conn:
        q = """
        SELECT t.txn_id, t.account_id, t.amount, t.channel, t.location, t.txn_time,
               a.customer_id, c.region
        FROM Transaction t
        JOIN Account a ON a.account_id = t.account_id
        JOIN Customer c ON c.customer_id = a.customer_id
        ORDER BY t.txn_time DESC
        LIMIT %s
        """
        df = pd.read_sql(q, conn, params=(limit,))
    return df

def featurize(df: pd.DataFrame):
    df = df.copy()
    # Encode simple features
    df["channel_code"] = df["channel"].astype("category").cat.codes
    df["region_code"] = df["region"].astype("category").cat.codes
    # Per-account stats
    grp = df.groupby("account_id")["amount"]
    df["z_by_account"] = (df["amount"] - grp.transform("mean")) / (grp.transform("std").replace(0,1))
    X = df[["amount","channel_code","region_code","z_by_account"]].fillna(0).to_numpy()
    return df, X

def score_and_write(df, scores):
    # IsolationForest returns negative scores for anomalies; invert to make higher=more suspicious
    norm = (scores.min(), scores.max())
    if norm[1] - norm[0] == 0:
        proba = np.zeros_like(scores)
    else:
        proba = (scores - norm[0]) / (norm[1] - norm[0])

    flagged = proba > 0.65  # threshold (tunable)
    reasons = np.where(df["z_by_account"].abs() > 2.5, "Amount z-score high", "IForest anomaly")
    rows = list(zip(df["txn_id"].tolist(), proba.tolist(), flagged.tolist(), reasons.tolist()))

    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO FraudScore (txn_id, anomaly_score, flagged, reason) VALUES (%s,%s,%s,%s)",
            rows
        )
    return int(flagged.sum())

def run_model():
    df = fetch_recent_txns()
    if df.empty:
        return 0
    df_f, X = featurize(df)
    clf = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
    clf.fit(X)
    scores = -clf.decision_function(X)  # higher => more anomalous
    flagged = score_and_write(df_f, scores)
    return flagged

if __name__ == "__main__":
    n = run_model()
    print(f"Flagged {n} suspicious transactions.")
