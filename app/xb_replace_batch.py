
import sqlite3, datetime
from pathlib import Path

def _db():
    return Path(__file__).resolve().parent.parent/"data"/"miniapp.db"

def _conn():
    c=sqlite3.connect(str(_db()))
    c.row_factory=sqlite3.Row
    return c

def _table_exists(c,t):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None

def _ensure_cols(c,table):
    cols=[r["name"] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if "replaces_batch_id" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN replaces_batch_id INTEGER")
    if "superseded_by_batch_id" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN superseded_by_batch_id INTEGER")
    if "superseded_at" not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN superseded_at TEXT")
    c.commit()

def _table_for_source(source_type):
    return {
        "dms-xa":"xb_src_batch_v2",
        "dms-mbw":"xb_dms_mbw_batch",
        "misa-ban-bu":"xb_misa_bu_batch",
    }.get(source_type)

def prepare_replacement(source_type, old_batch_id):
    table=_table_for_source(source_type)
    if not table:
        raise ValueError("Nguồn không hợp lệ")
    c=_conn()
    if not _table_exists(c,table):
        c.close(); raise ValueError("Không tìm thấy bảng Batch")
    _ensure_cols(c,table)
    row=c.execute(f"SELECT batch_id,status FROM {table} WHERE batch_id=?",(int(old_batch_id),)).fetchone()
    if not row:
        c.close(); raise ValueError("Batch cũ không tồn tại")
    if str(row["status"]).upper()!="COMMITTED":
        c.close(); raise ValueError("Chỉ được thay thế Batch đang COMMITTED")
    c.close()
    return {"source_type":source_type,"old_batch_id":int(old_batch_id),"status":"READY"}

def finalize_replacement(source_type, old_batch_id, new_batch_id):
    table=_table_for_source(source_type)
    if not table:
        raise ValueError("Nguồn không hợp lệ")
    c=_conn()
    _ensure_cols(c,table)
    old=c.execute(f"SELECT batch_id,status FROM {table} WHERE batch_id=?",(int(old_batch_id),)).fetchone()
    new=c.execute(f"SELECT batch_id,status FROM {table} WHERE batch_id=?",(int(new_batch_id),)).fetchone()
    if not old or not new:
        c.close(); raise ValueError("Không tìm thấy Batch cũ hoặc mới")
    if str(new["status"]).upper()!="COMMITTED":
        c.close(); raise ValueError("Batch mới chưa COMMITTED")
    if str(old["status"]).upper()!="COMMITTED":
        c.close(); raise ValueError("Batch cũ không còn ở trạng thái COMMITTED")
    now=datetime.datetime.now().isoformat(timespec="seconds")
    c.execute(
        f"UPDATE {table} SET status='SUPERSEDED', superseded_by_batch_id=?, superseded_at=? WHERE batch_id=?",
        (int(new_batch_id),now,int(old_batch_id))
    )
    c.execute(
        f"UPDATE {table} SET replaces_batch_id=? WHERE batch_id=?",
        (int(old_batch_id),int(new_batch_id))
    )
    c.commit(); c.close()
    return {
        "source_type":source_type,
        "old_batch_id":int(old_batch_id),
        "new_batch_id":int(new_batch_id),
        "old_status":"SUPERSEDED",
        "new_status":"COMMITTED"
    }

def replacement_history():
    c=_conn()
    out=[]
    specs=[
        ("dms-xa","DMS – Xả","xb_src_batch_v2"),
        ("dms-mbw","DMS/MBW – Giao thật / Bán bù","xb_dms_mbw_batch"),
        ("misa-ban-bu","MISA – Bán bù","xb_misa_bu_batch"),
    ]
    for st,label,t in specs:
        if not _table_exists(c,t): continue
        _ensure_cols(c,t)
        rows=c.execute(
            f"SELECT batch_id,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status,"
            f"replaces_batch_id,superseded_by_batch_id,superseded_at "
            f"FROM {t} ORDER BY batch_id DESC"
        ).fetchall()
        for r in rows:
            d=dict(r)
            d["source_type"]=st
            d["source_label"]=label
            out.append(d)
    c.close()
    out.sort(key=lambda x:str(x.get("uploaded_at","")),reverse=True)
    return out[:200]
