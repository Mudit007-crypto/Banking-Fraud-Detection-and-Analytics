USE bankfraud;

INSERT INTO Customer (name,email,phone,region) VALUES
('Aarav Mehta','aarav@example.com','9999990001','North'),
('Neha Sharma','neha@example.com','9999990002','West'),
('Ravi Kumar','ravi@example.com','9999990003','South'),
('Priya Nair','priya@example.com','9999990004','East'),
('Anil Kapoor','anil@example.com','9999990005','North'),
('Sunita Reddy','sunita@example.com','9999990006','South'),
('Karan Patel','karan@example.com','9999990007','West'),
('Meera Das','meera@example.com','9999990008','East');


INSERT INTO Employee (name,role,email) VALUES
('Admin One','ADMIN','admin1@bank.local'),
('Bhavya Singh','EMPLOYEE','bhavya@bank.local');

INSERT INTO Account (customer_id,account_type,balance) VALUES
(1,'SAVINGS',50000.00),
(2,'CURRENT',120000.00),
(3,'SAVINGS',8000.00);

INSERT INTO Loan (customer_id,amount,interest_rate,tenure_months,status) VALUES
(2,250000.00,11.5,36,'APPLIED');

INSERT INTO Transaction (account_id,txn_type,amount,channel,location) VALUES
(1,'DEPOSIT',10000,'BRANCH','Delhi'),
(1,'WITHDRAW',2000,'ATM','Delhi'),
(2,'TRANSFER_OUT',40000,'ONLINE','Mumbai'),
(3,'DEPOSIT',6000,'MOBILE','Chennai'),
(2,'WITHDRAW',150000,'ONLINE','Mumbai');