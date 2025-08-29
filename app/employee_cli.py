from app.db import get_conn
from app.auth import login

def ensure_employee(user):
    if not user or user["role"] not in ("ADMIN","EMPLOYEE"):
        raise PermissionError("Employee/Admin only.")

def approve_loan(loan_id, approve=True):
    new_status = "APPROVED" if approve else "REJECTED"
    q = "UPDATE Loan SET status=%s WHERE loan_id=%s"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(q, (new_status, loan_id))
        return cur.rowcount

def view_customer_history(customer_id):
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT a.account_id, a.account_type, a.balance, t.txn_id, t.txn_time, t.txn_type, t.amount
            FROM Account a
            LEFT JOIN Transaction t ON t.account_id = a.account_id
            WHERE a.customer_id = %s
            ORDER BY t.txn_time DESC
        """, (customer_id,))
        return cur.fetchall()

def run():
    u = login(input("Username: "), input("Password: "))
    ensure_employee(u)
    print("Employee menu: 1) Approve loan 2) View customer history 0) Exit")
    while True:
        c = input("> ")
        if c == "1":
            lid = int(input("Loan ID: "))
            ok = input("Approve? (y/n): ").lower() == "y"
            print("Updated rows:", approve_loan(lid, ok))
        elif c == "2":
            cid = int(input("Customer ID: "))
            rows = view_customer_history(cid)
            for r in rows:
                print(r)
        elif c == "0":
            break

if __name__ == "__main__":
    run()
