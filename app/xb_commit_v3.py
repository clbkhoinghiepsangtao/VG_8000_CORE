
import sqlite3
from pathlib import Path

def _vg_xb_v3_db():
    return Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

def vg_xb_v3_commit_batch(batch_id: int):
    conn=sqlite3.connect(str(_vg_xb_v3_db()))
    conn.row_factory=sqlite3.Row
    row=conn.execute(
        "SELECT batch_id,valid_rows,error_rows,status FROM xb_src_batch_v2 WHERE batch_id=?",
        (int(batch_id),)
    ).fetchone()
    if row is None:
        conn.close()
        raise ValueError("Batch không tồn tại")
    if int(row["error_rows"] or 0)>0:
        conn.close()
        raise ValueError("Batch còn lỗi, chưa được phép Commit")
    if str(row["status"]).upper()=="COMMITTED":
        out={"batch_id":row["batch_id"],"valid_rows":row["valid_rows"],"status":"COMMITTED","already_committed":True}
        conn.close()
        return out
    cur=conn.execute(
        "UPDATE xb_src_batch_v2 SET status='COMMITTED' WHERE batch_id=? AND status='PREVIEW'",
        (int(batch_id),)
    )
    conn.commit()
    if cur.rowcount!=1:
        conn.close()
        raise ValueError("Không cập nhật được trạng thái Batch")
    out={"batch_id":row["batch_id"],"valid_rows":row["valid_rows"],"status":"COMMITTED"}
    conn.close()
    return out

def vg_xb_v3_history():
    conn=sqlite3.connect(str(_vg_xb_v3_db()))
    conn.row_factory=sqlite3.Row
    rows=conn.execute(
        "SELECT batch_id,source_type,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status "
        "FROM xb_src_batch_v2 ORDER BY batch_id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
