import os, sqlite3, bcrypt
from datetime import datetime, timezone

DB_PATH = os.getenv("EPIFLOW_DB_PATH", "data/epiflow.db")

ROLE_PERMISSIONS = {
    "admin": {"upload","view_raw","schema","clean","analyse","internal_map","briefing_map","dashboard","ai","export_data","export_brief","manage_users","audit"},
    "analyst": {"upload","view_raw","schema","clean","analyse","internal_map","briefing_map","dashboard","ai","export_data","export_brief"},
    "viewer": {"briefing_map","dashboard","export_brief"},
}

def _conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with _conn() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            username TEXT NOT NULL,
            role TEXT,
            action TEXT NOT NULL,
            dataset TEXT,
            detail TEXT
        )""")

def create_user(username, password, role="viewer"):
    if role not in ROLE_PERMISSIONS:
        raise ValueError("Invalid role")
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with _conn() as con:
        con.execute(
            "INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
            (username, pw, role, datetime.now(timezone.utc).isoformat())
        )

def authenticate(username, password):
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
    if not row:
        return None
    stored = row["password_hash"]
    if isinstance(stored, str):
        stored = stored.encode()
    if bcrypt.checkpw(password.encode(), stored):
        return {"username": row["username"], "role": row["role"]}
    return None

def can(user, permission):
    return bool(user and permission in ROLE_PERMISSIONS.get(user.get("role"), set()))

def log_event(user, action, dataset=None, detail=None):
    if not user:
        return
    with _conn() as con:
        con.execute(
            "INSERT INTO audit_log(ts,username,role,action,dataset,detail) VALUES(?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), user["username"], user["role"], action, dataset, detail)
        )

def list_users():
    with _conn() as con:
        return [dict(r) for r in con.execute(
            "SELECT id,username,role,active,created_at FROM users ORDER BY username"
        )]

def list_audit(limit=500):
    with _conn() as con:
        return [dict(r) for r in con.execute(
            "SELECT ts,username,role,action,dataset,detail FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)
        )]
