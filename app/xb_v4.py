
import sqlite3
from pathlib import Path

def _db():
    return Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

def _table_exists(conn, name):
    r=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone()
    return r is not None

def vg_xb_v4_history():
    conn=sqlite3.connect(str(_db()))
    conn.row_factory=sqlite3.Row
    out=[]

    if _table_exists(conn,"xb_src_batch_v2"):
        rows=conn.execute(
            "SELECT batch_id,source_type,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status "
            "FROM xb_src_batch_v2 ORDER BY batch_id DESC"
        ).fetchall()
        for r in rows:
            d=dict(r); d["storage"]="xb_src_batch_v2"; out.append(d)

    if _table_exists(conn,"src_batch"):
        rows=conn.execute(
            "SELECT batch_id,source_type,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status "
            "FROM src_batch ORDER BY batch_id DESC"
        ).fetchall()
        for r in rows:
            d=dict(r); d["storage"]="src_batch"; out.append(d)

    conn.close()

    # Deduplicate same file/source/hash-era rows by storage priority:
    # prefer xb_src_batch_v2 over old src_batch.
    seen=set()
    final=[]
    for d in sorted(out,key=lambda x:(0 if x["storage"]=="xb_src_batch_v2" else 1,-int(x["batch_id"]))):
        key=(str(d.get("source_type")),str(d.get("file_name")),str(d.get("uploaded_at")))
        if key in seen: continue
        seen.add(key); final.append(d)

    final.sort(key=lambda x:str(x.get("uploaded_at","")),reverse=True)
    return final[:100]

def vg_xb_v4_commit(storage, batch_id):
    if storage not in ("xb_src_batch_v2","src_batch"):
        raise ValueError("Storage không hợp lệ")
    conn=sqlite3.connect(str(_db()))
    conn.row_factory=sqlite3.Row
    if not _table_exists(conn,storage):
        conn.close(); raise ValueError("Không tìm thấy bảng Batch")

    row=conn.execute(
        f"SELECT batch_id,valid_rows,error_rows,status FROM {storage} WHERE batch_id=?",
        (int(batch_id),)
    ).fetchone()
    if row is None:
        conn.close(); raise ValueError("Batch không tồn tại")
    if int(row["error_rows"] or 0)>0:
        conn.close(); raise ValueError("Batch còn lỗi, chưa được phép Commit")

    if str(row["status"]).upper()=="COMMITTED":
        result={"batch_id":row["batch_id"],"valid_rows":row["valid_rows"],"status":"COMMITTED","storage":storage,"already_committed":True}
        conn.close(); return result

    cur=conn.execute(
        f"UPDATE {storage} SET status='COMMITTED' WHERE batch_id=?",
        (int(batch_id),)
    )
    conn.commit()
    if cur.rowcount != 1:
        conn.close(); raise ValueError("Không cập nhật được Batch")

    result={"batch_id":row["batch_id"],"valid_rows":row["valid_rows"],"status":"COMMITTED","storage":storage}
    conn.close()
    return result

def vg_xb_v4_diag():
    conn=sqlite3.connect(str(_db()))
    result={"db":str(_db()),"tables":{}}
    for t in ("xb_src_batch_v2","src_batch"):
        if _table_exists(conn,t):
            count=conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            result["tables"][t]=count
        else:
            result["tables"][t]="MISSING"
    conn.close()
    return result
