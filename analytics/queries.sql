-- 1) Transaction volume per day
SELECT DATE(txn_time) AS day, COUNT(*) AS txn_count, SUM(amount) AS total_amount
FROM Transaction
GROUP BY day
ORDER BY day;

-- 2) Fraud probability per region (avg anomaly score + count of flags)
SELECT c.region, ROUND(AVG(fs.anomaly_score),4) AS avg_fraud_prob, SUM(fs.flagged) AS flags
FROM FraudScore fs
JOIN Transaction t ON t.txn_id = fs.txn_id
JOIN Account a ON a.account_id = t.account_id
JOIN Customer c ON c.customer_id = a.customer_id
GROUP BY c.region
ORDER BY avg_fraud_prob DESC;

-- 3) Loan approval stats
SELECT status, COUNT(*) AS cnt, SUM(amount) AS total_amount
FROM Loan
GROUP BY status
ORDER BY cnt DESC;

-- 4) Top suspicious recent transactions
SELECT fs.scored_at, fs.anomaly_score, fs.flagged, fs.reason,
       t.txn_id, t.account_id, t.amount, t.channel, t.location
FROM FraudScore fs
JOIN Transaction t ON t.txn_id = fs.txn_id
ORDER BY fs.scored_at DESC
LIMIT 20;