
import sqlite3
from pathlib import Path

def _db_v6():
    return Path(__file__).resolve().parent.parent/"data"/"miniapp.db"

def _exists_v6(c,t):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None

def unified_history_v6():
    c=sqlite3.connect(str(_db_v6()))
    c.row_factory=sqlite3.Row
    out=[]

    specs=[
      ("xb_src_batch_v2","dms-xa","DMS – Xả"),
      ("xb_dms_mbw_batch","dms-mbw","DMS/MBW – Giao thật / Bán bù"),
      ("xb_misa_bu_batch","misa-ban-bu","MISA – Bán bù"),
    ]

    for table,stype,label in specs:
        if not _exists_v6(c,table):
            continue
        rows=c.execute(
            f"SELECT batch_id,file_name,uploaded_by,uploaded_at,total_rows,valid_rows,error_rows,status FROM {table} ORDER BY batch_id DESC"
        ).fetchall()
        for r in rows:
            d=dict(r)
            d["storage"]=table
            d["source_type"]=stype
            d["source_label"]=label
            out.append(d)

    c.close()
    out.sort(key=lambda x:str(x.get("uploaded_at","")),reverse=True)
    return out[:100]
