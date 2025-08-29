def run_admin():
    import app.admin_cli as m
    m.run()

def run_employee():
    import app.employee_cli as m
    m.run()

def run_customer():
    import app.customer_cli as m
    m.run()

def export_analytics():
    from analytics.export_csvs import main as export_main
    export_main()

if __name__ == "__main__":
    print("1) Admin  2) Employee  3) Customer  4) Export Analytics CSVs  0) Exit")
    while True:
        ch = input("> ").strip()
        if ch == "1": run_admin()
        elif ch == "2": run_employee()
        elif ch == "3": run_customer()
        elif ch == "4": export_analytics()
        elif ch == "0": break
        else: print("choose 1/2/3/4/0")
