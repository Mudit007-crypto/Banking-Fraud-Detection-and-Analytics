🏦 Banking Fraud Detection & Analytics

A complete mini-banking system that manages accounts, loans, and transactions, detects fraud in real-time using machine learning, and visualizes analytics in Tableau.

✨ Features
🔹 Core Banking (MySQL 8.0 + Python)

Customers: deposit, withdraw, transfer, apply for loans.

Employees: approve/reject loans, view customer history.

Admins: manage accounts, transactions, employee roles.

Authentication: users stored with SHA-256 + UTF-8 password hashing.

🔹 Fraud Detection (AI / ML)

Isolation Forest anomaly detection model.

Features used: transaction amount, channel, region, per-account z-score.

Suspicious transactions flagged with reasons → saved in FraudScore.

Evaluation pipeline gives precision, recall, F1, ROC, PR curves.

Current performance (on dummy data):

Accuracy ≈ 99%

Precision (fraud) ≈ 84%

Recall (fraud) ≈ 91%

F1 ≈ 87%

🔹 Analytics (Tableau Public)

Transactions per day → Line chart (volume & amounts).

Fraud probability by region → Pie chart (flags & scores).

Loan approval stats → Bar chart (loan counts & total amounts).

Exported via Python → analytics/exports/*.csv.

🔐 Security Note

Passwords hashed with SHA-256 over UTF-8 encoded bytes.

For production, use stronger schemes like bcrypt or Argon2 with salting.

🚀 Results

~14,000 transactions + 500 loans simulated.

Fraud detection achieves ~99% accuracy, ~91% recall, ~84% precision.

Tableau dashboards give management-level insights.