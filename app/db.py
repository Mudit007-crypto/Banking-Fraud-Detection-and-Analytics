import mysql.connector as mysql
from dotenv import load_dotenv
import os

load_dotenv()

def get_conn():
    return mysql.connect(
        host=os.getenv("DB_HOST","127.0.0.1"),
        port=int(os.getenv("DB_PORT","3307")),
        user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASS","Scorpio04."),
        database=os.getenv("DB_NAME","bankfraud"),
        autocommit=True
    )
