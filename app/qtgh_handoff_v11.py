from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import sqlite3, json, datetime, hashlib
from decimal import Decimal, ROUND_HALF_UP

router=APIRouter(prefix="/api/qtgh-v11",tags=["QTGH BA V1.1"])

ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"data"/"miniapp.db"
HANDOFF_SOURCE_SYSTEM="DMS_MBW"
HANDOFF_BATCH_FLOOR=900000000

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

def master_rows(c,category):
    out=[]
    for r in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category=?",(category,)):
        try:p=json.loads(r["payload_json"] or "{}")
        except Exception:p={}
        p["_business_key"]=r["business_key"]
        out.append(p)
    return out

def staff_maps(c):
    by_ma={}
    for p in master_rows(c,"dm02-staff"):
        ma=str(p.get("MA_NV") or p.get("_business_key") or "").strip().upper()
        if ma:by_ma[ma]=p
    by_business={}
    for p in master_rows(c,"dm02a-staff-map"):
        for k in ("MA_NGHIEP_VU","MA_NV_NGHIEP_VU","MA_MAY","MA_NV_MAY"):
            v=str(p.get(k) or "").strip().upper()
            if v:by_business[v]=p
    return by_ma,by_business

def resolve_staff(c,code,maps=None):
    code=str(code or "").strip().upper()
    if not code:return ("","")
    by_ma,by_business=maps if maps is not None else staff_maps(c)
    if code in by_ma:
        p=by_ma[code]
        return (code,str(p.get("TEN_NV") or p.get("HO_TEN") or "").strip())
    m=by_business.get(code)
    if m:
        ma=str(m.get("MA_NV") or "").strip().upper()
        p=by_ma.get(ma,{})
        return (ma,str(p.get("TEN_NV") or p.get("HO_TEN") or "").strip())
    return ("","")

def resolve_customer(c,source_code,rows=None):
    code=str(source_code or "").strip().upper()
    if not code:return None
    for p in (rows if rows is not None else master_rows(c,"dm03-customer")):
        vals=[
            p.get("MA_KH_CHUAN"),p.get("MA_KH_MBW"),p.get("MA_KH_DMS"),
            p.get("_business_key")
        ]
        if any(str(v or "").strip().upper()==code for v in vals):
            return {
              "ma_kh_chuan":str(p.get("MA_KH_CHUAN") or p.get("_business_key") or "").strip(),
              "ma_kh_mbw":str(p.get("MA_KH_MBW") or "").strip(),
              "ma_kh_dms":str(p.get("MA_KH_DMS") or "").strip(),
              "ten_kh":str(p.get("TEN_KH") or p.get("TEN_KHACH_HANG") or "").strip(),
            }
    return None

def canonical_projection_money(prep_row):
    try:
        raw=json.loads(prep_row["raw_payload_json"] or "{}")
    except Exception:
        raw={}
    base_raw=raw.get("DON_GIA_CHUA_VAT")
    if base_raw not in (None,""):
        vat=(Decimal(str(base_raw or 0))*Decimal("1.08")).quantize(
            Decimal("0.01"),rounding=ROUND_HALF_UP
        )
    else:
        vat=Decimal(str(prep_row["unit_price_vat"] or 0)).quantize(
            Decimal("0.01"),rounding=ROUND_HALF_UP
        )
    qty=Decimal(str(prep_row["sale_qty_su"] or 0))
    due=Decimal(str(prep_row["amount_due_order"] or 0))
    ck=(qty*vat-due).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    if abs(ck)<Decimal("0.005"):
        ck=Decimal("0.00")
    return vat,ck

def ensure_schema():
    c=conn()
    tables={r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "qtgh_handoff" not in tables:
        c.execute("""CREATE TABLE qtgh_handoff(
          handoff_id TEXT PRIMARY KEY,
          print_lot_id TEXT NOT NULL UNIQUE,
          finalization_id TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL,
          order_count INTEGER NOT NULL DEFAULT 0,
          line_count INTEGER NOT NULL DEFAULT 0,
          performed_by TEXT,
          performed_at TEXT,
          error_text TEXT
        )""")
    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_handoff)")}
    if "source_batch_id" not in cols:
        c.execute("ALTER TABLE qtgh_handoff ADD COLUMN source_batch_id INTEGER")
    if "projection_checksum" not in cols:
        c.execute("ALTER TABLE qtgh_handoff ADD COLUMN projection_checksum TEXT")
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS ux_qtgh_handoff_source_batch
                 ON qtgh_handoff(source_batch_id)
                 WHERE source_batch_id IS NOT NULL""")
    c.commit();c.close()

ensure_schema()

def load_context(c,print_lot_id):
    lot=c.execute("SELECT * FROM qtgh_print_lot WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if not lot:
        raise HTTPException(404,"Không tìm thấy PRINT LOT")
    fin=c.execute("""SELECT * FROM qtgh_delivery_finalization
                     WHERE print_lot_id=?""",(print_lot_id,)).fetchone()
    if not fin or fin["finalize_status"]!="FINALIZED":
        raise HTTPException(400,"PRINT LOT chưa FINALIZED")
    if lot["status"] not in ("DA_CHOT_GIAO","DA_BAN_GIAO_QTGH"):
        raise HTTPException(400,f"Trạng thái PRINT LOT không hợp lệ để handoff: {lot['status']}")
    orders=[dict(r) for r in c.execute("""SELECT loai_don,ma_don_nguon
      FROM qtgh_print_lot_order WHERE print_lot_id=? ORDER BY ma_don_nguon""",(print_lot_id,))]
    if not orders:
        raise HTTPException(400,"PRINT LOT không có đơn")
    return lot,fin,orders

def preflight(c,print_lot_id):
    customers=master_rows(c,"dm03-customer")
    personnel=staff_maps(c)
    lot,fin,orders=load_context(c,print_lot_id)

    old=c.execute("SELECT * FROM qtgh_handoff WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if old:
        return {
          "eligible":old["status"]=="COMMITTED",
          "already_handed_off":old["status"]=="COMMITTED",
          "handoff":dict(old),
          "conflicts":[],
          "order_count":old["order_count"],
          "line_count":old["line_count"]
        }

    order_nos=[x["ma_don_nguon"] for x in orders]
    qs=",".join("?" for _ in order_nos)

    projection_conflicts=[dict(r) for r in c.execute(f"""
      SELECT ma_don_nguon,COUNT(*) n
      FROM qtgh_source_projection
      WHERE source_system=? AND ma_don_nguon IN ({qs})
      GROUP BY ma_don_nguon
    """,[HANDOFF_SOURCE_SYSTEM,*order_nos]).fetchall()]

    draft_conflicts=[dict(r) for r in c.execute(f"""
      SELECT source_system,ma_don_nguon,status,id
      FROM qtgh_draft_order
      WHERE ma_don_nguon IN ({qs})
    """,order_nos).fetchall()]

    prep=[dict(r) for r in c.execute(f"""
      SELECT p.*
      FROM qtgh_prep_line p
      WHERE p.prep_batch_id=?
        AND p.ma_don_nguon IN ({qs})
      ORDER BY p.ma_don_nguon,p.id
    """,[lot["prep_batch_id"],*order_nos]).fetchall()]

    conflicts=[]
    if projection_conflicts:
        conflicts.append({"type":"PROJECTION_ORDER_EXISTS","rows":projection_conflicts})
    if draft_conflicts:
        conflicts.append({"type":"DRAFT_ORDER_EXISTS","rows":draft_conflicts})

    if not prep:
        conflicts.append({"type":"NO_PREP_LINES"})

    nvgh,_=resolve_staff(c,fin["actual_delivery_staff_code"],personnel)
    driver,_=resolve_staff(c,fin["actual_driver_code"],personnel)
    if not nvgh:
        conflicts.append({"type":"NVGH_MAPPING","code":fin["actual_delivery_staff_code"]})
    if not driver:
        conflicts.append({"type":"DRIVER_MAPPING","code":fin["actual_driver_code"]})

    missing_customers=[]
    missing_nvtt=[]
    order_dates=[]
    for r in prep:
        order_dates.append(str(r["order_date"] or "")[:10])
        source_kh=r["ma_kh_dms"] or r["ma_kh_mbw"] or r["ma_kh_chuan"]
        if not resolve_customer(c,source_kh,customers):
            missing_customers.append(source_kh)
        ma_nvtt,_=resolve_staff(c,r["ma_nvtt"],personnel)
        if not ma_nvtt:
            missing_nvtt.append(r["ma_nvtt"])

    if missing_customers:
        conflicts.append({"type":"CUSTOMER_MAPPING","codes":sorted(set(missing_customers))})
    if missing_nvtt:
        conflicts.append({"type":"NVTT_MAPPING","codes":sorted(set(missing_nvtt))})

    actual_day=str(fin["actual_delivery_date"] or "")[:10]
    bad_days=sorted(set(d for d in order_dates if d and actual_day and d>actual_day))
    if bad_days:
        conflicts.append({"type":"ACTUAL_DATE_BEFORE_ORDER_DATE","order_dates":bad_days,"actual":actual_day})

    expected_total=0
    for order in order_nos:
        rows=[r for r in prep if r["ma_don_nguon"]==order]
        A=sum(int(r["amount_due_order"] or 0) for r in rows)
        B=max([int(r["order_reward_accum"] or 0) for r in rows] or [0])
        C=max([int(r["order_reward_display"] or 0) for r in rows] or [0])
        expected_total+=max(0,A-B-C)

    if int(lot["total_amount"] or 0)!=int(expected_total):
        conflicts.append({
          "type":"LOT_TOTAL_MISMATCH",
          "lot_total":int(lot["total_amount"] or 0),
          "calculated_total":int(expected_total)
        })

    return {
      "eligible":len(conflicts)==0,
      "already_handed_off":False,
      "print_lot_id":print_lot_id,
      "finalization_id":fin["finalization_id"],
      "actual_delivery_date":fin["actual_delivery_date"],
      "actual_nvgh":fin["actual_delivery_staff_code"],
      "actual_driver":fin["actual_driver_code"],
      "actual_vehicle":fin["actual_vehicle_code"],
      "actual_lot":fin["actual_lot_code"],
      "order_count":len(order_nos),
      "line_count":len(prep),
      "total_amount":expected_total,
      "conflicts":conflicts,
      "orders":order_nos
    }

@router.get("/print-lot/{print_lot_id}/handoff-preview")
def handoff_preview(print_lot_id:str):
    c=conn()
    try:return preflight(c,print_lot_id)
    finally:c.close()

@router.get("/print-lot/{print_lot_id}/handoff")
def handoff_state(print_lot_id:str):
    c=conn()
    r=c.execute("SELECT * FROM qtgh_handoff WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    c.close()
    return {"handoff":dict(r) if r else None}

@router.post("/print-lot/{print_lot_id}/handoff")
async def commit_handoff(print_lot_id:str,request:Request):
    body=await request.json()
    user=str(body.get("username") or "dev").strip()

    c=conn()
    try:
        pf=preflight(c,print_lot_id)
        if pf.get("already_handed_off"):
            return {"status":"COMMITTED","idempotent":True,"handoff":pf["handoff"]}
        if not pf["eligible"]:
            raise HTTPException(409,detail={"message":"Preflight handoff không đạt","conflicts":pf["conflicts"]})

        lot,fin,orders=load_context(c,print_lot_id)
        order_nos=[x["ma_don_nguon"] for x in orders]
        qs=",".join("?" for _ in order_nos)
        prep=[dict(r) for r in c.execute(f"""
          SELECT * FROM qtgh_prep_line
          WHERE prep_batch_id=? AND ma_don_nguon IN ({qs})
          ORDER BY ma_don_nguon,id
        """,[lot["prep_batch_id"],*order_nos]).fetchall()]

        max_batch=c.execute("""SELECT COALESCE(MAX(source_batch_id),?) m
                               FROM qtgh_source_projection
                               WHERE source_batch_id>=?""",
                            (HANDOFF_BATCH_FLOOR,HANDOFF_BATCH_FLOOR)).fetchone()["m"]
        source_batch_id=int(max_batch)+1
        handoff_id="HO-"+hashlib.sha256(
            f"{print_lot_id}|{fin['finalization_id']}|{source_batch_id}".encode()
        ).hexdigest()[:12].upper()

        actual_nvgh,_=resolve_staff(c,fin["actual_delivery_staff_code"])
        actual_driver,_=resolve_staff(c,fin["actual_driver_code"])

        projection_payload=[]
        row_seq=0
        seen_order=set()
        customers=master_rows(c,"dm03-customer")
        personnel=staff_maps(c)
        customer_cache={}
        staff_cache={}

        for r in prep:
            row_seq+=1
            order=r["ma_don_nguon"]
            first_line=order not in seen_order
            seen_order.add(order)

            source_kh=r["ma_kh_dms"] or r["ma_kh_mbw"] or r["ma_kh_chuan"]
            if source_kh not in customer_cache:
                customer_cache[source_kh]=resolve_customer(c,source_kh,customers)
            cust=customer_cache[source_kh]
            staff_key=r["ma_nvtt"]
            if staff_key not in staff_cache:
                staff_cache[staff_key]=resolve_staff(c,staff_key,personnel)
            ma_nvtt,ten_nvtt=staff_cache[staff_key]

            loai=str(r["loai_don"] or "").upper()
            ma_kh_dms=source_kh if loai=="L" else (cust["ma_kh_dms"] or "")
            ma_kh_mbw=source_kh if loai=="B" else (cust["ma_kh_mbw"] or "")

            tl=int(r["order_reward_accum"] or 0) if first_line else 0
            tb=int(r["order_reward_display"] or 0) if first_line else 0

            exact_vat,exact_ck=canonical_projection_money(r)
            payload={
              "source_system":HANDOFF_SOURCE_SYSTEM,
              "source_batch_id":source_batch_id,
              "source_row_no":row_seq,
              "loai_don":loai,
              "ma_don_nguon":order,
              "ngay_don":str(r["order_date"] or "")[:10],
              "ngay_giao":str(fin["actual_delivery_date"] or "")[:10],
              "ma_lo":str(fin["actual_lot_code"] or ""),
              "ma_nvgh":actual_nvgh,
              "ma_lai_xe":actual_driver,
              "ma_phuong_tien":str(fin["actual_vehicle_code"] or ""),
              "ma_nvtt":ma_nvtt,
              "ma_kh_chuan":cust["ma_kh_chuan"],
              "ma_kh_mbw":ma_kh_mbw,
              "ma_kh_dms":ma_kh_dms,
              "ma_sku":str(r["ma_sku"] or ""),
              "ten_sku":str(r["ten_sku"] or ""),
              "sl_hang_ban_dat":str(r["sale_qty_su"] or "0"),
              "sl_hang_km_dat":str(r["promo_qty_su"] or "0"),
              "don_gia_co_vat":float(exact_vat),
              "ck_km_dong_goc":float(exact_ck),
              "thuong_tich_luy_goc":tl,
              "thuong_trung_bay_goc":tb,
              "ten_kh":cust["ten_kh"],
              "ten_nvtt":ten_nvtt,
            }
            payload["source_hash"]=hashlib.sha256(canon(payload).encode()).hexdigest()
            projection_payload.append(payload)

        checksum=hashlib.sha256(canon(projection_payload).encode()).hexdigest()

        c.execute("BEGIN IMMEDIATE")

        c.execute("""INSERT INTO qtgh_handoff(
          handoff_id,print_lot_id,finalization_id,status,order_count,line_count,
          performed_by,performed_at,error_text,source_batch_id,projection_checksum
        ) VALUES(?,?,?,'IN_PROGRESS',?,?,?,NULL,NULL,?,?)""",
        (handoff_id,print_lot_id,fin["finalization_id"],len(order_nos),len(projection_payload),
         user,source_batch_id,checksum))

        sql="""INSERT INTO qtgh_source_projection(
          source_system,source_batch_id,source_row_no,loai_don,ma_don_nguon,
          ngay_don,ngay_giao,ma_lo,ma_nvgh,ma_lai_xe,ma_phuong_tien,ma_nvtt,
          ma_kh_chuan,ma_kh_mbw,ma_kh_dms,ma_sku,ten_sku,
          sl_hang_ban_dat,sl_hang_km_dat,don_gia_co_vat,ck_km_dong_goc,
          thuong_tich_luy_goc,thuong_trung_bay_goc,source_hash,ten_kh,ten_nvtt
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

        for p in projection_payload:
            c.execute(sql,(
              p["source_system"],p["source_batch_id"],p["source_row_no"],p["loai_don"],p["ma_don_nguon"],
              p["ngay_don"],p["ngay_giao"],p["ma_lo"],p["ma_nvgh"],p["ma_lai_xe"],p["ma_phuong_tien"],p["ma_nvtt"],
              p["ma_kh_chuan"],p["ma_kh_mbw"],p["ma_kh_dms"],p["ma_sku"],p["ten_sku"],
              p["sl_hang_ban_dat"],p["sl_hang_km_dat"],p["don_gia_co_vat"],p["ck_km_dong_goc"],
              p["thuong_tich_luy_goc"],p["thuong_trung_bay_goc"],p["source_hash"],p["ten_kh"],p["ten_nvtt"]
            ))

        c.execute("""UPDATE qtgh_handoff
                     SET status='COMMITTED',performed_at=?
                     WHERE handoff_id=?""",(now(),handoff_id))
        c.execute("""UPDATE qtgh_delivery_finalization
                     SET handoff_id=? WHERE finalization_id=?""",
                  (handoff_id,fin["finalization_id"]))
        c.execute("UPDATE qtgh_print_lot SET status='DA_BAN_GIAO_QTGH' WHERE print_lot_id=?",
                  (print_lot_id,))
        c.execute("""INSERT INTO qtgh_delivery_audit(
          event_type,object_type,object_id,username,occurred_at,after_json
        ) VALUES('QTGH_HANDOFF_COMMIT','PRINT_LOT',?,?,?,?)""",
        (print_lot_id,user,now(),canon({
          "handoff_id":handoff_id,"source_batch_id":source_batch_id,
          "order_count":len(order_nos),"line_count":len(projection_payload),
          "projection_checksum":checksum
        })))
        c.commit()

        return {
          "status":"COMMITTED","idempotent":False,
          "handoff_id":handoff_id,"source_batch_id":source_batch_id,
          "order_count":len(order_nos),"line_count":len(projection_payload),
          "projection_checksum":checksum,
          "ui04_filter":{
            "ngay_giao":str(fin["actual_delivery_date"] or "")[:10],
            "ma_nvgh":actual_nvgh,
            "ma_lo":str(fin["actual_lot_code"] or "")
          }
        }

    except HTTPException:
        c.rollback()
        raise
    except Exception as e:
        c.rollback()
        raise HTTPException(400,f"Handoff rollback: {e}")
    finally:
        c.close()
