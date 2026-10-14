
import os, json, tempfile, shutil, sqlite3, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT))

from app.db import init_db, connect
from app.security import verify_password, hash_password, has_permission, audit

def ok(name, cond, detail=""):
    status="PASS" if cond else "FAIL"
    print(f"{status:4} | {name}" + (f" | {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)

def main():
    init_db()
    # auth/RBAC
    with connect() as con:
        admin=con.execute("SELECT * FROM app_user WHERE username='admin'").fetchone()
        kt=con.execute("SELECT * FROM app_user WHERE username='ketoan01'").fetchone()
    ok("Admin user exists", admin is not None)
    ok("SUPER_ADMIN role", admin["role"]=="SUPER_ADMIN")
    ok("RBAC KE_TOAN upload", has_permission("KE_TOAN","UPLOAD_SOURCE"))
    ok("RBAC VIEWER no upload", not has_permission("VIEWER","UPLOAD_SOURCE"))

    # audit
    audit("admin","SMOKE_TEST","SYSTEM","PILOT","pilot readiness")
    with connect() as con:
        a=con.execute("SELECT * FROM audit_log WHERE action='SMOKE_TEST' ORDER BY id DESC LIMIT 1").fetchone()
    ok("Audit log insert", a is not None)

    # adjustment
    with connect() as con:
        con.execute("""INSERT OR REPLACE INTO adjustment_doc
          (adjustment_id,original_doc_type,original_doc_id,direction,amount,quantity,reason,status,created_by)
          VALUES('ADJ-SMOKE-001','GH','GH-DEMO-001','INCREASE',1000,1,'Smoke test','DRAFT','admin')""")
        r=con.execute("SELECT * FROM adjustment_doc WHERE adjustment_id='ADJ-SMOKE-001'").fetchone()
    ok("Adjustment references original", r is not None and r["original_doc_id"]=="GH-DEMO-001")

    # backup/restore simulation
    db_path = ROOT/"data"/"vinh_giang.db"
    backup_dir = ROOT/"backup"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir/"smoke_backup.db"
    shutil.copy2(db_path, backup)
    ok("Backup file created", backup.exists() and backup.stat().st_size>0)

    # sanity query copied db
    con2=sqlite3.connect(backup)
    c=con2.execute("SELECT count(*) FROM app_user").fetchone()[0]
    con2.close()
    ok("Backup readable", c>=1, f"users={c}")

    print("\nPILOT_READINESS_SMOKE_TEST: PASS")
if __name__=="__main__":
    main()
