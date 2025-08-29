# scripts/generate_dummy_data.py
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

import numpy as np
from app.db import get_conn

# ==== knobs you can tweak ====
N_TXNS = 1500          # how many transactions to add (approx; transfers create 2 rows)
DAYS_BACK = 60        # spread transactions over the last N days
FRAUD_RATE = 0.20     # ~10% of txns will look suspicious
SEED = 42
# ============================

random.seed(SEED)
np.random.seed(SEED)

CHANNELS = ["BRANCH", "ATM", "ONLINE", "MOBILE"]
CITIES_BY_REGION = {
    "North":  ["Delhi", "Jaipur", "Chandigarh", "Lucknow"],
    "West":   ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "South":  ["Chennai", "Bengaluru", "Hyderabad", "Kochi"],
    "East":   ["Kolkata", "Patna", "Bhubaneswar", "Guwahati"],
    None:     ["Metro"]
}

def _random_time_within(days_back: int) -> datetime:
    # Bias a bit toward recent days
    delta_days = int(np.random.beta(2, 6) * days_back)
    dt = datetime.now() - timedelta(days=delta_days, hours=random.randint(0,23), minutes=random.randint(0,59))
    return dt.replace(second=random.randint(0,59), microsecond=0)

def _lognormal_amount(mu=8.5, sigma=0.7) -> float:
    # gives a skewed distribution around a few thousand to tens of thousands
    return float(max(100, np.random.lognormal(mean=mu, sigma=sigma)))

def _choose_location(region: Optional[str]) -> str:
    return random.choice(CITIES_BY_REGION.get(region, CITIES_BY_REGION[None]))

def fetch_accounts() -> List[Dict]:
    sql = """
      SELECT a.account_id, a.customer_id, a.balance, c.region
      FROM Account a
      JOIN Customer c ON c.customer_id = a.customer_id
      WHERE a.status='ACTIVE'
    """
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()

def insert_transactions(rows):
    """
    rows: (account_id, txn_time, txn_type, amount, counterparty_account, channel, location)
    Cast NumPy types -> native Python so mysql-connector is happy.
    """
    def norm(row):
        acc_id, when, ttype, amt, cpa, channel, location = row
        return (
            int(acc_id),
            when,                         # datetime OK
            str(ttype),
            float(amt),
            (int(cpa) if cpa is not None else None),
            str(channel),
            str(location),
        )

    clean_rows = [norm(r) for r in rows]

    sql = """INSERT INTO Transaction
             (account_id, txn_time, txn_type, amount, counterparty_account, channel, location)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(sql, clean_rows)

def update_balances(balance_deltas: Dict[int, float]):
    with get_conn() as conn:
        cur = conn.cursor()
        for acc_id, delta in balance_deltas.items():
            cur.execute("UPDATE Account SET balance = balance + %s WHERE account_id=%s", (delta, acc_id))

def sprinkle_loans():
    """Make loan stats more interesting: approve some, reject some, disburse a few."""
    with get_conn() as conn:
        cur = conn.cursor()
        # Approve all 'APPLIED', half reject randomly, some disburse
        cur.execute("UPDATE Loan SET status='APPROVED' WHERE status='APPLIED'")
        # randomly reject ~30% of approved
        cur.execute("UPDATE Loan SET status='REJECTED' WHERE status='APPROVED' AND RAND() < 0.3")
        # from remaining approved, disburse ~50%
        cur.execute("UPDATE Loan SET status='DISBURSED' WHERE status='APPROVED' AND RAND() < 0.5")

def generate():
    accts = fetch_accounts()
    if len(accts) < 2:
        print("Need at least 2 active accounts to generate transfers. Add more accounts if possible.")
    acct_ids = [a["account_id"] for a in accts]
    by_id = {a["account_id"]: a for a in accts}
    rows = []
    bal_delta = {}  # track net balance change per account

    for i in range(N_TXNS):
        # pick a primary account (weight larger balances slightly higher)
        weights = np.array([max(1.0, math.log1p(a["balance"])) for a in accts], dtype=float)
        weights /= weights.sum()
        acc = np.random.choice(accts, p=weights)

        # choose type (transfers create 2 rows)
        txn_type = np.random.choice(["DEPOSIT","WITHDRAW","TRANSFER"], p=[0.40, 0.35, 0.25])

        # set base amount
        amt = _lognormal_amount()

        # fraudify ~FRAUD_RATE: make amount extreme or odd channel combos
        is_fraud_like = (np.random.rand() < FRAUD_RATE)
        if is_fraud_like:
            # spike amount (very large withdrawal/transfer) or odd micro-transactions
            if np.random.rand() < 0.7:
                amt *= np.random.uniform(8, 20)   # very large
            else:
                amt = np.random.choice([199, 299, 499, 999])  # odd splits

        when = _random_time_within(DAYS_BACK)
        channel = random.choice(CHANNELS)
        location = _choose_location(acc.get("region"))

        if txn_type == "DEPOSIT":
            rows.append((int(acc["account_id"]), when, "DEPOSIT", float(round(amt, 2)),None, channel, location))
            bal_delta[acc["account_id"]] = bal_delta.get(acc["account_id"], 0.0) + amt

        elif txn_type == "WITHDRAW":
            # keep within balance to avoid negatives (demo)
            amt = min(amt, max(100.0, float(by_id[acc["account_id"]]["balance"]) + bal_delta.get(acc["account_id"], 0.0)))
            rows.append((int(acc["account_id"]), when, "WITHDRAW", float(round(amt, 2)),None, channel, location))
            bal_delta[acc["account_id"]] = bal_delta.get(acc["account_id"], 0.0) - amt

        else:  # TRANSFER
            # pick a different account
            dst = acc["account_id"]
            while dst == acc["account_id"] and len(acct_ids) > 1:
                dst = random.choice(acct_ids)
            # keep within balance
            amt = min(amt, max(100.0, float(by_id[acc["account_id"]]["balance"]) + bal_delta.get(acc["account_id"], 0.0)))
            rows.append((int(acc["account_id"]), when, "TRANSFER_OUT", float(round(amt, 2)),int(dst), channel, location))
            rows.append((int(dst), when, "TRANSFER_IN", float(round(amt, 2)),int(acc["account_id"]), channel, _choose_location(by_id[int(dst)].get("region"))))
            bal_delta[acc["account_id"]] = bal_delta.get(acc["account_id"], 0.0) - amt
            bal_delta[dst] = bal_delta.get(dst, 0.0) + amt

    insert_transactions(rows)
    update_balances(bal_delta)
    sprinkle_loans()
    print(f"Inserted {len(rows)} transaction rows (~{N_TXNS} events). Updated balances for {len(bal_delta)} accounts.")

def score_new():
    # run the existing model to fill FraudScore
    from app.fraud_model import run_model
    flagged = run_model()
    print(f"Fraud model scored. Newly flagged: {flagged}")

def generate_loans(n=100):
    """Insert n synthetic loan applications across all customers/regions."""
    # Fetch all customers
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT customer_id, region FROM Customer")
        customers = cur.fetchall()

    statuses = ["APPLIED", "APPROVED", "REJECTED", "DISBURSED", "CLOSED"]
    rows = []
    for i in range(n):
        cust = random.choice(customers)
        cust_id = cust["customer_id"]
        amount = round(random.uniform(50000, 800000), 2)
        interest = round(random.uniform(7.5, 14.5), 2)
        tenure = random.choice([12, 24, 36, 48, 60])
        status = random.choices(
            statuses, weights=[0.2, 0.3, 0.2, 0.2, 0.1], k=1
        )[0]
        rows.append((cust_id, amount, interest, tenure, status))

    sql = """
      INSERT INTO Loan (customer_id, amount, interest_rate, tenure_months, status)
      VALUES (%s, %s, %s, %s, %s)
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(sql, rows)

    print(f"✓ Inserted {len(rows)} synthetic loans for {len(customers)} customers across regions.")

def main():
    generate()
    score_new()
    generate_loans(180)
    print("Done.")

if __name__ == "__main__":
    main()
