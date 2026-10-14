from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import sqlite3, json, datetime, uuid
from decimal import Decimal, ROUND_HALF_UP

router=APIRouter(prefix="/api/qtgh-v11",tags=["QTGH BA V1.1"])
ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"data"/"miniapp.db"

def conn():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");c.execute("PRAGMA busy_timeout=5000");return c
def now():return datetime.datetime.now().isoformat(timespec="seconds")
def D(v):
    try:return Decimal(str(v if v not in (None,"") else 0))
    except Exception:return Decimal("0")
def money(v):return int(D(v).quantize(Decimal("1"),rounding=ROUND_HALF_UP))
def parse_date(v):
    if v in (None,""):return None
    if isinstance(v,datetime.datetime):return v.date()
    if isinstance(v,datetime.date):return v
    s=str(v).strip()
    for f in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y"):
        try:return datetime.datetime.strptime(s[:10],f).date()
        except Exception:pass
    try:return datetime.date.fromisoformat(s[:10])
    except Exception:return None

def ensure_extra_columns():
    c=conn()
    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_prep_line)").fetchall()}
    if "order_reward_other" not in cols:
        c.execute("ALTER TABLE qtgh_prep_line ADD COLUMN order_reward_other INTEGER NOT NULL DEFAULT 0")
    if "don_app" not in cols:
        c.execute("ALTER TABLE qtgh_prep_line ADD COLUMN don_app TEXT")
    c.commit();c.close()
ensure_extra_columns()

def master_rows(category):
    c=conn();rows=[]
    try:
        for r in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category=?",(category,)):
            try:p=json.loads(r["payload_json"] or "{}")
            except Exception:p={}
            p["_business_key"]=r["business_key"];rows.append(p)
    finally:c.close()
    return rows

def product_map():
    out={}
    for p in master_rows("dm01-product"):
        k=str(p.get("MA_SKU") or p.get("_business_key") or "").strip().upper()
        if k:out[k]=p
    return out

def staff_maps():
    by_ma={}
    for p in master_rows("dm02-staff"):
        ma=str(p.get("MA_NV") or p.get("_business_key") or "").strip().upper()
        if ma:by_ma[ma]=p
    by_nv={}
    for p in master_rows("dm02a-staff-map"):
        for k in ("MA_NGHIEP_VU","MA_NV_NGHIEP_VU","MA_MAY","MA_NV_MAY"):
            v=p.get(k)
            if v not in (None,""):by_nv[str(v).strip().upper()]=p
    return by_ma,by_nv

def resolve_staff(code):
    code=str(code or "").strip().upper()
    if not code:return {}
    by_ma,by_nv=staff_maps()
    if code in by_ma:return by_ma[code]
    x=by_nv.get(code) or {};ma=str(x.get("MA_NV") or "").strip().upper()
    return by_ma.get(ma,{}) if ma else {}

def resolve_customer(code):
    code=str(code or "").strip().upper()
    if not code:return {}
    for p in master_rows("dm03-customer"):
        vals=[p.get("MA_KH_CHUAN"),p.get("MA_KH_MBW"),p.get("MA_KH_DMS"),p.get("_business_key")]
        if any(str(v or "").strip().upper()==code for v in vals):return p
    return {}

def get_bank(bank_id):
    c=conn();r=c.execute("SELECT id,ma_tknh,bank_name,account_no,account_name,status FROM qtgh_receiving_bank_account WHERE id=? AND status='ACTIVE'",(bank_id,)).fetchone();c.close()
    return dict(r) if r else {}

def calc_price_vat(row,product):
    if row.get("DON_GIA_CO_VAT") not in (None,""):return money(row.get("DON_GIA_CO_VAT"))
    pre=D(row.get("DON_GIA_CHUA_VAT"));vat=D(row.get("VAT_RATE"))
    if vat==0:vat=D(product.get("VAT_RATE") or 0.08)
    if vat>1:vat=vat/Decimal("100")
    return money(pre*(Decimal("1")+vat))

def build_line_payload(d,product):
    ratio=D(product.get("SO_SU_THUNG") or 1)
    sale_qty=D(d.get("SL_SU"))+D(d.get("SL_THUNG"))*ratio
    promo_qty=D(d.get("SL_KM_SU"))+D(d.get("SL_KM_THUNG"))*ratio
    price_vat=calc_price_vat(d,product)
    amount_due=money(d.get("DOANH_SO_PHAI_THU"))
    gross=money((sale_qty+promo_qty)*D(price_vat));promo_value=money(promo_qty*D(price_vat))
    line_discount=max(0,gross-promo_value-amount_due)
    return sale_qty,promo_qty,price_vat,line_discount,amount_due

def promo_price_index(rows):
    out={}
    for row in rows:
        sku=str(row.get("MA_SKU") or "").strip().upper()
        if sku:
            out.setdefault(sku,[]).append(row)
    return out


def promo_reference_price(index,sku,order_date,product):
    day=parse_date(order_date)
    if day is None:
        return None
    valid=[]
    for row in index.get(sku,[]):
        if str(row.get("TRANG_THAI") or "").strip().upper()!="DANG_HIEU_LUC":
            continue
        start=parse_date(row.get("TU_NGAY"))
        end=parse_date(row.get("DEN_NGAY"))
        if start is None or start>day or (end is not None and end<day):
            continue
        if row.get("DEN_NGAY") not in (None,"") and end is None:
            continue
        price=calc_price_vat(row,product)
        if price>0:
            valid.append((start,price))
    if not valid:
        return None
    latest=max(start for start,price in valid)
    prices={price for start,price in valid if start==latest}
    return prices.pop() if len(prices)==1 else None


@router.post("/prep/commit-v2")
async def prep_commit_v2(request:Request):
    return commit_prepared(await request.json())

def commit_prepared(body):
    filename=str(body.get("filename") or "upload.xlsx");checksum=str(body.get("checksum") or "").strip()
    rows=body.get("rows") or [];uploaded_by=str(body.get("uploaded_by") or "pilot")
    if not checksum or not rows:raise HTTPException(400,"Thiếu checksum hoặc dữ liệu preview")
    try:expected_total_rows=int(body.get("expected_total_rows"))
    except (TypeError,ValueError):raise HTTPException(400,"Thiếu tổng số dòng Preview để đối chiếu")
    if expected_total_rows<=0 or len(rows)!=expected_total_rows:
        raise HTTPException(400,f"Số dòng Commit ({len(rows)}) khác Preview ({expected_total_rows}); dừng nạp để tránh thiếu dữ liệu")
    if any(not bool(r.get("valid")) for r in rows):raise HTTPException(400,"Còn dòng lỗi; không được commit")

    c=conn();dup=c.execute("SELECT prep_batch_id FROM qtgh_prep_batch WHERE source_checksum=?",(checksum,)).fetchone()
    if dup:c.close();raise HTTPException(409,f"FR04: File đã commit ở PREP BATCH {dup['prep_batch_id']}")
    products=product_map();prep_batch_id="PREP-"+uuid.uuid4().hex[:12].upper()

    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute("""INSERT INTO qtgh_prep_batch(prep_batch_id,source_file_name,source_checksum,uploaded_by,uploaded_at,status,total_lines)
                     VALUES(?,?,?,?,?,'DA_NAP_HOP_LE',?)""",(prep_batch_id,filename,checksum,uploaded_by,now(),len(rows)))
        order_due={};order_meta={}
        for r in rows:
            d=dict(r.get("data") or {});rn=int(r.get("row_no") or 0)
            order=str(d.get("SO_HOA_DON") or "").strip();sku=str(d.get("MA_SKU") or "").strip().upper()
            product=products.get(sku)
            if not order or not sku or not product:raise HTTPException(400,f"Dòng {rn}: thiếu/mapping lỗi SO_HOA_DON/MA_SKU")
            od=parse_date(d.get("NGAY_DON"));pd=parse_date(d.get("NGAY_GIAO"))
            if not od or not pd or pd!=od+datetime.timedelta(days=1):raise HTTPException(400,f"Dòng {rn}: VAL01/VAL02")
            bank_code=str(d.get("MA_TKNH") or "").strip().upper()
            bank=None
            for b in c.execute("SELECT id,ma_tknh,bank_name,account_no,account_name,status FROM qtgh_receiving_bank_account WHERE status='ACTIVE'"):
                bd=dict(b)
                candidates={
                    str(bd.get("id") or "").strip().upper(),
                    str(bd.get("ma_tknh") or "").strip().upper(),
                    str(bd.get("bank_name") or "").strip().upper(),
                    str(bd.get("account_no") or "").strip().upper(),
                }
                if bank_code in candidates:
                    bank=bd
                    break
            if not bank:
                raise HTTPException(400,f"Dòng {rn}: tài khoản nhận {d.get('MA_TKNH')} không hợp lệ")
            sale_qty,promo_qty,price_vat,line_discount,amount_due=build_line_payload(d,product)
            loai=str(d.get("LOAI_DON") or "").strip().upper()
            if loai not in ("L","B"):
                raise HTTPException(400,f"Dòng {rn}: LOAI_DON phải là L hoặc B")
            kh=str(d.get("MA_KH_NGUON") or "").strip()
            tl=money(d.get("THUONG_TICH_LUY"));tb=money(d.get("THUONG_TRUNG_BAY"))
            c.execute("""INSERT INTO qtgh_prep_line(
              prep_batch_id,source_row_no,loai_don,ma_don_nguon,order_date,planned_delivery_date,
              planned_delivery_staff_code,planned_driver_code,planned_vehicle_code,planned_lot_code,
              delivery_sequence,receiving_bank_id,ma_nvtt,ma_kh_chuan,ma_kh_mbw,ma_kh_dms,
              ma_sku,ten_sku,sale_qty_su,promo_qty_su,unit_price_vat,line_discount,
              order_reward_accum,order_reward_display,order_reward_other,don_app,amount_due_order,raw_payload_json,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (prep_batch_id,rn,loai,order,str(od),str(pd),
             str(d.get("MA_NV_GIAO_HANG_NGHIEP_VU") or ""),str(d.get("MA_NV_LAI_XE_NGHIEP_VU") or ""),
             str(d.get("PHUONG_TIEN") or ""),str(d.get("LO_GIAO_HANG") or ""),
             int(d.get("THU_TU_GIAO") or 0) if str(d.get("THU_TU_GIAO") or "").strip() else None,
             bank["id"],str(d.get("MA_NV_KD_NGHIEP_VU") or ""),"",
             kh if loai=="B" else "",kh if loai=="L" else "",sku,str(d.get("TEN_SKU") or product.get("TEN_SKU") or ""),
             str(sale_qty),str(promo_qty),price_vat,line_discount,tl,tb,money(d.get("GIAM_TRU_CAP_DON_KHAC")),str(d.get("DON_APP") or ""),amount_due,
             json.dumps(d,ensure_ascii=False,default=str),now()))
            order_due[order]=amount_due
            order_meta[order]={"planned_delivery_date":str(pd),"planned_delivery_staff_code":str(d.get("MA_NV_GIAO_HANG_NGHIEP_VU") or ""),
              "planned_driver_code":str(d.get("MA_NV_LAI_XE_NGHIEP_VU") or ""),"planned_vehicle_code":str(d.get("PHUONG_TIEN") or ""),
              "planned_lot_code":str(d.get("LO_GIAO_HANG") or ""),"customer_code":kh,"loai_don":loai}
        order_due={}
        for rr in c.execute("""SELECT ma_don_nguon,
                     COALESCE(SUM(amount_due_order),0) A,
                     COALESCE(MAX(order_reward_accum),0) B,
                     COALESCE(MAX(order_reward_display),0) C
              FROM qtgh_prep_line
              WHERE prep_batch_id=?
              GROUP BY ma_don_nguon""",(prep_batch_id,)):
            order_due[rr["ma_don_nguon"]]=max(0,int(rr["A"] or 0)-int(rr["B"] or 0)-int(rr["C"] or 0))
        total_amount=sum(order_due.values())
        c.execute("UPDATE qtgh_prep_batch SET total_orders=?,total_amount=? WHERE prep_batch_id=?",(len(order_due),total_amount,prep_batch_id))
        groups={}
        for order,m in order_meta.items():
            key=(m["planned_delivery_date"],m["planned_lot_code"],m["planned_delivery_staff_code"]);groups.setdefault(key,[]).append(order)
        lot_ids=[]
        for (pdate,lot_code,nvgh),orders in groups.items():
            pid="LOT-"+uuid.uuid4().hex[:12].upper();first=order_meta[orders[0]]
            customers={order_meta[o]["customer_code"] for o in orders if order_meta[o]["customer_code"]};amount=sum(order_due[o] for o in orders)
            c.execute("""INSERT INTO qtgh_print_lot(print_lot_id,prep_batch_id,planned_delivery_date,planned_delivery_staff_code,
              planned_driver_code,planned_vehicle_code,planned_lot_code,status,order_count,customer_count,total_amount,created_by,created_at,version)
              VALUES(?,?,?,?,?,?,?,'DA_NAP_HOP_LE',?,?,?,?,?,1)""",
              (pid,prep_batch_id,pdate,nvgh,first["planned_driver_code"],first["planned_vehicle_code"],lot_code,len(orders),len(customers),amount,uploaded_by,now()))
            for o in orders:c.execute("INSERT INTO qtgh_print_lot_order(print_lot_id,loai_don,ma_don_nguon) VALUES(?,?,?)",(pid,order_meta[o]["loai_don"],o))
            lot_ids.append(pid)
        c.execute("""INSERT INTO qtgh_delivery_audit(event_type,object_type,object_id,username,occurred_at,after_json)
                     VALUES('PREP_COMMIT','PREP_BATCH',?,?,?,?)""",
                     (prep_batch_id,uploaded_by,now(),json.dumps({"orders":len(order_due),"lines":len(rows),"lots":lot_ids,"total_amount":total_amount},ensure_ascii=False)))
        c.commit()
    except HTTPException:
        c.rollback();raise
    except Exception as e:
        c.rollback();raise HTTPException(400,str(e))
    finally:c.close()
    return {"prep_batch_id":prep_batch_id,"status":"DA_NAP_HOP_LE","total_orders":len(order_due),"total_lines":len(rows),"total_amount":total_amount,"print_lot_ids":lot_ids}

@router.get("/print-lot/{print_lot_id}/preview")
def print_lot_preview(print_lot_id:str):
    # VG_PRODUCT_NAMES_V1
    from .qtgh_product_print_names import product_names, lot_names, display_name
    c=conn()
    lot=c.execute("SELECT * FROM qtgh_print_lot WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if not lot:
        c.close()
        raise HTTPException(404,"Không tìm thấy PRINT LOT")

    orders=[dict(r) for r in c.execute("""
      SELECT o.loai_don,
             o.ma_don_nguon,
             MIN(p.delivery_sequence) AS delivery_sequence,
             MIN(COALESCE(NULLIF(p.ma_kh_dms,''),NULLIF(p.ma_kh_mbw,''),NULLIF(p.ma_kh_chuan,''),'')) AS customer_code
      FROM qtgh_print_lot_order o
      LEFT JOIN qtgh_prep_line p
        ON p.prep_batch_id=?
       AND p.ma_don_nguon=o.ma_don_nguon
      WHERE o.print_lot_id=?
      GROUP BY o.loai_don,o.ma_don_nguon
      ORDER BY
        CASE WHEN MIN(p.delivery_sequence) IS NULL THEN 1 ELSE 0 END,
        MIN(p.delivery_sequence),
        customer_code,
        o.ma_don_nguon
    """,(lot["prep_batch_id"],print_lot_id)).fetchall()]

    products=product_map()
    promo_prices=promo_price_index(master_rows("price"))
    mapped_names=lot_names(c, print_lot_id, product_names(c))
    out=[]
    lot_total=0

    for o in orders:
        lines=[dict(r) for r in c.execute("""
          SELECT *
          FROM qtgh_prep_line
          WHERE prep_batch_id=? AND ma_don_nguon=?
          ORDER BY COALESCE(delivery_sequence,999999),id
        """,(lot["prep_batch_id"],o["ma_don_nguon"])).fetchall()]
        if not lines:
            continue

        first=lines[0]
        raw0=json.loads(first["raw_payload_json"] or "{}")
        customer_code=first["ma_kh_dms"] or first["ma_kh_mbw"] or first["ma_kh_chuan"] or ""
        customer=resolve_customer(customer_code)
        nvkd=resolve_staff(first["ma_nvtt"])
        nvgh=resolve_staff(first["planned_delivery_staff_code"])
        bank=get_bank(first["receiving_bank_id"])

        A=sum(int(x["amount_due_order"] or 0) for x in lines)
        B=max(int(x["order_reward_accum"] or 0) for x in lines)
        C=max(int(x["order_reward_display"] or 0) for x in lines)
        final_payable=max(0,A-B-C)
        lot_total+=final_payable

        print_lines=[]
        for x in lines:
            raw=json.loads(x["raw_payload_json"] or "{}")
            sku=str(x["ma_sku"] or "").strip().upper()
            prod=products.get(sku,{})
            price=int(x["unit_price_vat"] or 0)
            disc=int(x["line_discount"] or 0)
            ratio=D(prod.get("SO_SU_THUNG") or 1)
            sale_qty=D(raw.get("SL_SU")) + D(raw.get("SL_THUNG"))*ratio
            after=money((D(price)*sale_qty-D(disc))/sale_qty) if sale_qty>0 else 0

            print_lines.append({
              "sku":sku,
              "name":display_name(mapped_names, sku, x["ten_sku"]),
              "qc":prod.get("SO_SU_THUNG") or "",
              "sl_thung":raw.get("SL_THUNG") or 0,
              "sl_le":raw.get("SL_SU") or 0,
              "sl_km_thung":raw.get("SL_KM_THUNG") or 0,
              "sl_km_le":raw.get("SL_KM_SU") or 0,
              "unit_price_promo_vat":promo_reference_price(promo_prices,sku,first["order_date"],prod),
              "unit_price_original_vat":price,
              "unit_price_after_discount":after,
              "line_discount":disc,
              "line_amount":int(x["amount_due_order"] or 0),
            })

        out.append({
          "invoice_no":o["ma_don_nguon"],
          "source_type":o["loai_don"],
          "delivery_sequence":o.get("delivery_sequence"),
          "order_date":first["order_date"],
          "customer":{
            "canonical_code":customer.get("MA_KH_CHUAN") or customer_code,
            "code":customer_code,
            "name":customer.get("TEN_KH") or customer.get("TEN_KHACH_HANG") or "",
            "phone":customer.get("SDT_CHINH") or customer.get("SO_DIEN_THOAI") or "",
            "delivery_address":raw0.get("DIA_CHI_GIAO_HANG") or customer.get("DIA_CHI") or "",
          },
          "sales_staff":{
            "code":first["ma_nvtt"],
            "name":nvkd.get("TEN_NV") or nvkd.get("HO_TEN") or "",
            "phone":nvkd.get("SDT") or nvkd.get("SO_DIEN_THOAI") or "",
          },
          "delivery_staff":{
            "code":first["planned_delivery_staff_code"],
            "name":nvgh.get("TEN_NV") or nvgh.get("HO_TEN") or "",
            "phone":nvgh.get("SDT") or nvgh.get("SO_DIEN_THOAI") or "",
          },
          "bank":{
            "bank_name":bank.get("bank_name") or "",
            "account_no":bank.get("account_no") or "",
            "account_name":bank.get("account_name") or "",
          },
          "lines":print_lines,
          "total_goods_A":A,
          "reward_accum_B":B,
          "reward_display_C":C,
          "final_payable_D":final_payable
        })

    c.close()
    lot_dict=dict(lot)
    lot_dict["total_amount"]=lot_total
    return {"lot":lot_dict,"orders":out,"count":len(out)}

