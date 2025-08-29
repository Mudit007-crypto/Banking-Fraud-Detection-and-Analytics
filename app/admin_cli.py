from app.db import get_conn
from app.auth import login

def ensure_admin(user):
    if not user or user["role"] != "ADMIN":
        raise PermissionError("Admin only.")

def create_employee(name, role, email):
    q = "INSERT INTO Employee (name,role,email) VALUES (%s,%s,%s)"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(q, (name, role, email))
        return cur.lastrowid

def list_customers():
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Customer")
        return cur.fetchall()

def run():
    u = login(input("Username: "), input("Password: "))
    ensure_admin(u)
    print("Admin menu: 1) List customers 2) Create employee 0) Exit")
    while True:
        c = input("> ")
        if c == "1":
            for row in list_customers():
                print(row)
        elif c == "2":
            name = input("Emp name: ")
            role = input("Role (ADMIN/EMPLOYEE): ")
            email = input("Email: ")
            emp_id = create_employee(name, role, email)
            print("Created employee_id:", emp_id)
        elif c == "0":
            break

if __name__ == "__main__":
    run()
