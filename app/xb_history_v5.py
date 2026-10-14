
import sqlite3
from pathlib import Path

def _db():
    return Path(__file__).resolve().parent.parent/"data"/"miniapp.db"

def _exists(c,t):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None

def unified_history():
    c=sqlite3.connect(str(_db()))
    c.row_factory=sqlite3.Row
    rows=[]

    if _exists(c,"xb_src_batch_v2"):
        for r in c.execute(
            "SELECT batch_id,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status "
            "FROM xb_src_batch_v2 ORDER BY batch_id DESC"
        ).fetchall():
            d=dict(r)
            d["source_type"]="dms-xa"
            d["source_label"]="DMS – Xả"
            d["storage"]="xb_src_batch_v2"
            rows.append(d)

    if _exists(c,"xb_dms_mbw_batch"):
        for r in c.execute(
            "SELECT batch_id,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status "
            "FROM xb_dms_mbw_batch ORDER BY batch_id DESC"
        ).fetchall():
            d=dict(r)
            d["source_type"]="dms-mbw"
            d["source_label"]="DMS/MBW – Giao thật / Bán bù"
            d["storage"]="xb_dms_mbw_batch"
            rows.append(d)

    c.close()

    # only keep meaningful operational batches
    clean=[]
    for d in rows:
        # keep committed always; keep preview only if it has actual valid data or actual errors
        st=str(d.get("status") or "").upper()
        total=int(d.get("total_rows") or 0)
        valid=int(d.get("valid_rows") or 0)
        err=int(d.get("error_rows") or 0)
        if st=="COMMITTED" or total>0 or valid>0 or err>0:
            clean.append(d)

    clean.sort(key=lambda x:str(x.get("uploaded_at","")),reverse=True)
    return clean[:100]

def unified_commit(storage,batch_id):
    c=sqlite3.connect(str(_db()))
    c.row_factory=sqlite3.Row

    if storage=="xb_src_batch_v2":
        table="xb_src_batch_v2"
    elif storage=="xb_dms_mbw_batch":
        table="xb_dms_mbw_batch"
    else:
        c.close()
        raise ValueError("Nguồn Batch không hợp lệ")

    r=c.execute(
        f"SELECT batch_id,valid_rows,error_rows,status FROM {table} WHERE batch_id=?",
        (int(batch_id),)
    ).fetchone()
    if not r:
        c.close();raise ValueError("Batch không tồn tại")
    if int(r["error_rows"] or 0)>0:
        c.close();raise ValueError("Batch còn lỗi")

    c.execute(f"UPDATE {table} SET status='COMMITTED' WHERE batch_id=?",(int(batch_id),))
    c.commit();c.close()
    return {"batch_id":batch_id,"valid_rows":r["valid_rows"],"status":"COMMITTED","storage":storage}
