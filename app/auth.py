from app.db import get_conn
import hashlib

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def create_user(username, password, role, ref_id):
    q = "INSERT INTO UserAuth (username,password_hash,role,ref_id) VALUES (%s,%s,%s,%s)"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(q, (username, hash_pw(password), role, ref_id))

def login(username, password):
    q = "SELECT user_id, role, ref_id, password_hash FROM UserAuth WHERE username=%s"
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(q, (username,))
        row = cur.fetchone()
    if not row or row["password_hash"] != hash_pw(password):
        return None
    return {"user_id": row["user_id"], "role": row["role"], "ref_id": row["ref_id"]}
