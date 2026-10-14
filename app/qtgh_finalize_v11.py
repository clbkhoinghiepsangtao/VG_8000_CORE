from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import sqlite3, json, datetime, hashlib

router=APIRouter(prefix="/api/qtgh-v11",tags=["QTGH BA V1.1"])
ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"data"/"miniapp.db"

def conn():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=5000")
    return c

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)

def valid_date(v):
    try:
        datetime.date.fromisoformat(str(v or "")[:10]); return True
    except Exception:
        return False

def ensure_schema():
    c=conn()
    tables={r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "qtgh_delivery_finalization" not in tables:
        c.execute("""CREATE TABLE qtgh_delivery_finalization(
          finalization_id TEXT PRIMARY KEY,
          print_lot_id TEXT NOT NULL UNIQUE,
          actual_delivery_date TEXT NOT NULL,
          actual_delivery_staff_code TEXT,
          actual_driver_code TEXT,
          actual_vehicle_code TEXT,
          actual_lot_code TEXT NOT NULL,
          reason TEXT,
          warehouse_source_note TEXT,
          finalized_by TEXT NOT NULL,
          finalized_at TEXT NOT NULL,
          finalize_status TEXT NOT NULL DEFAULT 'FINALIZED',
          version INTEGER NOT NULL DEFAULT 1,
          handoff_id TEXT
        )""")
    c.commit(); c.close()

ensure_schema()

@router.get("/print-lot/{print_lot_id}/actual")
def get_actual(print_lot_id:str):
    c=conn()
    lot=c.execute("SELECT * FROM qtgh_print_lot WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if not lot:
        c.close(); raise HTTPException(404,"Không tìm thấy PRINT LOT")
    pb=c.execute("""SELECT print_batch_id,status FROM qtgh_print_batch
                    WHERE print_lot_id=? ORDER BY print_version DESC LIMIT 1""",(print_lot_id,)).fetchone()
    fin=c.execute("SELECT * FROM qtgh_delivery_finalization WHERE print_lot_id=?",(print_lot_id,)).fetchone()

    planned={
      "delivery_date":lot["planned_delivery_date"],
      "delivery_staff_code":lot["planned_delivery_staff_code"] or "",
      "driver_code":lot["planned_driver_code"] or "",
      "vehicle_code":lot["planned_vehicle_code"] or "",
      "lot_code":lot["planned_lot_code"] or "",
    }
    actual=dict(fin) if fin else {
      "actual_delivery_date":planned["delivery_date"],
      "actual_delivery_staff_code":planned["delivery_staff_code"],
      "actual_driver_code":planned["driver_code"],
      "actual_vehicle_code":planned["vehicle_code"],
      "actual_lot_code":planned["lot_code"],
      "reason":"",
      "warehouse_source_note":"",
      "finalize_status":"DRAFT"
    }
    out={
      "print_lot_id":print_lot_id,
      "lot_status":lot["status"],
      "print_locked":bool(pb),
      "planned":planned,
      "actual":actual,
      "locked":bool(fin and fin["finalize_status"]=="FINALIZED")
    }
    c.close()
    return out

@router.post("/print-lot/{print_lot_id}/finalize")
async def finalize(print_lot_id:str,request:Request):
    body=await request.json()
    user=str(body.get("username") or "dev").strip()
    ad=str(body.get("actual_delivery_date") or "").strip()
    nvgh=str(body.get("actual_delivery_staff_code") or "").strip().upper()
    drv=str(body.get("actual_driver_code") or "").strip().upper()
    veh=str(body.get("actual_vehicle_code") or "").strip()
    lotcode=str(body.get("actual_lot_code") or "").strip()
    reason=str(body.get("reason") or "").strip()
    source=str(body.get("warehouse_source_note") or "").strip()

    if not valid_date(ad): raise HTTPException(400,"Ngày giao thực tế không hợp lệ")
    if not nvgh: raise HTTPException(400,"Thiếu NVGH thực tế")
    if not drv: raise HTTPException(400,"Thiếu Lái xe thực tế")
    if not veh: raise HTTPException(400,"Thiếu Phương tiện thực tế")
    if not lotcode: raise HTTPException(400,"Thiếu Mã lô thực tế")

    c=conn()
    lot=c.execute("SELECT * FROM qtgh_print_lot WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if not lot:
        c.close(); raise HTTPException(404,"Không tìm thấy PRINT LOT")
    pb=c.execute("""SELECT print_batch_id FROM qtgh_print_batch
                    WHERE print_lot_id=? ORDER BY print_version DESC LIMIT 1""",(print_lot_id,)).fetchone()
    if not pb:
        c.close(); raise HTTPException(400,"PRINT LOT chưa khóa bản in/QR")

    old=c.execute("SELECT * FROM qtgh_delivery_finalization WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if old:
        out=dict(old); c.close()
        return {"status":"ALREADY_FINALIZED","finalization":out,"idempotent":True}

    planned={
      "delivery_date":str(lot["planned_delivery_date"] or ""),
      "delivery_staff_code":str(lot["planned_delivery_staff_code"] or "").upper(),
      "driver_code":str(lot["planned_driver_code"] or "").upper(),
      "vehicle_code":str(lot["planned_vehicle_code"] or ""),
      "lot_code":str(lot["planned_lot_code"] or ""),
    }
    actual={
      "delivery_date":ad,
      "delivery_staff_code":nvgh,
      "driver_code":drv,
      "vehicle_code":veh,
      "lot_code":lotcode,
    }
    changed={k:{"planned":planned[k],"actual":actual[k]} for k in planned if str(planned[k])!=str(actual[k])}
    if changed and not reason:
        c.close(); raise HTTPException(400,"Có thay đổi: bắt buộc nhập Lý do thay đổi")
    if changed and not source:
        c.close(); raise HTTPException(400,"Có thay đổi: bắt buộc nhập Nguồn xác nhận Thủ kho")

    fid="FIN-"+hashlib.sha256(f"{print_lot_id}|{now()}|{user}".encode()).hexdigest()[:12].upper()
    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute("""INSERT INTO qtgh_delivery_finalization(
          finalization_id,print_lot_id,actual_delivery_date,
          actual_delivery_staff_code,actual_driver_code,actual_vehicle_code,
          actual_lot_code,reason,warehouse_source_note,finalized_by,
          finalized_at,finalize_status,version,handoff_id
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,'FINALIZED',1,NULL)""",
        (fid,print_lot_id,ad,nvgh,drv,veh,lotcode,reason or None,source or None,user,now()))
        c.execute("UPDATE qtgh_print_lot SET status='DA_CHOT_GIAO' WHERE print_lot_id=?",(print_lot_id,))
        c.execute("""INSERT INTO qtgh_delivery_audit(
          event_type,object_type,object_id,username,occurred_at,
          before_json,after_json,reason,source_note
        ) VALUES('DELIVERY_FINALIZE','PRINT_LOT',?,?,?,?,?,?,?)""",
        (print_lot_id,user,now(),canon(planned),canon({"actual":actual,"changed":changed}),
         reason or None,source or None))
        c.commit()
    except Exception:
        c.rollback(); c.close(); raise

    fin=dict(c.execute("SELECT * FROM qtgh_delivery_finalization WHERE finalization_id=?",(fid,)).fetchone())
    c.close()
    return {"status":"FINALIZED","finalization":fin,"changed":changed,"idempotent":False}
