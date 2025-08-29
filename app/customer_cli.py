from app.db import get_conn
from app.auth import login

def ensure_customer(user):
    if not user or user["role"] != "CUSTOMER":
        raise PermissionError("Customer only.")

def deposit(account_id, amount):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Account SET balance = balance + %s WHERE account_id=%s", (amount, account_id))
        cur.execute("""INSERT INTO Transaction (account_id, txn_type, amount, channel, location)
                       VALUES (%s,'DEPOSIT',%s,'BRANCH','Local')""", (account_id, amount))

def withdraw(account_id, amount):
    with get_conn() as conn:
        cur = conn.cursor()
        # naive check
        cur.execute("SELECT balance FROM Account WHERE account_id=%s FOR UPDATE", (account_id,))
        bal = cur.fetchone()[0]
        if bal < amount:
            raise ValueError("Insufficient funds")
        cur.execute("UPDATE Account SET balance = balance - %s WHERE account_id=%s", (amount, account_id))
        cur.execute("""INSERT INTO Transaction (account_id, txn_type, amount, channel, location)
                       VALUES (%s,'WITHDRAW',%s,'ATM','Local')""", (account_id, amount))

def transfer(src_account, dst_account, amount):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT balance FROM Account WHERE account_id=%s FOR UPDATE", (src_account,))
        bal = cur.fetchone()[0]
        if bal < amount:
            raise ValueError("Insufficient funds")
        cur.execute("UPDATE Account SET balance = balance - %s WHERE account_id=%s", (amount, src_account))
        cur.execute("UPDATE Account SET balance = balance + %s WHERE account_id=%s", (amount, dst_account))
        cur.execute("""INSERT INTO Transaction (account_id, txn_type, amount, channel, location, counterparty_account)
                       VALUES (%s,'TRANSFER_OUT',%s,'ONLINE','Local',%s)""", (src_account, amount, dst_account))
        cur.execute("""INSERT INTO Transaction (account_id, txn_type, amount, channel, location, counterparty_account)
                       VALUES (%s,'TRANSFER_IN',%s,'ONLINE','Local',%s)""", (dst_account, amount, src_account))

def run():
    u = login(input("Username: "), input("Password: "))
    ensure_customer(u)
    print("Customer menu: 1) Deposit 2) Withdraw 3) Transfer 0) Exit")
    while True:
        c = input("> ")
        if c == "1":
            aid = int(input("Account ID: "))
            amt = float(input("Amount: "))
            deposit(aid, amt)
            print("Deposited.")
        elif c == "2":
            aid = int(input("Account ID: "))
            amt = float(input("Amount: "))
            withdraw(aid, amt)
            print("Withdrawn.")
        elif c == "3":
            src = int(input("From Account: "))
            dst = int(input("To Account: "))
            amt = float(input("Amount: "))
            transfer(src, dst, amt)
            print("Transferred.")
        elif c == "0":
            break

if __name__ == "__main__":
    run()
