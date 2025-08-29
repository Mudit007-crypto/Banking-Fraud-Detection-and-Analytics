CREATE ROLE IF NOT EXISTS role_admin, role_employee, role_customer;
GRANT ALL PRIVILEGES ON bankfraud.* TO role_admin;
GRANT SELECT,INSERT,UPDATE ON bankfraud.Customer  TO role_employee;
GRANT SELECT,INSERT,UPDATE ON bankfraud.Account   TO role_employee;
GRANT SELECT,INSERT,UPDATE ON bankfraud.Loan      TO role_employee;
GRANT SELECT ON bankfraud.Transaction             TO role_employee;

GRANT SELECT ON bankfraud.Customer TO role_customer;
GRANT SELECT,INSERT ON bankfraud.Transaction TO role_customer;
GRANT SELECT,UPDATE ON bankfraud.Account TO role_customer;