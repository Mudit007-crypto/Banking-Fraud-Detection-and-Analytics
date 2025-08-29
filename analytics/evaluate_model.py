# analytics/evaluate_model.py
"""
Evaluate fraud model performance.

By default this pulls from MySQL (via app.db.get_conn), uses the latest
FraudScore per txn_id, treats transactions with reason containing
'Amount z-score high' as TRUE FRAUD (1), and uses the model's 'flagged'
as the prediction (1/0). You can also override the threshold to rebuild
predictions from anomaly_score.

Outputs:
- prints metrics to console
- saves confusion_matrix.csv, metrics.json
- saves roc.png, pr_curve.png in analytics/exports/
"""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve
)
import matplotlib.pyplot as plt

# our DB connector
from app.db import get_conn


EXPORT_DIR = Path("analytics/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_latest_scores():
    """Fetch FraudScore and keep the latest row per txn_id."""
    q = """
        SELECT score_id, txn_id, anomaly_score, flagged, reason, scored_at
        FROM FraudScore
        ORDER BY score_id ASC
    """
    with get_conn() as conn:
        df = pd.read_sql(q, conn)

    # keep last (latest) row per txn_id by score_id
    latest = df.groupby("txn_id", as_index=False).tail(1).reset_index(drop=True)
    # normalize types
    latest["flagged"] = latest["flagged"].astype(int)
    latest["anomaly_score"] = latest["anomaly_score"].astype(float)
    latest["reason"] = latest["reason"].astype(str)
    return latest


def label_from_reason(df: pd.DataFrame, keyword: str = "Amount z-score high") -> pd.Series:
    """Ground-truth labels from 'reason' substring."""
    return df["reason"].str.contains(keyword, case=False, na=False).astype(int)


def try_label_from_transaction_flag():
    """
    If you later add Transaction.is_fraud ground truth, we can use it here.
    This function tries to fetch it; if not present, returns None.
    """
    q = """
    SELECT fs.txn_id, t.is_fraud
    FROM FraudScore fs
    JOIN Transaction t ON t.txn_id = fs.txn_id
    LIMIT 1
    """
    try:
        with get_conn() as conn:
            df = pd.read_sql(q, conn)
        if "is_fraud" in df.columns:
            return True
    except Exception:
        pass
    return False


def evaluate(latest: pd.DataFrame, y_true: pd.Series, y_pred: pd.Series):
    """Compute core metrics and plots; return dict with key numbers."""
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Classification report
    report = classification_report(y_true, y_pred, output_dict=True)

    # ROC/PR using continuous scores
    scores = latest["anomaly_score"].values
    fpr, tpr, _ = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)
    prec, rec, _ = precision_recall_curve(y_true, scores)

    # Save numeric outputs
    pd.DataFrame(cm, index=["Actual 0", "Actual 1"], columns=["Pred 0", "Pred 1"])\
        .to_csv(EXPORT_DIR / "confusion_matrix.csv", index=True)
    with open(EXPORT_DIR / "metrics.json", "w") as f:
        json.dump({
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "accuracy": report["accuracy"],
            "precision_fraud": report["1"]["precision"],
            "recall_fraud": report["1"]["recall"],
            "f1_fraud": report["1"]["f1-score"],
            "precision_legit": report["0"]["precision"],
            "recall_legit": report["0"]["recall"],
            "f1_legit": report["0"]["f1-score"],
            "roc_auc": roc_auc
        }, f, indent=2)

    # ROC plot
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], "k--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title("ROC Curve - Fraud Detection")
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(EXPORT_DIR / "roc.png", dpi=160)
    plt.close()

    # Precision-Recall plot
    plt.figure(figsize=(6, 5))
    plt.plot(rec, prec)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall Curve - Fraud Detection")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(EXPORT_DIR / "pr_curve.png", dpi=160)
    plt.close()

    return {
        "cm": cm,
        "report": report,
        "roc_auc": roc_auc
    }


def main():
    ap = argparse.ArgumentParser(description="Evaluate fraud model using latest FraudScore rows.")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Optional: override prediction threshold; if set, y_pred = (anomaly_score >= threshold). "
                         "If omitted, uses the stored 'flagged' column.")
    ap.add_argument("--ground-truth", choices=["reason", "transaction"], default="reason",
                    help="Where to read true labels from. 'reason' (default) looks for the keyword "
                         "'Amount z-score high'. 'transaction' expects a Transaction.is_fraud column.")
    ap.add_argument("--keyword", default="Amount z-score high",
                    help="Keyword to detect true fraud in reason (used when --ground-truth=reason).")
    args = ap.parse_args()

    latest = fetch_latest_scores()

    # Ground truth labels
    if args.ground_truth == "transaction" and try_label_from_transaction_flag():
        q = """
        WITH latest AS (
          SELECT txn_id, MAX(score_id) AS max_sid
          FROM FraudScore
          GROUP BY txn_id
        )
        SELECT fs.txn_id, t.is_fraud
        FROM FraudScore fs
        JOIN latest l ON l.txn_id = fs.txn_id AND l.max_sid = fs.score_id
        JOIN Transaction t ON t.txn_id = fs.txn_id
        """
        with get_conn() as conn:
            truth_df = pd.read_sql(q, conn)
        y_true = truth_df.set_index("txn_id").loc[latest["txn_id"]]["is_fraud"].astype(int).values
    else:
        y_true = label_from_reason(latest, args.keyword).values

    # Predictions: either stored 'flagged' or recomputed threshold
    if args.threshold is not None:
        y_pred = (latest["anomaly_score"].values >= args.threshold).astype(int)
    else:
        y_pred = latest["flagged"].values

    results = evaluate(latest, y_true, y_pred)

    # Console summary (nice & short)
    cm = results["cm"]
    tn, fp, fn, tp = cm.ravel()
    rep = results["report"]
    print("\n=== Confusion Matrix ===")
    print(pd.DataFrame(cm, index=["Actual 0", "Actual 1"], columns=["Pred 0", "Pred 1"]))
    print("\n=== Key Metrics ===")
    print(f"Accuracy:        {rep['accuracy']:.4f}")
    print(f"Precision (1):   {rep['1']['precision']:.4f}")
    print(f"Recall    (1):   {rep['1']['recall']:.4f}")
    print(f"F1-score  (1):   {rep['1']['f1-score']:.4f}")
    print(f"ROC AUC:         {results['roc_auc']:.4f}")
    print(f"\nSaved plots + files in: {EXPORT_DIR.resolve()}")


if __name__ == "__main__":
    main()
