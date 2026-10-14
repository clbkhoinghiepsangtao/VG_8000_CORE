
import sqlite3, json, datetime, uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from collections import defaultdict
from io import BytesIO

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

def conn():
    c=sqlite3.connect(str(DB_PATH))
    c.row_factory=sqlite3.Row
    return c

def D(v):
    if v in (None,""): return Decimal("0")
    try: return Decimal(str(v))
    except: return Decimal("0")

def money(v):
    return int(D(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def sval(v):
    return str(v or "").strip()

def up(v):
    return sval(v).upper()

def vget(d,*keys):
    for k in keys:
        if k in d and d[k] not in (None,""):
            return d[k]
    return None

def parse_date(v):
    if v in (None,""): return None
    if isinstance(v,(int,float)) and not isinstance(v,bool):
        n=float(v)
        if 20000 <= n <= 80000:
            return datetime.date(1899,12,30)+datetime.timedelta(days=int(n))
    s=sval(v)
    try:
        if s.replace(".","",1).isdigit():
            n=float(s)
            if 20000 <= n <= 80000:
                return datetime.date(1899,12,30)+datetime.timedelta(days=int(n))
    except: pass
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%Y/%m/%d","%Y-%m-%d %H:%M:%S"):
        try: return datetime.datetime.strptime(s[:19],fmt).date()
        except: pass
    try: return datetime.date.fromisoformat(s[:10])
    except: return None

def table_exists(c,t):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone() is not None

def ensure_schema(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS qtgh_source_projection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_system TEXT NOT NULL,
      source_batch_id INTEGER,
      source_row_no INTEGER,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      ngay_don TEXT,
      ngay_giao TEXT,
      ma_lo TEXT,
      ma_nvgh TEXT,
      ma_lai_xe TEXT,
      ma_phuong_tien TEXT,
      ma_nvtt TEXT,
      ma_kh_chuan TEXT,
      ma_kh_mbw TEXT,
      ma_kh_dms TEXT,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sl_hang_ban_dat TEXT NOT NULL DEFAULT '0',
      sl_hang_km_dat TEXT NOT NULL DEFAULT '0',
      don_gia_co_vat INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_goc INTEGER NOT NULL DEFAULT 0,
      thuong_tich_luy_goc INTEGER NOT NULL DEFAULT 0,
      thuong_trung_bay_goc INTEGER NOT NULL DEFAULT 0,
      source_hash TEXT,
      UNIQUE(source_system,source_batch_id,source_row_no)
    );

    CREATE TABLE IF NOT EXISTS qtgh_draft_order(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_system TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'NHAP',
      vo_type TEXT NOT NULL DEFAULT 'GIAO_DU',
      accumulation_after INTEGER NOT NULL DEFAULT 0,
      display_after INTEGER NOT NULL DEFAULT 0,
      other_order_discount_after INTEGER NOT NULL DEFAULT 0,
      so_phai_thu_goc INTEGER NOT NULL DEFAULT 0,
      so_phai_thu_sau_qt INTEGER NOT NULL DEFAULT 0,
      tien_mat INTEGER NOT NULL DEFAULT 0,
      tien_ck_xac_nhan INTEGER NOT NULL DEFAULT 0,
      so_du_co_su_dung INTEGER NOT NULL DEFAULT 0,
      can_tru INTEGER NOT NULL DEFAULT 0,
      cong_no_kh INTEGER NOT NULL DEFAULT 0,
      bank_txn_id TEXT,
      bank_account TEXT,
      created_at TEXT,
      updated_at TEXT,
      locked_at TEXT,
      locked_by TEXT,
      UNIQUE(source_system,ma_don_nguon)
    );

    CREATE TABLE IF NOT EXISTS qtgh_draft_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sl_hang_ban_dat TEXT NOT NULL,
      sl_hang_ban_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_ban_thuc_giao TEXT NOT NULL DEFAULT '0',
      sl_hang_km_dat TEXT NOT NULL DEFAULT '0',
      sl_hang_km_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_km_thuc_giao TEXT NOT NULL DEFAULT '0',
      don_gia_co_vat INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_goc INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_sau INTEGER NOT NULL DEFAULT 0,
      thanh_tien_sau INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS qtgh_session(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ma_phien_qt TEXT UNIQUE NOT NULL,
      ngay_giao TEXT,
      ma_nvgh TEXT,
      ma_lo TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_at TEXT,
      locked_at TEXT,
      locked_by TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_session_order(
      session_id INTEGER NOT NULL,
      draft_order_id INTEGER NOT NULL,
      PRIMARY KEY(session_id,draft_order_id)
    );

    CREATE TABLE IF NOT EXISTS qtgh_cash_receipt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_type TEXT NOT NULL,
      source_id INTEGER NOT NULL,
      ma_nvgh TEXT,
      expected_amount INTEGER NOT NULL DEFAULT 0,
      actual_amount INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'CHO_THU',
      created_at TEXT,
      locked_at TEXT,
      locked_by TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_return_note(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CHO_KHO',
      created_at TEXT,
      locked_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_return_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      return_note_id INTEGER NOT NULL,
      ma_sku TEXT NOT NULL,
      sl_hang_ban_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_km_tra TEXT NOT NULL DEFAULT '0',
      kho_nhan_hang_ban TEXT NOT NULL DEFAULT '0',
      kho_nhan_hang_km TEXT NOT NULL DEFAULT '0'
    );

    CREATE TABLE IF NOT EXISTS qtgh_customer_debt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      ma_kh_chuan TEXT,
      ma_don_nguon TEXT NOT NULL,
      ma_nvgh TEXT,
      original_amount INTEGER NOT NULL,
      collected_amount INTEGER NOT NULL DEFAULT 0,
      balance INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CON_NO',
      created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_customer_debt_collection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_debt_id INTEGER NOT NULL,
      cash_amount INTEGER NOT NULL DEFAULT 0,
      bank_amount INTEGER NOT NULL DEFAULT 0,
      overpay_amount INTEGER NOT NULL DEFAULT 0,
      overpay_reason TEXT,
      created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_employee_debt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cash_receipt_id INTEGER NOT NULL,
      ma_nvgh TEXT,
      original_amount INTEGER NOT NULL,
      collected_amount INTEGER NOT NULL DEFAULT 0,
      balance INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CON_NO',
      created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_employee_debt_collection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_debt_id INTEGER NOT NULL,
      planned_amount INTEGER NOT NULL,
      cash_receipt_id INTEGER,
      created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_adjustment(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_doc_type TEXT NOT NULL,
      source_doc_id INTEGER NOT NULL,
      adjustment_type TEXT NOT NULL,
      delta_amount INTEGER NOT NULL DEFAULT 0,
      reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_by TEXT,
      approved_by TEXT,
      created_at TEXT,
      approved_at TEXT
    );

    CREATE TABLE IF NOT EXISTS qtgh_cash_inventory(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      inventory_date TEXT NOT NULL,
      opening_balance INTEGER NOT NULL DEFAULT 0,
      receipt_total INTEGER NOT NULL DEFAULT 0,
      system_closing INTEGER NOT NULL DEFAULT 0,
      actual_count INTEGER,
      variance INTEGER,
      status TEXT NOT NULL DEFAULT 'NHAP',
      counted_by TEXT,
      locked_at TEXT,
      UNIQUE(inventory_date)
    );
    """)
    c.commit()

ORDER_FIELDS=("MA_DON_NGUON","SO_HOA_DON","MA_DON_DMS","MA_DON_MBW","MA_DON","SO_DON","SO_DON_HANG","SO_CT","SO_CHUNG_TU","SO_PHIEU")
def detect_order_no(d):
    for k in ORDER_FIELDS:
        x=vget(d,k)
        if x not in (None,""):
            return sval(x)
    for k,x in d.items():
        ku=up(k)
        if x not in (None,"") and any(t in ku for t in ("DON","HOA_DON","CHUNG_TU","SO_CT","SO_PHIEU")):
            sx=sval(x)
            if sx:
                return sx
    return ""

def source_iter(c):
    # Primary integrated source used by XB.
    if table_exists(c,"xb_dms_mbw_batch") and table_exists(c,"xb_dms_mbw_row"):
        batches=c.execute("SELECT batch_id FROM xb_dms_mbw_batch WHERE UPPER(status)='COMMITTED'").fetchall()
        for b in batches:
            bid=b["batch_id"]
            rows=c.execute("SELECT row_no,payload_json FROM xb_dms_mbw_row WHERE batch_id=? AND UPPER(status)='VALID'",(bid,)).fetchall()
            for r in rows:
                try:d=json.loads(r["payload_json"])
                except: continue
                yield bid,r["row_no"],d
        return

    # Compatibility fallback.
    if table_exists(c,"xb_src_batch_v2") and table_exists(c,"xb_src_row_v2"):
        batches=c.execute("SELECT batch_id FROM xb_src_batch_v2 WHERE 1=0 /* SOURCE_SCOPE_CLEANUP_V1: QTGH excludes legacy DMS-Xa */").fetchall()
        for b in batches:
            bid=b["batch_id"]
            rows=c.execute("SELECT * FROM xb_src_row_v2 WHERE batch_id=?",(bid,)).fetchall()
            for r in rows:
                raw=None
                for k in ("payload_json","data_json","row_json","json_data","data"):
                    if k in r.keys() and r[k]:
                        raw=r[k]; break
                if not raw: continue
                try:d=json.loads(raw)
                except: continue
                yield bid,r["row_no"] if "row_no" in r.keys() else 0,d

def project_sources():
    c=conn(); ensure_schema(c)
    masters=_qtgh_master_product_info()
    inserted=0
    for bid,rowno,d in source_iter(c):
        loai=up(vget(d,"LOAI_DON"))
        if loai not in ("L","B"):
            continue
        ono=detect_order_no(d)
        sku=up(vget(d,"MA_SKU"))
        if not ono or not sku:
            continue

        # Source system inferred by business type.
        source_system="DMS" if loai=="L" else "MBW"
        day_order=parse_date(vget(d,"NGAY_DON"))
        day_delivery=parse_date(vget(d,"NGAY_GIAO","NGAY_DON"))

        # Prefer quantities already converted to SU; otherwise convert source
        # sale/promotion cases using the same master ratio as the rebuild flow.
        ratio=masters.get(sku,{"SO_SU_THUNG":Decimal("1")})["SO_SU_THUNG"]
        sale_standard=vget(d,"SL_HANG_BAN_DAT","SL_BAN_QUY_SU")
        promo_standard=vget(d,"SL_HANG_KM_DAT","SL_KM_QUY_SU")
        sale_qty=(D(sale_standard) if sale_standard is not None else
                  D(vget(d,"SL_SU","SO_LUONG_SU"))+
                  D(vget(d,"SL_THUNG","SL_THU","SO_LUONG_THUNG"))*ratio)
        promo_qty=(D(promo_standard) if promo_standard is not None else
                   D(vget(d,"SL_KM_SU","SO_LUONG_KM_SU","SL_KM","SO_LUONG_KM"))+
                   D(vget(d,"SL_KM_THUNG","SL_KM_TH","SO_LUONG_KM_THUNG"))*ratio)

        price_pre=D(vget(d,"DON_GIA_CHUA_VAT","DON_GIA_CHUA_THUE"))
        vat=D(vget(d,"VAT_RATE","VAT"))
        if vat>1: vat=vat/100
        price_vat=money(price_pre*(Decimal("1")+vat))
        if price_vat==0:
            price_vat=money(vget(d,"DON_GIA_CO_VAT","GIA_CO_VAT"))

        ck=money(vget(d,"CK_DONG_SKU","CK_KM_TIEN","CK_THUONG_MAI","CK_BANG_TIEN"))
        tl=money(vget(d,"THUONG_TICH_LUY"))
        tb=money(vget(d,"THUONG_TRUNG_BAY"))

        vals=(
          source_system,bid,rowno,loai,ono,
          str(day_order or ""),str(day_delivery or ""),
          sval(vget(d,"MA_LO","LO_GIAO_HANG","LO_GIAO")),
          up(vget(d,"MA_NVGH","MA_NV_GIAO_HANG","MA_NV_GIAO_HANG_NGHIEP_VU")),
          up(vget(d,"MA_LAI_XE","MA_NV_LAI_XE","MA_NV_LAI_XE_NGHIEP_VU")),
          up(vget(d,"MA_PHUONG_TIEN","PHUONG_TIEN","BIEN_SO")),
          up(vget(d,"MA_NVTT","MA_NV_KD_NGHIEP_VU","MA_NV_NGHIEP_VU","MA_NV")),
          sval(vget(d,"MA_KH_CHUAN")),
          sval(vget(d,"MA_KH_MBW")),
          sval(vget(d,"MA_KH_DMS","MA_KH")),
          sku,sval(vget(d,"TEN_SKU")),str(sale_qty),str(promo_qty),price_vat,ck,tl,tb
        )
        cur=c.execute("""INSERT OR IGNORE INTO qtgh_source_projection(
          source_system,source_batch_id,source_row_no,loai_don,ma_don_nguon,ngay_don,ngay_giao,ma_lo,
          ma_nvgh,ma_lai_xe,ma_phuong_tien,ma_nvtt,ma_kh_chuan,ma_kh_mbw,ma_kh_dms,ma_sku,ten_sku,
          sl_hang_ban_dat,sl_hang_km_dat,don_gia_co_vat,ck_km_dong_goc,thuong_tich_luy_goc,thuong_trung_bay_goc
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",vals)
        inserted += cur.rowcount
    c.commit()
    count=c.execute("SELECT COUNT(*) n FROM qtgh_source_projection").fetchone()["n"]
    orders=c.execute("SELECT COUNT(DISTINCT source_system||'|'||ma_don_nguon) n FROM qtgh_source_projection").fetchone()["n"]
    c.close()
    return {"inserted":inserted,"rows":count,"orders":orders}

def order_list(date_from=None,date_to=None):
    project_sources()
    c=conn(); ensure_schema(c)
    q="""SELECT source_system,loai_don,ma_don_nguon,MIN(ngay_giao) ngay_giao,
      MAX(ma_nvgh) ma_nvgh,MAX(ma_lai_xe) ma_lai_xe,MAX(ma_phuong_tien) ma_phuong_tien,MAX(ma_lo) ma_lo,
      MAX(ma_kh_chuan) ma_kh_chuan,MAX(ma_kh_mbw) ma_kh_mbw,MAX(ma_kh_dms) ma_kh_dms,
      COUNT(*) so_sku
      FROM qtgh_source_projection WHERE 1=1"""
    p=[]
    if date_from:
        q+=" AND ngay_giao>=?";p.append(date_from)
    if date_to:
        q+=" AND ngay_giao<=?";p.append(date_to)
    q+=" GROUP BY source_system,loai_don,ma_don_nguon ORDER BY ngay_giao DESC,ma_don_nguon DESC"
    rows=[dict(r) for r in c.execute(q,p).fetchall()]
    # status from draft
    states={(r["source_system"],r["ma_don_nguon"]):dict(r) for r in c.execute("SELECT source_system,ma_don_nguon,status,id FROM qtgh_draft_order").fetchall()}
    for r in rows:
        st=states.get((r["source_system"],r["ma_don_nguon"]))
        r["status"]=st["status"] if st else "CHUA_QT"
        r["draft_id"]=st["id"] if st else None
    c.close()
    return {"rows":rows,"count":len(rows)}

def calc_line(sale_dat,sale_tra,km_dat,km_tra,price_vat,ck_after):
    sale_actual=D(sale_dat)-D(sale_tra)
    promo_actual=D(km_dat)-D(km_tra)
    if sale_actual<0 or promo_actual<0: raise ValueError("QTGH_QTY_001")
    gross=(sale_actual+promo_actual)*D(price_vat)
    promo_value=promo_actual*D(price_vat)
    amount=money(gross-D(ck_after)-promo_value)
    return sale_actual,promo_actual,max(0,amount)

def create_or_get_draft(source_system,order_no):
    project_sources()
    c=conn(); ensure_schema(c)
    ex=c.execute("SELECT id FROM qtgh_draft_order WHERE source_system=? AND ma_don_nguon=?",(source_system,order_no)).fetchone()
    if ex:
        did=ex["id"]; c.close(); return get_draft(did)
    src=c.execute("SELECT * FROM qtgh_source_projection WHERE source_system=? AND ma_don_nguon=? ORDER BY id",(source_system,order_no)).fetchall()
    if not src:
        c.close(); raise ValueError("Không tìm thấy đơn nguồn")
    tl=max([r["thuong_tich_luy_goc"] for r in src] or [0])
    tb=max([r["thuong_trung_bay_goc"] for r in src] or [0])
    now=datetime.datetime.now().isoformat(timespec="seconds")
    cur=c.execute("""INSERT INTO qtgh_draft_order(
      source_system,ma_don_nguon,status,vo_type,accumulation_after,display_after,created_at,updated_at
    ) VALUES(?,?,'NHAP','GIAO_DU',?,?,?,?)""",(source_system,order_no,tl,tb,now,now))
    did=cur.lastrowid
    original_total=0
    for r in src:
        sale=D(r["sl_hang_ban_dat"]); promo=D(r["sl_hang_km_dat"])
        ck=r["ck_km_dong_goc"]; price=r["don_gia_co_vat"]
        sa,pa,amount=calc_line(sale,0,promo,0,price,ck)
        original_total+=amount
        c.execute("""INSERT INTO qtgh_draft_line(
          draft_order_id,ma_sku,ten_sku,sl_hang_ban_dat,sl_hang_ban_tra,sl_hang_ban_thuc_giao,
          sl_hang_km_dat,sl_hang_km_tra,sl_hang_km_thuc_giao,don_gia_co_vat,ck_km_dong_goc,ck_km_dong_sau,thanh_tien_sau
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (did,r["ma_sku"],r["ten_sku"],str(sale),"0",str(sa),str(promo),"0",str(pa),price,ck,ck,amount))
    due=max(0,original_total-tl-tb)
    c.execute("UPDATE qtgh_draft_order SET so_phai_thu_goc=?,so_phai_thu_sau_qt=?,tien_mat=? WHERE id=?",(due,due,due,did))
    c.commit(); c.close()
    return get_draft(did)

def get_draft(did):
    c=conn(); ensure_schema(c)
    h=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not h: c.close(); raise ValueError("Không tìm thấy quyết toán nháp")
    lines=[dict(r) for r in c.execute("SELECT * FROM qtgh_draft_line WHERE draft_order_id=? ORDER BY id",(did,)).fetchall()]
    out=dict(h);out["lines"]=lines
    c.close();return out

def update_draft(did,payload):
    c=conn(); ensure_schema(c)
    h=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not h: c.close(); raise ValueError("Không tìm thấy nháp")
    if h["status"]=="DA_KHOA": c.close(); raise ValueError("QTGH_LOCK_001")
    for x in payload.get("lines",[]):
        row=c.execute("SELECT * FROM qtgh_draft_line WHERE id=? AND draft_order_id=?",(int(x["id"]),did)).fetchone()
        if not row: continue
        sale_tra=D(x.get("sl_hang_ban_tra",0))
        km_tra=D(x.get("sl_hang_km_tra",0))
        if sale_tra>D(row["sl_hang_ban_dat"]) or km_tra>D(row["sl_hang_km_dat"]):
            c.close(); raise ValueError("QTGH_QTY_001")
        ck_after=money(x.get("ck_km_dong_sau",row["ck_km_dong_goc"]))
        sa,pa,amount=calc_line(row["sl_hang_ban_dat"],sale_tra,row["sl_hang_km_dat"],km_tra,row["don_gia_co_vat"],ck_after)
        c.execute("""UPDATE qtgh_draft_line SET sl_hang_ban_tra=?,sl_hang_ban_thuc_giao=?,
          sl_hang_km_tra=?,sl_hang_km_thuc_giao=?,ck_km_dong_sau=?,thanh_tien_sau=? WHERE id=?""",
          (str(sale_tra),str(sa),str(km_tra),str(pa),ck_after,amount,row["id"]))

    acc=money(payload.get("accumulation_after",h["accumulation_after"]))
    disp=money(payload.get("display_after",h["display_after"]))
    other=money(payload.get("other_order_discount_after",h["other_order_discount_after"]))
    subtotal=c.execute("SELECT COALESCE(SUM(thanh_tien_sau),0) x FROM qtgh_draft_line WHERE draft_order_id=?",(did,)).fetchone()["x"]
    due=max(0,subtotal-acc-disp-other)

    cash=money(payload.get("tien_mat",h["tien_mat"]))
    bank=money(payload.get("tien_ck_xac_nhan",h["tien_ck_xac_nhan"]))
    credit=money(payload.get("so_du_co_su_dung",h["so_du_co_su_dung"]))
    offset=money(payload.get("can_tru",h["can_tru"]))

    old_due=money(h["so_phai_thu_sau_qt"])
    old_cash=money(h["tien_mat"])
    old_bank=money(h["tien_ck_xac_nhan"])
    old_credit=money(h["so_du_co_su_dung"])
    old_offset=money(h["can_tru"])
    was_default_cash=(old_cash==old_due and old_bank==0 and old_credit==0 and old_offset==0)
    mode=str(payload.get("payment_mode","")).strip().upper()

    if was_default_cash and mode not in ("MIXED","BANK_100","DEBT"):
        if cash==old_cash and bank==0 and credit==0 and offset==0:
            cash=due

    total_paid=cash+bank+credit+offset
    if bank==0 and credit==0 and offset==0 and cash>due:
        cash=due
        total_paid=due
    if total_paid>due:
        c.close()
        raise ValueError(
            f"QTGH_PAY_001: Tổng thanh toán {total_paid:,} vượt số phải thu sau QT {due:,}. "
            f"TM={cash:,}; CK={bank:,}; Số dư={credit:,}; Cấn trừ={offset:,}"
        )
    debt=due-total_paid

    c.execute("""UPDATE qtgh_draft_order SET vo_type=?,accumulation_after=?,display_after=?,other_order_discount_after=?,
      so_phai_thu_sau_qt=?,tien_mat=?,tien_ck_xac_nhan=?,so_du_co_su_dung=?,can_tru=?,cong_no_kh=?,
      bank_txn_id=?,bank_account=?,updated_at=? WHERE id=?""",
      (payload.get("vo_type",h["vo_type"]),acc,disp,other,due,cash,bank,credit,offset,debt,
       sval(payload.get("bank_txn_id",h["bank_txn_id"])),sval(payload.get("bank_account",h["bank_account"])),
       datetime.datetime.now().isoformat(timespec="seconds"),did))
    c.commit(); c.close()
    return get_draft(did)

def lock_draft(did,user="pilot"):
    c=conn(); ensure_schema(c)
    h=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not h: c.close(); raise ValueError("Không tìm thấy nháp")
    if h["status"]=="DA_KHOA": c.close(); return get_draft(did)
    if h["tien_ck_xac_nhan"]>0 and (not h["bank_txn_id"] or not h["bank_account"]):
        c.close(); raise ValueError("QTGH_BANK_001: CK cần tài khoản nhận và mã giao dịch")
    if h["bank_txn_id"]:
        dup=c.execute("SELECT id FROM qtgh_draft_order WHERE bank_txn_id=? AND id<>?",(h["bank_txn_id"],did)).fetchone()
        if dup:
            c.close(); raise ValueError("QTGH_BANK_002")

    now=datetime.datetime.now().isoformat(timespec="seconds")
    src=c.execute("""SELECT MAX(ma_nvgh) ma_nvgh,MAX(ma_kh_chuan) ma_kh_chuan
      FROM qtgh_source_projection WHERE source_system=? AND ma_don_nguon=?""",(h["source_system"],h["ma_don_nguon"])).fetchone()
    c.execute("UPDATE qtgh_draft_order SET status='DA_KHOA',locked_at=?,locked_by=? WHERE id=?",(now,user,did))

    if h["tien_mat"]>0:
        c.execute("""INSERT INTO qtgh_cash_receipt(source_type,source_id,ma_nvgh,expected_amount,status,created_at)
          VALUES('QT_DON',?,?,?,'CHO_THU',?)""",(did,src["ma_nvgh"],h["tien_mat"],now))
    if h["cong_no_kh"]>0:
        c.execute("""INSERT INTO qtgh_customer_debt(draft_order_id,ma_kh_chuan,ma_don_nguon,ma_nvgh,original_amount,balance,status,created_at)
          VALUES(?,?,?,?,?,?,'CON_NO',?)""",(did,src["ma_kh_chuan"],h["ma_don_nguon"],src["ma_nvgh"],h["cong_no_kh"],h["cong_no_kh"],now))

    lines=c.execute("SELECT * FROM qtgh_draft_line WHERE draft_order_id=?",(did,)).fetchall()
    if any(D(r["sl_hang_ban_tra"])>0 or D(r["sl_hang_km_tra"])>0 for r in lines):
        cur=c.execute("INSERT INTO qtgh_return_note(draft_order_id,status,created_at) VALUES(?,'CHO_KHO',?)",(did,now))
        rnid=cur.lastrowid
        for r in lines:
            if D(r["sl_hang_ban_tra"])>0 or D(r["sl_hang_km_tra"])>0:
                c.execute("""INSERT INTO qtgh_return_line(return_note_id,ma_sku,sl_hang_ban_tra,sl_hang_km_tra)
                  VALUES(?,?,?,?)""",(rnid,r["ma_sku"],r["sl_hang_ban_tra"],r["sl_hang_km_tra"]))
    c.commit(); c.close()
    return get_draft(did)

def cash_receipts():
    c=conn(); ensure_schema(c)
    rows=[dict(r) for r in c.execute("SELECT * FROM qtgh_cash_receipt ORDER BY id DESC").fetchall()]
    c.close();return {"rows":rows}

def receive_cash(rid,actual,user="thuquy"):
    c=conn();ensure_schema(c)
    r=c.execute("SELECT * FROM qtgh_cash_receipt WHERE id=?",(rid,)).fetchone()
    if not r: c.close();raise ValueError("Không tìm thấy phiếu")
    actual=money(actual)
    if actual>r["expected_amount"]: c.close();raise ValueError("QTGH_CASH_001")
    shortage=r["expected_amount"]-actual
    status="DA_THU_DU" if shortage==0 else "THU_THIEU"
    now=datetime.datetime.now().isoformat(timespec="seconds")
    c.execute("UPDATE qtgh_cash_receipt SET actual_amount=?,status=?,locked_at=?,locked_by=? WHERE id=?",(actual,status,now,user,rid))
    if shortage>0 and r["source_type"]!="THU_NO_NVGH":
        c.execute("""INSERT INTO qtgh_employee_debt(cash_receipt_id,ma_nvgh,original_amount,balance,status,created_at)
          VALUES(?,?,?,?, 'CON_NO',?)""",(rid,r["ma_nvgh"],shortage,shortage,now))
    if r["source_type"]=="THU_NO_NVGH":
        rel=c.execute("SELECT employee_debt_id FROM qtgh_employee_debt_collection WHERE cash_receipt_id=?",(rid,)).fetchone()
        if rel:
            debt=c.execute("SELECT * FROM qtgh_employee_debt WHERE id=?",(rel["employee_debt_id"],)).fetchone()
            applied=min(actual,debt["balance"]);bal=debt["balance"]-applied
            c.execute("UPDATE qtgh_employee_debt SET collected_amount=collected_amount+?,balance=?,status=? WHERE id=?",
                      (applied,bal,"DA_TAT_TOAN" if bal==0 else "THU_MOT_PHAN",debt["id"]))
    c.commit(); c.close();return cash_receipts()

def return_notes():
    c=conn();ensure_schema(c)
    notes=[]
    for h in c.execute("SELECT * FROM qtgh_return_note ORDER BY id DESC").fetchall():
        x=dict(h);x["lines"]=[dict(r) for r in c.execute("SELECT * FROM qtgh_return_line WHERE return_note_id=?",(h["id"],)).fetchall()];notes.append(x)
    c.close();return {"rows":notes}

def receive_return(note_id,lines):
    c=conn();ensure_schema(c)
    try:
        if not c.execute("SELECT 1 FROM qtgh_return_note WHERE id=?", (note_id,)).fetchone():
            raise ValueError("Không tìm thấy phiếu trả hàng")
        validated=[]
        for x in lines:
            r=c.execute("SELECT * FROM qtgh_return_line WHERE id=? AND return_note_id=?",(int(x["id"]),note_id)).fetchone()
            if not r:
                raise ValueError("Dòng hàng không thuộc phiếu trả")
            hb=Decimal(str(x.get("kho_nhan_hang_ban") or 0));km=Decimal(str(x.get("kho_nhan_hang_km") or 0))
            if not hb.is_finite() or not km.is_finite() or hb<0 or km<0:
                raise ValueError("Số lượng kho nhận không được âm hoặc không hợp lệ")
            if hb>D(r["sl_hang_ban_tra"]) or km>D(r["sl_hang_km_tra"]):
                raise ValueError("Số lượng kho nhận vượt số lượng trả dự kiến")
            validated.append((str(hb),str(km),r["id"]))
        for hb,km,rid in validated:
            c.execute("UPDATE qtgh_return_line SET kho_nhan_hang_ban=?,kho_nhan_hang_km=? WHERE id=?",(hb,km,rid))
        shortage=c.execute("""SELECT COUNT(*) n FROM qtgh_return_line WHERE return_note_id=? AND
          (CAST(kho_nhan_hang_ban AS REAL)<CAST(sl_hang_ban_tra AS REAL) OR CAST(kho_nhan_hang_km AS REAL)<CAST(sl_hang_km_tra AS REAL))""",(note_id,)).fetchone()["n"]
        c.execute("UPDATE qtgh_return_note SET status=?,locked_at=? WHERE id=?",
          ("KHO_NHAN_THIEU" if shortage else "KHO_DA_NHAN_DU",datetime.datetime.now().isoformat(timespec="seconds"),note_id))
        c.commit()
    except Exception:
        c.rollback();raise
    finally:
        c.close()
    return return_notes()


def customer_debts():
    c=conn();ensure_schema(c)
    rows=[dict(r) for r in c.execute("SELECT * FROM qtgh_customer_debt ORDER BY id DESC").fetchall()]
    c.close();return {"rows":rows}

def collect_customer_debt(debt_id,cash,bank,reason=""):
    values=[Decimal(str(v or 0)) for v in (cash,bank)]
    if any(not v.is_finite() or v<0 for v in values):
        raise ValueError("Số tiền thu nợ không hợp lệ")
    cash,bank=[int(v.quantize(Decimal("1"),rounding=ROUND_HALF_UP)) for v in values]
    total=cash+bank
    if total<=0:
        raise ValueError("Số tiền thu nợ phải dương")
    c=conn();ensure_schema(c)
    try:
        c.execute("BEGIN IMMEDIATE")
        d=c.execute("SELECT * FROM qtgh_customer_debt WHERE id=?",(debt_id,)).fetchone()
        if not d:
            raise ValueError("Không tìm thấy nợ KH")
        over=max(0,total-d["balance"])
        if over>0 and not sval(reason):
            raise ValueError("QTGH_CREDIT_001")
        applied=min(total,d["balance"]);bal=d["balance"]-applied
        now=datetime.datetime.now().isoformat(timespec="seconds")
        c.execute("""INSERT INTO qtgh_customer_debt_collection(customer_debt_id,cash_amount,bank_amount,overpay_amount,overpay_reason,created_at)
          VALUES(?,?,?,?,?,?)""",(debt_id,cash,bank,over,sval(reason),now))
        c.execute("UPDATE qtgh_customer_debt SET collected_amount=collected_amount+?,balance=?,status=? WHERE id=?",
          (applied,bal,"DA_TAT_TOAN" if bal==0 else "THU_MOT_PHAN",debt_id))
        if cash>0:
            c.execute("""INSERT INTO qtgh_cash_receipt(source_type,source_id,ma_nvgh,expected_amount,status,created_at)
              VALUES('THU_NO_KH',?,?,?,'CHO_THU',?)""",(debt_id,d["ma_nvgh"],cash,now))
        c.commit()
    except Exception:
        c.rollback();raise
    finally:
        c.close()
    return customer_debts()


def employee_debts():
    c=conn();ensure_schema(c)
    rows=[dict(r) for r in c.execute("SELECT * FROM qtgh_employee_debt ORDER BY id DESC").fetchall()]
    c.close();return {"rows":rows}

def plan_employee_debt_collection(debt_id,amount):
    c=conn();ensure_schema(c)
    d=c.execute("SELECT * FROM qtgh_employee_debt WHERE id=?",(debt_id,)).fetchone()
    if not d: c.close();raise ValueError("Không tìm thấy nợ NVGH")
    amount=money(amount)
    if amount<=0 or amount>d["balance"]: c.close();raise ValueError("Số dự kiến thu không hợp lệ")
    now=datetime.datetime.now().isoformat(timespec="seconds")
    cur=c.execute("""INSERT INTO qtgh_cash_receipt(source_type,source_id,ma_nvgh,expected_amount,status,created_at)
      VALUES('THU_NO_NVGH',?,?,?,'CHO_THU',?)""",(debt_id,d["ma_nvgh"],amount,now))
    rid=cur.lastrowid
    c.execute("""INSERT INTO qtgh_employee_debt_collection(employee_debt_id,planned_amount,cash_receipt_id,created_at)
      VALUES(?,?,?,?)""",(debt_id,amount,rid,now))
    c.commit();c.close();return cash_receipts()

def adjustments():
    c=conn();ensure_schema(c)
    rows=[dict(r) for r in c.execute("SELECT * FROM qtgh_adjustment ORDER BY id DESC").fetchall()]
    c.close();return {"rows":rows}

def create_adjustment(doc_type,doc_id,adj_type,delta,reason,user="pilot"):
    if not sval(reason): raise ValueError("Bắt buộc lý do")
    c=conn();ensure_schema(c)
    c.execute("""INSERT INTO qtgh_adjustment(source_doc_type,source_doc_id,adjustment_type,delta_amount,reason,status,created_by,created_at)
      VALUES(?,?,?,?,?,'CHO_DUYET',?,?)""",(doc_type,doc_id,adj_type,money(delta),reason,user,datetime.datetime.now().isoformat(timespec="seconds")))
    c.commit();c.close();return adjustments()

def approve_adjustment(adj_id,user="duyet"):
    c=conn();ensure_schema(c)
    a=c.execute("SELECT * FROM qtgh_adjustment WHERE id=?",(adj_id,)).fetchone()
    if not a: c.close();raise ValueError("Không tìm thấy phiếu")
    if a["created_by"]==user: c.close();raise ValueError("QTGH_ADJ_001")
    c.execute("UPDATE qtgh_adjustment SET status='DA_DUYET',approved_by=?,approved_at=? WHERE id=?",
              (user,datetime.datetime.now().isoformat(timespec="seconds"),adj_id))
    c.commit();c.close();return adjustments()

def cash_inventory(date):
    c=conn();ensure_schema(c)
    prev=c.execute("SELECT system_closing FROM qtgh_cash_inventory WHERE inventory_date<? ORDER BY inventory_date DESC LIMIT 1",(date,)).fetchone()
    opening=prev["system_closing"] if prev else 0
    receipts=c.execute("""SELECT COALESCE(SUM(actual_amount),0) x FROM qtgh_cash_receipt
      WHERE status IN ('DA_THU_DU','THU_THIEU') AND substr(locked_at,1,10)=?""",(date,)).fetchone()["x"]
    closing=opening+receipts
    c.execute("""INSERT INTO qtgh_cash_inventory(inventory_date,opening_balance,receipt_total,system_closing,status)
      VALUES(?,?,?,?, 'NHAP')
      ON CONFLICT(inventory_date) DO UPDATE SET opening_balance=excluded.opening_balance,receipt_total=excluded.receipt_total,system_closing=excluded.system_closing""",
      (date,opening,receipts,closing))
    c.commit()
    row=dict(c.execute("SELECT * FROM qtgh_cash_inventory WHERE inventory_date=?",(date,)).fetchone())
    c.close();return row

def lock_cash_inventory(date,actual,user="thuquy"):
    c=conn();ensure_schema(c)
    actual=money(actual)
    row=c.execute("SELECT * FROM qtgh_cash_inventory WHERE inventory_date=?",(date,)).fetchone()
    if not row: c.close();raise ValueError("Chưa tạo kiểm kê")
    variance=actual-row["system_closing"]
    c.execute("UPDATE qtgh_cash_inventory SET actual_count=?,variance=?,status='DA_KHOA',counted_by=?,locked_at=? WHERE inventory_date=?",
              (actual,variance,user,datetime.datetime.now().isoformat(timespec="seconds"),date))
    c.commit();c.close();return cash_inventory(date)

def context_options(ngay_don=None, ma_nvgh=None):
    project_sources()
    c=conn(); ensure_schema(c)
    if not ngay_don:
        dates=[r["ngay_don"] for r in c.execute(
            "SELECT DISTINCT ngay_don FROM qtgh_source_projection WHERE COALESCE(ngay_don,'')<>'' ORDER BY ngay_don DESC"
        ).fetchall()]
        c.close()
        return {"dates":dates,"employees":[],"lots":[]}
    employees=[r["ma_nvgh"] for r in c.execute(
        "SELECT DISTINCT ma_nvgh FROM qtgh_source_projection WHERE ngay_don=? AND COALESCE(ma_nvgh,'')<>'' ORDER BY ma_nvgh",
        (ngay_don,)
    ).fetchall()]
    lots=[]
    if ma_nvgh:
        lots=[r["ma_lo"] for r in c.execute(
            "SELECT DISTINCT ma_lo FROM qtgh_source_projection WHERE ngay_don=? AND ma_nvgh=? AND COALESCE(ma_lo,'')<>'' ORDER BY ma_lo",
            (ngay_don,ma_nvgh)
        ).fetchall()]
    c.close()
    return {"dates":[ngay_don],"employees":employees,"lots":lots}

def order_list_scoped(ngay_don=None, ma_nvgh=None, ma_lo=None):
    project_sources()
    c=conn(); ensure_schema(c)
    q="""SELECT source_system,loai_don,ma_don_nguon,
      MIN(ngay_don) ngay_don, MIN(ngay_giao) ngay_giao,
      MAX(ma_nvgh) ma_nvgh,MAX(ma_lai_xe) ma_lai_xe,
      MAX(ma_phuong_tien) ma_phuong_tien,MAX(ma_lo) ma_lo,
      MAX(ma_kh_chuan) ma_kh_chuan,MAX(ma_kh_mbw) ma_kh_mbw,
      MAX(ma_kh_dms) ma_kh_dms,COUNT(*) so_sku
      FROM qtgh_source_projection WHERE 1=1"""
    p=[]
    if ngay_don:
        q+=" AND ngay_don=?"; p.append(ngay_don)
    if ma_nvgh:
        q+=" AND ma_nvgh=?"; p.append(ma_nvgh)
    if ma_lo:
        q+=" AND ma_lo=?"; p.append(ma_lo)
    q+=" GROUP BY source_system,loai_don,ma_don_nguon ORDER BY ngay_don DESC,ma_don_nguon DESC"
    rows=[dict(r) for r in c.execute(q,p).fetchall()]
    states={(r["source_system"],r["ma_don_nguon"]):dict(r) for r in c.execute(
        "SELECT source_system,ma_don_nguon,status,id FROM qtgh_draft_order"
    ).fetchall()}
    for r in rows:
        st=states.get((r["source_system"],r["ma_don_nguon"]))
        r["status"]=st["status"] if st else "CHUA_QT"
        r["draft_id"]=st["id"] if st else None
    c.close()
    return {"rows":rows,"count":len(rows)}

def ensure_ui_flow_columns():
    c=conn(); ensure_schema(c)
    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_source_projection)").fetchall()}
    for name,ddl in [("ten_kh","TEXT"),("ten_nvtt","TEXT")]:
        if name not in cols:
            c.execute(f"ALTER TABLE qtgh_source_projection ADD COLUMN {name} {ddl}")
    c.commit(); c.close()

def ui01_search_orders(q):
    ensure_ui_flow_columns()
    project_sources()
    term=sval(q)
    if not term:
        return {"rows":[]}
    like=f"%{term}%"
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT source_system,loai_don,ma_don_nguon,MIN(ngay_don) ngay_don,MIN(ngay_giao) ngay_giao,
             MAX(ma_nvgh) ma_nvgh,MAX(ma_nvtt) ma_nvtt,
             MAX(ma_kh_chuan) ma_kh_chuan,MAX(ma_kh_mbw) ma_kh_mbw,MAX(ma_kh_dms) ma_kh_dms,
             MAX(ma_lo) ma_lo,COUNT(*) so_sku
      FROM qtgh_source_projection
      WHERE ma_don_nguon LIKE ?
         OR ma_kh_chuan LIKE ? OR ma_kh_mbw LIKE ? OR ma_kh_dms LIKE ?
         OR ma_nvtt LIKE ?
      GROUP BY source_system,loai_don,ma_don_nguon
      ORDER BY ngay_giao DESC,ma_don_nguon DESC
      LIMIT 30
    """,(like,like,like,like,like)).fetchall()]
    c.close()
    return {"rows":rows}

def ui04_lot_orders(ngay_giao,ma_nvgh,ma_lo):
    ensure_ui_flow_columns()
    project_sources()
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT source_system,loai_don,ma_don_nguon,MIN(ngay_don) ngay_don,MIN(ngay_giao) ngay_giao,
             MAX(ma_nvgh) ma_nvgh,MAX(ma_lo) ma_lo,MAX(ma_kh_chuan) ma_kh_chuan,
             MAX(ma_kh_mbw) ma_kh_mbw,MAX(ma_kh_dms) ma_kh_dms,COUNT(*) so_sku
      FROM qtgh_source_projection
      WHERE ngay_giao=? AND ma_nvgh=? AND ma_lo=?
      GROUP BY source_system,loai_don,ma_don_nguon
      ORDER BY ma_don_nguon
    """,(ngay_giao,ma_nvgh,ma_lo)).fetchall()]
    drafts={(r["source_system"],r["ma_don_nguon"]):dict(r) for r in c.execute("SELECT * FROM qtgh_draft_order").fetchall()}
    out=[]
    c.close()
    for r in rows:
        d=drafts.get((r["source_system"],r["ma_don_nguon"]))
        if d:
            r.update({"abnormal":True,"draft_id":d["id"],"so_phai_thu":d["so_phai_thu_sau_qt"],
                      "tien_mat":d["tien_mat"],"tien_ck":d["tien_ck_xac_nhan"],
                      "cong_no_kh":d["cong_no_kh"],"status_qt":d["status"]})
        else:
            draft=create_or_get_draft(r["source_system"],r["ma_don_nguon"])
            r.update({"abnormal":False,"draft_id":draft["id"],"so_phai_thu":draft["so_phai_thu_sau_qt"],
                      "tien_mat":draft["so_phai_thu_sau_qt"],"tien_ck":0,
                      "cong_no_kh":0,"status_qt":"MAC_DINH_BINH_THUONG"})
        out.append(r)
    return {"rows":out,"count":len(out)}

def ui04_finalize_lot(ngay_giao,ma_nvgh,ma_lo,user="pilot"):
    data=ui04_lot_orders(ngay_giao,ma_nvgh,ma_lo)
    total_expected=0
    locked=[]
    for r in data["rows"]:
        d=get_draft(r["draft_id"])
        if d["status"]!="DA_KHOA":
            d=lock_draft(r["draft_id"],user)
        total_expected += d["tien_mat"]
        locked.append(d["id"])
    return {"orders":len(locked),"cash_expected":total_expected,
            "message":"Đã khóa các đơn và phát sinh phiếu thu sang UI05."}

# ===== QTGH V0.3 corrective flow helpers =====

def _qtgh_master_product_info():
    out={}
    try:
        from .xb_mapping_audit import _load_master_dataset
        c=conn()
        rows=_load_master_dataset(c,["dm01-product","product","DM01_SAN_PHAM"])
        c.close()
        for d in rows:
            sku=up(vget(d,"MA_SKU"))
            if not sku: continue
            ratio=D(vget(d,"SO_SU_THUNG"))
            vat=D(vget(d,"VAT_RATE"))
            if vat>1: vat=vat/100
            out[sku]={
                "SO_SU_THUNG": ratio if ratio>0 else Decimal("1"),
                "VAT_RATE": vat if vat>=0 else Decimal("0"),
            }
    except Exception:
        pass
    return out

def qtgh_v03_rebuild_projection():
    c=conn(); ensure_schema(c)
    # receiving bank account config
    c.execute("""
    CREATE TABLE IF NOT EXISTS qtgh_receiving_bank_account(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      bank_name TEXT NOT NULL,
      account_no TEXT NOT NULL,
      account_name TEXT,
      status TEXT NOT NULL DEFAULT 'ACTIVE',
      UNIQUE(bank_name,account_no)
    )
    """)
    # session-level receipt identity
    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_cash_receipt)").fetchall()}
    if "session_key" not in cols:
        c.execute("ALTER TABLE qtgh_cash_receipt ADD COLUMN session_key TEXT")
    c.commit()

    # remove only QTGH projection/drafts/derived docs, preserve source XB
    for t in [
        "qtgh_employee_debt_collection","qtgh_employee_debt",
        "qtgh_customer_debt_collection","qtgh_customer_debt",
        "qtgh_return_line","qtgh_return_note",
        "qtgh_cash_receipt","qtgh_session_order","qtgh_session",
        "qtgh_draft_line","qtgh_draft_order","qtgh_source_projection"
    ]:
        try:c.execute(f"DELETE FROM {t}")
        except:pass
    c.commit()

    masters=_qtgh_master_product_info()
    inserted=0
    for bid,rowno,d in source_iter(c):
        loai=up(vget(d,"LOAI_DON"))
        if loai not in ("L","B"): continue
        ono=detect_order_no(d); sku=up(vget(d,"MA_SKU"))
        if not ono or not sku: continue

        mi=masters.get(sku,{"SO_SU_THUNG":Decimal("1"),"VAT_RATE":Decimal("0")})
        ratio=mi["SO_SU_THUNG"]

        sale_su=D(vget(d,"SL_SU","SO_LUONG_SU"))
        sale_case=D(vget(d,"SL_THUNG","SO_LUONG_THUNG"))
        sale_qty=sale_su + sale_case*ratio

        promo_su=D(vget(d,"SL_KM_SU","SO_LUONG_KM_SU","SL_KM"))
        promo_case=D(vget(d,"SL_KM_THUNG","SO_LUONG_KM_THUNG"))
        promo_qty=promo_su + promo_case*ratio

        price_pre=D(vget(d,"DON_GIA_CHUA_VAT","DON_GIA_CHUA_THUE"))
        vat=D(vget(d,"VAT_RATE","VAT"))
        if vat>1: vat=vat/100
        if vat==0:
            vat=mi["VAT_RATE"]
        price_vat=money(price_pre*(Decimal("1")+vat))
        if price_pre==0:
            price_vat=money(vget(d,"DON_GIA_CO_VAT","GIA_CO_VAT"))

        day_order=parse_date(vget(d,"NGAY_DON"))
        day_delivery=parse_date(vget(d,"NGAY_GIAO","NGAY_DON"))
        source_system="DMS" if loai=="L" else "MBW"

        vals=(
          source_system,bid,rowno,loai,ono,
          str(day_order or ""),str(day_delivery or ""),
          sval(vget(d,"MA_LO","LO_GIAO_HANG","LO_GIAO")),
          up(vget(d,"MA_NVGH","MA_NV_GIAO_HANG","MA_NV_GIAO_HANG_NGHIEP_VU")),
          up(vget(d,"MA_LAI_XE","MA_NV_LAI_XE","MA_NV_LAI_XE_NGHIEP_VU")),
          up(vget(d,"MA_PHUONG_TIEN","PHUONG_TIEN","BIEN_SO")),
          up(vget(d,"MA_NVTT","MA_NV_KD_NGHIEP_VU","MA_NV_NGHIEP_VU","MA_NV")),
          sval(vget(d,"MA_KH_CHUAN")),
          sval(vget(d,"MA_KH_MBW")),
          sval(vget(d,"MA_KH_DMS","MA_KH")),
          sku,sval(vget(d,"TEN_SKU")),
          str(sale_qty),str(promo_qty),
          price_vat,
          money(vget(d,"CK_DONG_SKU","CK_KM_TIEN","CK_THUONG_MAI","CK_BANG_TIEN")),
          money(vget(d,"THUONG_TICH_LUY")),
          money(vget(d,"THUONG_TRUNG_BAY"))
        )
        c.execute("""INSERT OR IGNORE INTO qtgh_source_projection(
          source_system,source_batch_id,source_row_no,loai_don,ma_don_nguon,ngay_don,ngay_giao,ma_lo,
          ma_nvgh,ma_lai_xe,ma_phuong_tien,ma_nvtt,ma_kh_chuan,ma_kh_mbw,ma_kh_dms,ma_sku,ten_sku,
          sl_hang_ban_dat,sl_hang_km_dat,don_gia_co_vat,ck_km_dong_goc,thuong_tich_luy_goc,thuong_trung_bay_goc
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",vals)
        inserted+=1
    c.commit();c.close()
    return {"rows":inserted}

def receiving_banks():
    c=conn();ensure_schema(c)
    c.execute("""CREATE TABLE IF NOT EXISTS qtgh_receiving_bank_account(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      bank_name TEXT NOT NULL,
      account_no TEXT NOT NULL,
      account_name TEXT,
      status TEXT NOT NULL DEFAULT 'ACTIVE',
      UNIQUE(bank_name,account_no)
    )""")
    rows=[dict(r) for r in c.execute(
      "SELECT * FROM qtgh_receiving_bank_account WHERE status='ACTIVE' ORDER BY bank_name,account_no"
    ).fetchall()]
    c.close()
    return {"rows":rows}

def add_receiving_bank(bank_name,account_no,account_name=""):
    if not sval(bank_name) or not sval(account_no):
        raise ValueError("Thiếu ngân hàng hoặc số tài khoản")
    c=conn();ensure_schema(c)
    c.execute("""INSERT OR IGNORE INTO qtgh_receiving_bank_account(bank_name,account_no,account_name,status)
      VALUES(?,?,?,'ACTIVE')""",(sval(bank_name),sval(account_no),sval(account_name)))
    c.commit();c.close()
    return receiving_banks()

def set_draft_full_break(did):
    d=get_draft(did)
    lines=[]
    for x in d["lines"]:
        lines.append({
            "id":x["id"],
            "sl_hang_ban_tra":x["sl_hang_ban_dat"],
            "sl_hang_km_tra":x["sl_hang_km_dat"],
            "ck_km_dong_sau":0
        })
    return update_draft(did,{
        "vo_type":"VO_100",
        "lines":lines,
        "accumulation_after":0,
        "display_after":0,
        "other_order_discount_after":0,
        "tien_mat":0,
        "tien_ck_xac_nhan":0,
        "so_du_co_su_dung":0,
        "can_tru":0,
        "bank_txn_id":"",
        "bank_account":""
    })

def set_draft_payment_mode(did,mode,bank_account="",bank_txn_id=""):
    d=get_draft(did)
    due=d["so_phai_thu_sau_qt"]
    payload={
        "lines":[],
        "accumulation_after":d["accumulation_after"],
        "display_after":d["display_after"],
        "other_order_discount_after":d["other_order_discount_after"],
        "bank_account":bank_account,
        "bank_txn_id":bank_txn_id
    }
    if mode=="CASH_100":
        payload.update({"tien_mat":due,"tien_ck_xac_nhan":0})
    elif mode=="BANK_100":
        payload.update({"tien_mat":0,"tien_ck_xac_nhan":due})
    elif mode=="MIXED":
        # keep current user-entered amounts
        payload.update({"tien_mat":d["tien_mat"],"tien_ck_xac_nhan":d["tien_ck_xac_nhan"]})
    elif mode=="DEBT":
        # keep current paid amounts, debt auto-computed
        payload.update({"tien_mat":d["tien_mat"],"tien_ck_xac_nhan":d["tien_ck_xac_nhan"]})
    return update_draft(did,payload)

def abnormal_drafts_scoped(ngay_giao=None,ma_nvgh=None,ma_lo=None):
    c=conn();ensure_schema(c)
    q="""SELECT d.*, MAX(s.ngay_giao) ngay_giao,MAX(s.ma_nvgh) ma_nvgh,MAX(s.ma_lo) ma_lo,
      MAX(s.ma_kh_mbw) ma_kh_mbw,MAX(s.ma_kh_dms) ma_kh_dms
      FROM qtgh_draft_order d
      JOIN qtgh_source_projection s
        ON s.source_system=d.source_system AND s.ma_don_nguon=d.ma_don_nguon
      WHERE d.vo_type<>'GIAO_DU' OR d.tien_ck_xac_nhan>0 OR d.cong_no_kh>0"""
    p=[]
    if ngay_giao:q+=" AND s.ngay_giao=?";p.append(ngay_giao)
    if ma_nvgh:q+=" AND s.ma_nvgh=?";p.append(ma_nvgh)
    if ma_lo:q+=" AND s.ma_lo=?";p.append(ma_lo)
    q+=" GROUP BY d.id ORDER BY d.updated_at DESC"
    rows=[dict(r) for r in c.execute(q,p).fetchall()]
    c.close();return {"rows":rows}

def delivery_context(ngay_giao=None,ma_nvgh=None):
    c=conn();ensure_schema(c)
    if not ngay_giao:
        dates=[r["ngay_giao"] for r in c.execute(
          "SELECT DISTINCT ngay_giao FROM qtgh_source_projection WHERE COALESCE(ngay_giao,'')<>'' ORDER BY ngay_giao DESC"
        ).fetchall()]
        c.close();return {"dates":dates,"employees":[],"lots":[]}
    employees=[r["ma_nvgh"] for r in c.execute(
      "SELECT DISTINCT ma_nvgh FROM qtgh_source_projection WHERE ngay_giao=? AND COALESCE(ma_nvgh,'')<>'' ORDER BY ma_nvgh",(ngay_giao,)
    ).fetchall()]
    lots=[]
    if ma_nvgh:
        lots=[r["ma_lo"] for r in c.execute(
          "SELECT DISTINCT ma_lo FROM qtgh_source_projection WHERE ngay_giao=? AND ma_nvgh=? AND COALESCE(ma_lo,'')<>'' ORDER BY ma_lo",
          (ngay_giao,ma_nvgh)
        ).fetchall()]
    c.close();return {"dates":[ngay_giao],"employees":employees,"lots":lots}

def _lock_order_without_cash_receipt(did,user="pilot"):
    c=conn();ensure_schema(c)
    h=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not h: c.close();raise ValueError("Không tìm thấy nháp")
    if h["status"]=="DA_KHOA": c.close();return
    if h["tien_ck_xac_nhan"]>0 and (not h["bank_txn_id"] or not h["bank_account"]):
        c.close();raise ValueError("QTGH_BANK_001")
    now=datetime.datetime.now().isoformat(timespec="seconds")
    src=c.execute("""SELECT MAX(ma_nvgh) ma_nvgh,MAX(ma_kh_chuan) ma_kh_chuan
      FROM qtgh_source_projection WHERE source_system=? AND ma_don_nguon=?""",
      (h["source_system"],h["ma_don_nguon"])).fetchone()
    c.execute("UPDATE qtgh_draft_order SET status='DA_KHOA',locked_at=?,locked_by=? WHERE id=?",(now,user,did))
    if h["cong_no_kh"]>0:
        c.execute("""INSERT INTO qtgh_customer_debt(draft_order_id,ma_kh_chuan,ma_don_nguon,ma_nvgh,original_amount,balance,status,created_at)
          VALUES(?,?,?,?,?,?,'CON_NO',?)""",(did,src["ma_kh_chuan"],h["ma_don_nguon"],src["ma_nvgh"],h["cong_no_kh"],h["cong_no_kh"],now))
    lines=c.execute("SELECT * FROM qtgh_draft_line WHERE draft_order_id=?",(did,)).fetchall()
    if any(D(r["sl_hang_ban_tra"])>0 or D(r["sl_hang_km_tra"])>0 for r in lines):
        cur=c.execute("INSERT INTO qtgh_return_note(draft_order_id,status,created_at) VALUES(?,'CHO_KHO',?)",(did,now))
        rnid=cur.lastrowid
        for r in lines:
            if D(r["sl_hang_ban_tra"])>0 or D(r["sl_hang_km_tra"])>0:
                c.execute("""INSERT INTO qtgh_return_line(return_note_id,ma_sku,sl_hang_ban_tra,sl_hang_km_tra)
                  VALUES(?,?,?,?)""",(rnid,r["ma_sku"],r["sl_hang_ban_tra"],r["sl_hang_km_tra"]))
    c.commit();c.close()

def finalize_lot_session(ngay_giao,ma_nvgh,ma_lo,user="pilot"):
    data=ui04_lot_orders(ngay_giao,ma_nvgh,ma_lo)
    if not data["rows"]:
        raise ValueError("Không có đơn trong lô")
    session_key=f"{ngay_giao}|{ma_nvgh}|{ma_lo}"
    c=conn();ensure_schema(c)
    ex=c.execute("SELECT id,status FROM qtgh_session WHERE ngay_giao=? AND ma_nvgh=? AND ma_lo=? ORDER BY id DESC LIMIT 1",
                 (ngay_giao,ma_nvgh,ma_lo)).fetchone()
    if ex and ex["status"]=="DA_KHOA":
        c.close();return {"session_id":ex["id"],"message":"Phiên đã khóa trước đó."}
    if ex:
        sid=ex["id"]
    else:
        ma_phien="QT-"+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+"-"+ma_nvgh+"-"+ma_lo
        cur=c.execute("""INSERT INTO qtgh_session(ma_phien_qt,ngay_giao,ma_nvgh,ma_lo,status,created_at)
          VALUES(?,?,?,?, 'NHAP',?)""",(ma_phien,ngay_giao,ma_nvgh,ma_lo,datetime.datetime.now().isoformat(timespec="seconds")))
        sid=cur.lastrowid
    c.commit();c.close()

    total_cash=0
    for r in data["rows"]:
        did=r["draft_id"]
        d=get_draft(did)
        _lock_order_without_cash_receipt(did,user)
        total_cash+=d["tien_mat"]
        c=conn()
        c.execute("INSERT OR IGNORE INTO qtgh_session_order(session_id,draft_order_id) VALUES(?,?)",(sid,did))
        c.commit();c.close()

    c=conn()
    c.execute("UPDATE qtgh_session SET status='DA_KHOA',locked_at=?,locked_by=? WHERE id=?",
              (datetime.datetime.now().isoformat(timespec="seconds"),user,sid))
    if total_cash>0:
        c.execute("""INSERT INTO qtgh_cash_receipt(source_type,source_id,ma_nvgh,expected_amount,status,created_at,session_key)
          VALUES('QT_PHIEN',?,?,?,'CHO_THU',?,?)""",
          (sid,ma_nvgh,total_cash,datetime.datetime.now().isoformat(timespec="seconds"),session_key))
    c.commit();c.close()
    return {"session_id":sid,"orders":len(data["rows"]),"cash_expected":total_cash,
            "message":"Đã chốt phiên và lập 1 phiếu thu sang UI05."}

def suggest_delivery_employees(ngay_giao,q=""):
    c=conn(); ensure_schema(c)
    like=f"%{sval(q)}%"
    rows=[r["ma_nvgh"] for r in c.execute("""
      SELECT DISTINCT ma_nvgh
      FROM qtgh_source_projection
      WHERE ngay_giao=? AND COALESCE(ma_nvgh,'')<>'' AND ma_nvgh LIKE ?
      ORDER BY ma_nvgh LIMIT 30
    """,(ngay_giao,like)).fetchall()]
    c.close()
    return {"rows":rows}

def suggest_delivery_lots(ngay_giao,ma_nvgh,q=""):
    c=conn(); ensure_schema(c)
    like=f"%{sval(q)}%"
    rows=[r["ma_lo"] for r in c.execute("""
      SELECT DISTINCT ma_lo
      FROM qtgh_source_projection
      WHERE ngay_giao=? AND ma_nvgh=? AND COALESCE(ma_lo,'')<>'' AND ma_lo LIKE ?
      ORDER BY ma_lo LIMIT 30
    """,(ngay_giao,ma_nvgh,like)).fetchall()]
    c.close()
    return {"rows":rows}

# ===== QTGH V0.6 UI04 employee-centric settlement =====

def ui04_employee_suggestions(q="", ngay_giao=None):
    c=conn(); ensure_schema(c)
    like=f"%{sval(q)}%"
    sql="""SELECT DISTINCT ma_nvgh
           FROM qtgh_source_projection
           WHERE COALESCE(ma_nvgh,'')<>'' AND ma_nvgh LIKE ?"""
    p=[like]
    if ngay_giao:
        sql+=" AND ngay_giao=?"; p.append(ngay_giao)
    sql+=" ORDER BY ma_nvgh LIMIT 30"
    rows=[r["ma_nvgh"] for r in c.execute(sql,p).fetchall()]
    c.close()
    return {"rows":rows}

def ui04_lot_suggestions(ma_nvgh, q="", ngay_giao=None):
    c=conn(); ensure_schema(c)
    like=f"%{sval(q)}%"
    sql="""SELECT DISTINCT ma_lo
           FROM qtgh_source_projection
           WHERE ma_nvgh=? AND COALESCE(ma_lo,'')<>'' AND ma_lo LIKE ?"""
    p=[ma_nvgh,like]
    if ngay_giao:
        sql+=" AND ngay_giao=?"; p.append(ngay_giao)
    sql+=" ORDER BY ma_lo LIMIT 30"
    rows=[r["ma_lo"] for r in c.execute(sql,p).fetchall()]
    c.close()
    return {"rows":rows}

def _draft_is_abnormal(c,did):
    d=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not d: return False
    if d["vo_type"]!="GIAO_DU": return True
    if d["tien_ck_xac_nhan"]>0 or d["cong_no_kh"]>0 or d["so_du_co_su_dung"]>0 or d["can_tru"]>0:
        return True
    lines=c.execute("""SELECT COUNT(*) n FROM qtgh_draft_line
                       WHERE draft_order_id=? AND
                         (CAST(sl_hang_ban_tra AS REAL)>0 OR CAST(sl_hang_km_tra AS REAL)>0
                          OR ck_km_dong_sau<>ck_km_dong_goc)""",(did,)).fetchone()
    if lines and lines["n"]>0: return True
    # order-level discount changed from source originals
    src=c.execute("""SELECT COALESCE(MAX(thuong_tich_luy_goc),0) tl,
                            COALESCE(MAX(thuong_trung_bay_goc),0) tb
                     FROM qtgh_source_projection
                     WHERE source_system=? AND ma_don_nguon=?""",
                  (d["source_system"],d["ma_don_nguon"])).fetchone()
    if src and (d["accumulation_after"]!=src["tl"] or d["display_after"]!=src["tb"] or d["other_order_discount_after"]!=0):
        return True
    return False

def ui04_pending_orders(ma_nvgh, ngay_giao=None, ma_lo=None):
    """
    Employee is required.
    Date and lot are optional.
    Excludes orders already included in a locked QTGH session.
    Unselected orders remain pending and are not mutated.
    """
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn nhân viên giao hàng")

    project_sources()
    c=conn(); ensure_schema(c)

    sql="""SELECT s.source_system,s.loai_don,s.ma_don_nguon,
                  MIN(s.ngay_don) ngay_don,MIN(s.ngay_giao) ngay_giao,
                  MAX(s.ma_nvgh) ma_nvgh,MAX(s.ma_lo) ma_lo,
                  MAX(s.ma_kh_chuan) ma_kh_chuan,MAX(s.ma_kh_mbw) ma_kh_mbw,
                  MAX(s.ma_kh_dms) ma_kh_dms,COUNT(*) so_sku
           FROM qtgh_source_projection s
           WHERE s.ma_nvgh=?"""
    p=[ma_nvgh]
    if ngay_giao:
        sql+=" AND s.ngay_giao=?"; p.append(ngay_giao)
    if ma_lo:
        sql+=" AND s.ma_lo=?"; p.append(ma_lo)
    sql+=" GROUP BY s.source_system,s.loai_don,s.ma_don_nguon ORDER BY ngay_giao,ma_lo,ma_don_nguon"
    src_rows=[dict(r) for r in c.execute(sql,p).fetchall()]

    # Already settled in any locked session.
    settled={(r["source_system"],r["ma_don_nguon"]) for r in c.execute("""
        SELECT d.source_system,d.ma_don_nguon
        FROM qtgh_session_order so
        JOIN qtgh_session se ON se.id=so.session_id
        JOIN qtgh_draft_order d ON d.id=so.draft_order_id
        WHERE se.status='DA_KHOA'
    """).fetchall()}

    c.close()
    out=[]
    for r in src_rows:
        key=(r["source_system"],r["ma_don_nguon"])
        if key in settled:
            continue

        d=create_or_get_draft(r["source_system"],r["ma_don_nguon"])

        c2=conn()
        abnormal=_draft_is_abnormal(c2,d["id"])
        c2.close()

        r.update({
            "draft_id":d["id"],
            "abnormal":abnormal,
            "so_phai_thu":d["so_phai_thu_sau_qt"],
            "tien_mat":d["tien_mat"],
            "tien_ck":d["tien_ck_xac_nhan"],
            "cong_no_kh":d["cong_no_kh"],
            "status_qt":"BAT_THUONG_DA_NHAP" if abnormal else "BINH_THUONG_CHO_QT"
        })
        out.append(r)

    return {"rows":out,"count":len(out)}

def finalize_selected_employee_orders(ma_nvgh, draft_ids, user="pilot", note=""):
    """Lock all selected orders and create their receipt atomically."""
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc nhân viên giao hàng")
    ids=[]
    for x in draft_ids or []:
        try:
            v=int(x)
            if v not in ids: ids.append(v)
        except (TypeError,ValueError):
            continue
    if not ids:
        raise ValueError("Chưa chọn đơn nào để quyết toán")
    c=conn();ensure_schema(c)
    try:
        c.execute("BEGIN IMMEDIATE")
        qs=",".join("?" for _ in ids)
        rows=c.execute(f"""SELECT d.*,MAX(s.ma_nvgh) ma_nvgh,
          MAX(s.ngay_giao) ngay_giao,MAX(s.ma_lo) ma_lo,MAX(s.ma_kh_chuan) ma_kh_chuan
          FROM qtgh_draft_order d JOIN qtgh_source_projection s
          ON s.source_system=d.source_system AND s.ma_don_nguon=d.ma_don_nguon
          WHERE d.id IN ({qs}) GROUP BY d.id""",ids).fetchall()
        if len(rows)!=len(ids):
            raise ValueError("Có đơn không còn tồn tại trong danh sách quyết toán")
        used={x[0] for x in c.execute(f"""SELECT so.draft_order_id FROM qtgh_session_order so
          JOIN qtgh_session se ON se.id=so.session_id
          WHERE se.status='DA_KHOA' AND so.draft_order_id IN ({qs})""",ids)}
        for row in rows:
            if row["ma_nvgh"]!=ma_nvgh:
                raise ValueError("Có đơn không thuộc nhân viên giao hàng đã chọn")
            if row["status"]=="DA_KHOA" or row["id"] in used:
                raise ValueError("Có đơn đã được quyết toán ở phiên trước")
            if row["tien_ck_xac_nhan"]>0 and (not sval(row["bank_txn_id"]) or not sval(row["bank_account"])):
                raise ValueError("QTGH_BANK_001: CK cần tài khoản nhận và mã giao dịch")
        now=datetime.datetime.now().isoformat(timespec="seconds")
        ma_phien="QT-"+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+"-"+ma_nvgh
        sid=c.execute("""INSERT INTO qtgh_session(ma_phien_qt,ngay_giao,ma_nvgh,ma_lo,status,created_at)
          VALUES(?,?,?,'MULTI','NHAP',?)""",(ma_phien,"",ma_nvgh,now)).lastrowid
        total_cash=0;lots=set();days=set()
        for row in rows:
            did=row["id"]
            c.execute("UPDATE qtgh_draft_order SET status='DA_KHOA',locked_at=?,locked_by=? WHERE id=?",(now,user,did))
            if row["cong_no_kh"]>0:
                c.execute("""INSERT INTO qtgh_customer_debt(draft_order_id,ma_kh_chuan,ma_don_nguon,ma_nvgh,original_amount,balance,status,created_at)
                  VALUES(?,?,?,?,?,?,'CON_NO',?)""",(did,row["ma_kh_chuan"],row["ma_don_nguon"],ma_nvgh,row["cong_no_kh"],row["cong_no_kh"],now))
            lines=c.execute("SELECT * FROM qtgh_draft_line WHERE draft_order_id=?",(did,)).fetchall()
            returned=[line for line in lines if D(line["sl_hang_ban_tra"])>0 or D(line["sl_hang_km_tra"])>0]
            if returned:
                nid=c.execute("INSERT INTO qtgh_return_note(draft_order_id,status,created_at) VALUES(?,'CHO_KHO',?)",(did,now)).lastrowid
                for line in returned:
                    c.execute("""INSERT INTO qtgh_return_line(return_note_id,ma_sku,sl_hang_ban_tra,sl_hang_km_tra)
                      VALUES(?,?,?,?)""",(nid,line["ma_sku"],line["sl_hang_ban_tra"],line["sl_hang_km_tra"]))
            c.execute("INSERT INTO qtgh_session_order(session_id,draft_order_id) VALUES(?,?)",(sid,did))
            total_cash+=int(row["tien_mat"] or 0)
            if row["ma_lo"]:lots.add(row["ma_lo"])
            if row["ngay_giao"]:days.add(row["ngay_giao"])
        c.execute("""UPDATE qtgh_session SET status='DA_KHOA',locked_at=?,locked_by=?,ngay_giao=?,ma_lo=? WHERE id=?""",
          (now,user,",".join(sorted(days)),",".join(sorted(lots)) or "MULTI",sid))
        if total_cash>0:
            c.execute("""INSERT INTO qtgh_cash_receipt(source_type,source_id,ma_nvgh,expected_amount,status,created_at,session_key)
              VALUES('QT_PHIEN_NVGH',?,?,?,'CHO_THU',?,?)""",(sid,ma_nvgh,total_cash,now,f"NVGH|{ma_nvgh}|SESSION|{sid}"))
        c.commit()
    except Exception:
        c.rollback();raise
    finally:
        c.close()
    return {"session_id":sid,"orders":len(ids),"lots":sorted(lots),"days":sorted(days),"cash_expected":total_cash,
      "message":"Đã quyết toán các đơn được chọn và lập 1 phiếu thu duy nhất cho NVGH sang UI05."}


# ===== QTGH V0.7 flow alignment =====

def ui02_saved_drafts(ma_nvgh=None, q=""):
    c=conn(); ensure_schema(c)
    term=sval(q)
    like=f"%{term}%"
    sql="""SELECT d.id,d.source_system,d.ma_don_nguon,d.status,d.vo_type,
                  d.so_phai_thu_sau_qt,d.tien_mat,d.tien_ck_xac_nhan,d.cong_no_kh,
                  d.updated_at,
                  MAX(s.ngay_giao) ngay_giao,MAX(s.ma_nvgh) ma_nvgh,MAX(s.ma_lo) ma_lo,
                  MAX(s.ma_kh_mbw) ma_kh_mbw,MAX(s.ma_kh_dms) ma_kh_dms
           FROM qtgh_draft_order d
           JOIN qtgh_source_projection s
             ON s.source_system=d.source_system AND s.ma_don_nguon=d.ma_don_nguon
           WHERE 1=1"""
    p=[]
    if ma_nvgh:
        sql+=" AND s.ma_nvgh=?"; p.append(ma_nvgh)
    if term:
        sql+=" AND (d.ma_don_nguon LIKE ? OR s.ma_kh_mbw LIKE ? OR s.ma_kh_dms LIKE ?)"
        p += [like,like,like]
    sql+=" GROUP BY d.id ORDER BY d.updated_at DESC,d.id DESC"
    rows=[dict(r) for r in c.execute(sql,p).fetchall()]
    c.close()
    return {"rows":rows,"count":len(rows)}

# ===== QTGH V0.8 stable list APIs =====

def qtgh_v08_saved_drafts(ma_nvgh=None):
    c=conn(); ensure_schema(c)
    sql="""
    SELECT
      d.id,d.source_system,d.ma_don_nguon,d.status,d.vo_type,
      d.so_phai_thu_sau_qt,d.tien_mat,d.tien_ck_xac_nhan,d.cong_no_kh,
      MAX(s.ngay_giao) AS ngay_giao,
      MAX(s.ma_nvgh) AS ma_nvgh,
      MAX(s.ma_lo) AS ma_lo,
      MAX(s.ma_kh_mbw) AS ma_kh_mbw,
      MAX(s.ma_kh_dms) AS ma_kh_dms
    FROM qtgh_draft_order d
    JOIN qtgh_source_projection s
      ON s.source_system=d.source_system
     AND s.ma_don_nguon=d.ma_don_nguon
    WHERE 1=1
    """
    p=[]
    if ma_nvgh:
        sql+=" AND s.ma_nvgh=?"
        p.append(ma_nvgh)
    sql+=" GROUP BY d.id ORDER BY d.id DESC"
    rows=[dict(r) for r in c.execute(sql,p).fetchall()]
    c.close()
    return {"rows":rows,"count":len(rows)}

def qtgh_v08_pending_orders(ma_nvgh,ngay_giao=None,ma_lo=None):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    project_sources()
    c=conn(); ensure_schema(c)

    sql="""
    SELECT
      s.source_system,s.loai_don,s.ma_don_nguon,
      MIN(s.ngay_don) AS ngay_don,
      MIN(s.ngay_giao) AS ngay_giao,
      MAX(s.ma_nvgh) AS ma_nvgh,
      MAX(s.ma_lo) AS ma_lo,
      MAX(s.ma_kh_chuan) AS ma_kh_chuan,
      MAX(s.ma_kh_mbw) AS ma_kh_mbw,
      MAX(s.ma_kh_dms) AS ma_kh_dms,
      COUNT(*) AS so_sku
    FROM qtgh_source_projection s
    WHERE s.ma_nvgh=?
    """
    p=[ma_nvgh]
    if ngay_giao:
        sql+=" AND s.ngay_giao=?"
        p.append(ngay_giao)
    if ma_lo:
        sql+=" AND s.ma_lo=?"
        p.append(ma_lo)

    sql+=" GROUP BY s.source_system,s.loai_don,s.ma_don_nguon ORDER BY ngay_giao,ma_lo,ma_don_nguon"
    source_rows=[dict(r) for r in c.execute(sql,p).fetchall()]

    # Orders already included in a locked settlement session are excluded.
    settled=set()
    try:
        for r in c.execute("""
          SELECT d.source_system,d.ma_don_nguon
          FROM qtgh_session_order so
          JOIN qtgh_session se ON se.id=so.session_id
          JOIN qtgh_draft_order d ON d.id=so.draft_order_id
          WHERE se.status='DA_KHOA'
        """).fetchall():
            settled.add((r["source_system"],r["ma_don_nguon"]))
    except Exception:
        settled=set()
    c.close()

    out=[]
    for r in source_rows:
        key=(r["source_system"],r["ma_don_nguon"])
        if key in settled:
            continue

        d=create_or_get_draft(r["source_system"],r["ma_don_nguon"])

        abnormal=False
        try:
            if str(d.get("vo_type","GIAO_DU"))!="GIAO_DU":
                abnormal=True
            if float(d.get("tien_ck_xac_nhan",0) or 0)>0:
                abnormal=True
            if float(d.get("cong_no_kh",0) or 0)>0:
                abnormal=True
            for ln in d.get("lines",[]):
                if float(ln.get("sl_hang_ban_tra",0) or 0)>0 or float(ln.get("sl_hang_km_tra",0) or 0)>0:
                    abnormal=True
                    break
        except Exception:
            pass

        r.update({
          "draft_id":d["id"],
          "abnormal":abnormal,
          "so_phai_thu":d.get("so_phai_thu_sau_qt",0),
          "tien_mat":d.get("tien_mat",0),
          "tien_ck":d.get("tien_ck_xac_nhan",0),
          "cong_no_kh":d.get("cong_no_kh",0),
          "status_qt":"BAT_THUONG_DA_NHAP" if abnormal else "BINH_THUONG_CHO_QT"
        })
        out.append(r)

    return {"rows":out,"count":len(out)}

# ===== QTGH V0.8.2 UI04 read-only list / write-on-finalize =====

def qtgh_v082_pending_orders_readonly(ma_nvgh, ngay_giao=None, ma_lo=None):
    """
    UI04 search must be READ ONLY.
    Existing abnormal drafts are reused for display.
    Normal orders without drafts are calculated directly from projection,
    without creating qtgh_draft_order rows.
    """
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    c=conn()
    try:
        c.execute("PRAGMA busy_timeout=5000")
    except Exception:
        pass
    ensure_schema(c)

    sql="""
    SELECT
      s.source_system,s.loai_don,s.ma_don_nguon,
      MIN(s.ngay_don) AS ngay_don,
      MIN(s.ngay_giao) AS ngay_giao,
      MAX(s.ma_nvgh) AS ma_nvgh,
      MAX(s.ma_lo) AS ma_lo,
      MAX(s.ma_kh_chuan) AS ma_kh_chuan,
      MAX(s.ma_kh_mbw) AS ma_kh_mbw,
      MAX(s.ma_kh_dms) AS ma_kh_dms,
      COUNT(*) AS so_sku,
      SUM(
        CAST(s.sl_hang_ban_dat AS REAL) * CAST(s.don_gia_co_vat AS REAL)
        - CAST(s.ck_km_dong_goc AS REAL)
      ) AS tien_sau_ck_dong,
      MAX(CAST(s.thuong_tich_luy_goc AS REAL)) AS tl_goc,
      MAX(CAST(s.thuong_trung_bay_goc AS REAL)) AS tb_goc
    FROM qtgh_source_projection s
    WHERE s.ma_nvgh=?
    """
    p=[ma_nvgh]
    if ngay_giao:
        sql+=" AND s.ngay_giao=?"
        p.append(ngay_giao)
    if ma_lo:
        sql+=" AND s.ma_lo=?"
        p.append(ma_lo)
    sql+=" GROUP BY s.source_system,s.loai_don,s.ma_don_nguon ORDER BY ngay_giao,ma_lo,ma_don_nguon"

    source_rows=[dict(r) for r in c.execute(sql,p).fetchall()]

    settled=set()
    try:
        for r in c.execute("""
          SELECT d.source_system,d.ma_don_nguon
          FROM qtgh_session_order so
          JOIN qtgh_session se ON se.id=so.session_id
          JOIN qtgh_draft_order d ON d.id=so.draft_order_id
          WHERE se.status='DA_KHOA'
        """).fetchall():
            settled.add((r["source_system"],r["ma_don_nguon"]))
    except Exception:
        pass

    draft_map={}
    for r in c.execute("""
      SELECT id,source_system,ma_don_nguon,status,vo_type,
             so_phai_thu_sau_qt,tien_mat,tien_ck_xac_nhan,cong_no_kh
      FROM qtgh_draft_order
    """).fetchall():
        draft_map[(r["source_system"],r["ma_don_nguon"])]=dict(r)

    c.close()

    out=[]
    for r in source_rows:
        key=(r["source_system"],r["ma_don_nguon"])
        if key in settled:
            continue

        d=draft_map.get(key)
        if d:
            abnormal=(
                str(d.get("vo_type") or "GIAO_DU")!="GIAO_DU"
                or float(d.get("tien_ck_xac_nhan") or 0)>0
                or float(d.get("cong_no_kh") or 0)>0
            )
            r.update({
              "draft_id":d["id"],
              "selection_key":f'{r["source_system"]}|{r["ma_don_nguon"]}',
              "abnormal":abnormal,
              "so_phai_thu":d.get("so_phai_thu_sau_qt",0),
              "tien_mat":d.get("tien_mat",0),
              "tien_ck":d.get("tien_ck_xac_nhan",0),
              "cong_no_kh":d.get("cong_no_kh",0),
              "status_qt":"BAT_THUONG_DA_NHAP" if abnormal else "NHAP_CHO_QT"
            })
        else:
            # Normal order: delivery 100%, cash 100%.
            due=round(
                float(r.get("tien_sau_ck_dong") or 0)
                - float(r.get("tl_goc") or 0)
                - float(r.get("tb_goc") or 0)
            )
            if due < 0: due=0
            r.update({
              "draft_id":None,
              "selection_key":f'{r["source_system"]}|{r["ma_don_nguon"]}',
              "abnormal":False,
              "so_phai_thu":due,
              "tien_mat":due,
              "tien_ck":0,
              "cong_no_kh":0,
              "status_qt":"BINH_THUONG_CHO_QT"
            })
        out.append(r)

    return {"rows":out,"count":len(out)}

def qtgh_v082_finalize_selected(ma_nvgh, items, user="pilot"):
    """
    Create drafts only here, after the accountant explicitly selects orders.
    One employee -> one settlement session / one cash receipt even across lots.
    """
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc NVGH")
    if not items:
        raise ValueError("Chưa chọn đơn nào")

    draft_ids=[]
    seen=set()
    for item in items:
        src=sval(item.get("source_system"))
        ono=sval(item.get("ma_don_nguon"))
        if not src or not ono:
            continue
        key=(src,ono)
        if key in seen:
            continue
        seen.add(key)

        # Validate that this source order actually belongs to selected employee.
        c=conn()
        try:c.execute("PRAGMA busy_timeout=5000")
        except Exception:pass
        row=c.execute("""
          SELECT MAX(ma_nvgh) ma_nvgh
          FROM qtgh_source_projection
          WHERE source_system=? AND ma_don_nguon=?
        """,(src,ono)).fetchone()
        c.close()
        if not row or row["ma_nvgh"]!=ma_nvgh:
            raise ValueError(f"Đơn {ono} không thuộc NVGH {ma_nvgh}")

        d=create_or_get_draft(src,ono)
        draft_ids.append(d["id"])

    if not draft_ids:
        raise ValueError("Không có đơn hợp lệ để quyết toán")

    return finalize_selected_employee_orders(ma_nvgh,draft_ids,user=user)

# ===== QTGH V0.8.4 UI05 Treasurer workflow =====

def qtgh_v084_ensure_cash_schema(c):
    # Extend cash receipt without breaking old rows.
    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_cash_receipt)").fetchall()}
    adds=[
      ("receipt_kind","TEXT"),
      ("variance_amount","INTEGER"),
      ("resolution_code","TEXT"),
      ("resolution_note","TEXT"),
      ("received_at","TEXT"),
      ("received_by","TEXT")
    ]
    for name,ddl in adds:
        if name not in cols:
            c.execute(f"ALTER TABLE qtgh_cash_receipt ADD COLUMN {name} {ddl}")

    # Canonical employee debt table if old module has not created it yet.
    c.execute("""
    CREATE TABLE IF NOT EXISTS qtgh_employee_debt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_type TEXT,
      source_id INTEGER,
      ma_nvgh TEXT,
      original_amount INTEGER NOT NULL DEFAULT 0,
      collected_amount INTEGER NOT NULL DEFAULT 0,
      balance INTEGER NOT NULL DEFAULT 0,
      resolution_code TEXT,
      status TEXT NOT NULL DEFAULT 'CON_NO',
      created_at TEXT,
      updated_at TEXT
    )
    """)
    c.commit()

def qtgh_v084_cash_list():
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except Exception:pass
    ensure_schema(c)
    qtgh_v084_ensure_cash_schema(c)

    rows=[dict(r) for r in c.execute("""
      SELECT id,
             COALESCE(receipt_kind,source_type) receipt_kind,
             source_type,source_id,ma_nvgh,
             expected_amount,
             COALESCE(actual_amount,0) actual_amount,
             COALESCE(variance_amount,expected_amount-COALESCE(actual_amount,0)) variance_amount,
             resolution_code,resolution_note,status,
             created_at,received_at
      FROM qtgh_cash_receipt
      ORDER BY id DESC
    """).fetchall()]
    c.close()
    return {"rows":rows,"count":len(rows)}

def qtgh_v084_cash_detail(rid):
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except Exception:pass
    ensure_schema(c)
    qtgh_v084_ensure_cash_schema(c)

    r=c.execute("""
      SELECT id,
             COALESCE(receipt_kind,source_type) receipt_kind,
             source_type,source_id,ma_nvgh,
             expected_amount,
             COALESCE(actual_amount,0) actual_amount,
             COALESCE(variance_amount,expected_amount-COALESCE(actual_amount,0)) variance_amount,
             resolution_code,resolution_note,status,
             created_at,received_at,received_by
      FROM qtgh_cash_receipt WHERE id=?
    """,(rid,)).fetchone()
    c.close()
    if not r: raise ValueError("Không tìm thấy phiếu thu")
    return dict(r)

def _qtgh_v084_insert_employee_debt(c, rid, ma_nvgh, shortage, resolution_code, now):
    # Avoid duplicate debt if the same receipt is retried.
    try:
        ex=c.execute("""
          SELECT id FROM qtgh_employee_debt
          WHERE source_type='THIEU_NOP_UI05' AND source_id=?
          LIMIT 1
        """,(rid,)).fetchone()
        if ex:
            return ex["id"]
    except Exception:
        pass

    cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_employee_debt)").fetchall()}
    values={
      "source_type":"THIEU_NOP_UI05",
      "source_id":rid,
      "ma_nvgh":ma_nvgh,
      "original_amount":shortage,
      "collected_amount":0,
      "balance":shortage,
      "resolution_code":resolution_code,
      "status":"CON_NO",
      "created_at":now,
      "updated_at":now
    }
    use=[k for k in values if k in cols]
    if not use:
        raise ValueError("Không thể ghi công nợ NVGH")
    marks=",".join("?" for _ in use)
    cur=c.execute(
      f"INSERT INTO qtgh_employee_debt({','.join(use)}) VALUES({marks})",
      [values[k] for k in use]
    )
    return cur.lastrowid

def qtgh_v084_receive_cash(rid, actual_amount, resolution_code=None, resolution_note="", user="THU_QUY"):
    try:
        actual=int(round(float(actual_amount)))
    except Exception:
        raise ValueError("Tiền thực nộp không hợp lệ")
    if actual < 0:
        raise ValueError("Tiền thực nộp không được âm")

    allowed={"NOP_SAU","TRU_LUONG","XIN_Y_KIEN_LANH_DAO"}

    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except Exception:pass
    ensure_schema(c)
    qtgh_v084_ensure_cash_schema(c)

    try:
        c.execute("BEGIN IMMEDIATE")
        r=c.execute("SELECT * FROM qtgh_cash_receipt WHERE id=?",(rid,)).fetchone()
        if not r:
            raise ValueError("Không tìm thấy phiếu thu")

        if str(r["status"] or "") not in ("CHO_THU","NHAP",""):
            raise ValueError("Phiếu thu đã được xử lý")

        expected=int(r["expected_amount"] or 0)

        if actual > expected:
            raise ValueError(
              f"Không cho phép nộp thừa. Phải thu {expected:,}; thực nộp {actual:,}; "
              f"thừa {actual-expected:,}. Chuyển kế toán kiểm tra lại quyết toán tại bàn."
            )

        shortage=expected-actual
        resolution=(resolution_code or "").strip().upper()

        if shortage > 0 and resolution not in allowed:
            raise ValueError(
              "Nộp thiếu bắt buộc chọn Hướng giải quyết: "
              "Nộp sau / Trừ lương / Xin ý kiến lãnh đạo."
            )

        now=datetime.datetime.now().isoformat(timespec="seconds")
        new_status="DA_THU_DU" if shortage==0 else "DA_THU_THIEU"

        c.execute("""
          UPDATE qtgh_cash_receipt
          SET actual_amount=?,
              variance_amount=?,
              resolution_code=?,
              resolution_note=?,
              status=?,
              received_at=?,
              received_by=?,
              receipt_kind=COALESCE(receipt_kind,source_type)
          WHERE id=?
        """,(actual,shortage,resolution if shortage>0 else None,
             sval(resolution_note),new_status,now,user,rid))

        debt_id=None
        if shortage>0:
            debt_id=_qtgh_v084_insert_employee_debt(
              c,rid,sval(r["ma_nvgh"]),shortage,resolution,now
            )

        c.commit()
    except Exception:
        c.rollback()
        c.close()
        raise

    c.close()
    return {
      "id":rid,
      "expected_amount":expected,
      "actual_amount":actual,
      "shortage":shortage,
      "status":new_status,
      "employee_debt_id":debt_id,
      "message":"Đã thu đủ." if shortage==0
                else "Đã ghi nhận nộp thiếu và chuyển phần thiếu sang công nợ NVGH."
    }

# ===== QTGH V0.8.5 UI05 debt-schema + money-format compatibility =====

def qtgh_v085_parse_money(value):
    if value is None:
        return 0
    if isinstance(value,bool):
        raise ValueError("Số tiền không hợp lệ")
    if isinstance(value,(int,float)):
        number=Decimal(str(value))
        if not number.is_finite() or number<0:
            raise ValueError("Số tiền không hợp lệ hoặc âm")
        return int(number.quantize(Decimal("1"),rounding=ROUND_HALF_UP))
    s=str(value).strip()
    if not s:
        return 0
    # UI uses vi-VN thousands separators. Keep digits and optional leading minus.
    import re
    if not re.fullmatch(r"-?[0-9]+(?:[., ][0-9]+)*",s):
        raise ValueError("Số tiền không hợp lệ")
    neg=s.startswith("-")
    digits="".join(ch for ch in s if ch.isdigit())
    if not digits:
        raise ValueError("Số tiền không hợp lệ")
    n=int(digits)
    return -n if neg else n

def _qtgh_v085_insert_employee_debt(c, rid, ma_nvgh, shortage, resolution_code, now):
    """
    Compatible with both old and new qtgh_employee_debt schemas.
    In particular, existing Pilot DB requires cash_receipt_id NOT NULL.
    """
    cols={r["name"]:dict(r) for r in c.execute("PRAGMA table_info(qtgh_employee_debt)").fetchall()}

    # Duplicate guard using whichever receipt-link column exists.
    if "cash_receipt_id" in cols:
        ex=c.execute("SELECT id FROM qtgh_employee_debt WHERE cash_receipt_id=? LIMIT 1",(rid,)).fetchone()
        if ex:return ex["id"]
    elif "source_id" in cols:
        ex=c.execute("""
          SELECT id FROM qtgh_employee_debt
          WHERE source_type='THIEU_NOP_UI05' AND source_id=? LIMIT 1
        """,(rid,)).fetchone()
        if ex:return ex["id"]

    values={
      "cash_receipt_id":rid,
      "source_type":"THIEU_NOP_UI05",
      "source_id":rid,
      "ma_nvgh":ma_nvgh,
      "original_amount":shortage,
      "amount":shortage,
      "debt_amount":shortage,
      "collected_amount":0,
      "balance":shortage,
      "remaining_amount":shortage,
      "resolution_code":resolution_code,
      "resolution":resolution_code,
      "status":"CON_NO",
      "created_at":now,
      "updated_at":now
    }

    use=[]
    vals=[]
    for name in cols:
        if name=="id":
            continue
        if name in values:
            use.append(name); vals.append(values[name])
        else:
            col=cols[name]
            # Satisfy other NOT NULL legacy columns if needed.
            if int(col.get("notnull",0))==1 and col.get("dflt_value") is None:
                typ=str(col.get("type") or "").upper()
                if "INT" in typ or "REAL" in typ or "NUM" in typ:
                    use.append(name); vals.append(0)
                else:
                    use.append(name); vals.append("")

    marks=",".join("?" for _ in use)
    cur=c.execute(f"INSERT INTO qtgh_employee_debt({','.join(use)}) VALUES({marks})",vals)
    return cur.lastrowid

def qtgh_v085_receive_cash(rid, actual_amount, resolution_code=None, resolution_note="", user="THU_QUY"):
    actual=qtgh_v085_parse_money(actual_amount)
    if actual < 0:
        raise ValueError("Tiền thực nộp không được âm")

    allowed={"NOP_SAU","TRU_LUONG","XIN_Y_KIEN_LANH_DAO"}

    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except Exception:pass
    ensure_schema(c)
    qtgh_v084_ensure_cash_schema(c)

    try:
        c.execute("BEGIN IMMEDIATE")
        r=c.execute("SELECT * FROM qtgh_cash_receipt WHERE id=?",(rid,)).fetchone()
        if not r:
            raise ValueError("Không tìm thấy phiếu thu")

        if str(r["status"] or "") not in ("CHO_THU","NHAP",""):
            raise ValueError("Phiếu thu đã được xử lý")

        expected=int(r["expected_amount"] or 0)

        if actual > expected:
            raise ValueError(
              f"Không cho phép nộp thừa. Phải thu {expected:,}; thực nộp {actual:,}; "
              f"thừa {actual-expected:,}. Chuyển kế toán kiểm tra lại quyết toán tại bàn."
            )

        shortage=expected-actual
        resolution=(resolution_code or "").strip().upper()

        if shortage > 0 and resolution not in allowed:
            raise ValueError(
              "Nộp thiếu bắt buộc chọn Hướng giải quyết: "
              "Nộp sau / Trừ lương / Xin ý kiến lãnh đạo."
            )

        now=datetime.datetime.now().isoformat(timespec="seconds")
        new_status="DA_THU_DU" if shortage==0 else "DA_THU_THIEU"

        c.execute("""
          UPDATE qtgh_cash_receipt
          SET actual_amount=?,
              variance_amount=?,
              resolution_code=?,
              resolution_note=?,
              status=?,
              received_at=?,
              received_by=?,
              receipt_kind=COALESCE(receipt_kind,source_type)
          WHERE id=?
        """,(actual,shortage,resolution if shortage>0 else None,
             sval(resolution_note),new_status,now,user,rid))

        debt_id=None
        if shortage>0:
            debt_id=_qtgh_v085_insert_employee_debt(
              c,rid,sval(r["ma_nvgh"]),shortage,resolution,now
            )

        c.commit()
    except Exception:
        c.rollback()
        c.close()
        raise

    c.close()
    return {
      "id":rid,
      "expected_amount":expected,
      "actual_amount":actual,
      "shortage":shortage,
      "status":new_status,
      "employee_debt_id":debt_id,
      "message":"Đã thu đủ." if shortage==0
                else "Đã ghi nhận nộp thiếu và chuyển phần thiếu sang công nợ NVGH."
    }

# ===== QTGH V0.9 CUSTOMER DEBT COLLECTION =====

def _v09_money(v):
    try:
        if v is None: return 0
        if isinstance(v,(int,float)): return int(round(float(v)))
        s="".join(ch for ch in str(v) if ch.isdigit() or ch=="-")
        return int(s or 0)
    except:
        return 0

def _v09_customer_debt_rows(ma_nvgh=None, customer_code=None):
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    ensure_schema(c)

    try:
        debt_cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_customer_debt)").fetchall()}
    except:
        c.close()
        return []

    rows=[]
    for r0 in c.execute("SELECT * FROM qtgh_customer_debt ORDER BY id").fetchall():
        r=dict(r0)

        original=_v09_money(r.get("original_amount",r.get("amount",0)))
        collected=_v09_money(r.get("collected_amount",0))
        balance=_v09_money(r.get("balance",r.get("remaining_amount",original-collected)))
        if balance<=0:
            continue

        order=sval(r.get("ma_don_nguon"))
        src=""
        did=r.get("draft_order_id")
        if did:
            d=c.execute("SELECT source_system,ma_don_nguon FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
            if d:
                src=sval(d["source_system"])
                order=sval(d["ma_don_nguon"])

        if not order:
            continue

        p=c.execute("""
          SELECT MAX(ma_nvgh) ma_nvgh,
                 MAX(ma_kh_chuan) ma_kh_chuan,
                 MAX(ma_kh_dms) ma_kh_dms,
                 MAX(ma_kh_mbw) ma_kh_mbw,
                 MIN(ngay_don) ngay_don,
                 MIN(ngay_giao) ngay_giao
          FROM qtgh_source_projection
          WHERE ma_don_nguon=?
        """,(order,)).fetchone()

        nv=sval((p and p["ma_nvgh"]) or r.get("ma_nvgh"))
        if ma_nvgh and nv!=ma_nvgh:
            continue

        dms=sval(p["ma_kh_dms"] if p else "")
        mbw=sval(p["ma_kh_mbw"] if p else "")
        chuan=sval((p and p["ma_kh_chuan"]) or r.get("ma_kh_chuan"))

        if customer_code:
            cc=sval(customer_code).upper()
            if cc not in (dms.upper(),mbw.upper(),chuan.upper()):
                continue

        rows.append({
          "debt_id":r["id"],
          "draft_order_id":did,
          "source_system":src,
          "ma_don_nguon":order,
          "ngay_don":sval(p["ngay_don"] if p else r.get("created_at")),
          "ngay_giao":sval(p["ngay_giao"] if p else ""),
          "ma_nvgh":nv,
          "ma_kh_chuan":chuan,
          "ma_kh_dms":dms,
          "ma_kh_mbw":mbw,
          "original_amount":original,
          "collected_amount":collected,
          "balance":balance,
          "created_at":sval(r.get("created_at"))
        })
    c.close()

    rows.sort(key=lambda x:(x["ngay_don"] or "9999-99-99",x["created_at"] or "",x["debt_id"]))
    return rows

def qtgh_v09_ui07_debts(ma_nvgh):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")
    rows=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    return {"rows":rows,"count":len(rows),"total_balance":sum(r["balance"] for r in rows)}

def qtgh_v09_customer_debts(ma_nvgh,customer_code):
    if not sval(ma_nvgh): raise ValueError("Bắt buộc NVGH")
    if not sval(customer_code): raise ValueError("Bắt buộc mã khách hàng DMS/MBW")
    rows=_v09_customer_debt_rows(ma_nvgh=ma_nvgh,customer_code=customer_code)
    if not rows:
        raise ValueError("Không tìm thấy công nợ của khách hàng này thuộc NVGH đã chọn")
    return {"rows":rows,"count":len(rows),"total_balance":sum(r["balance"] for r in rows)}

def qtgh_v09_ensure_tables(c):
    c.execute("""
    CREATE TABLE IF NOT EXISTS qtgh_debt_collect_batch(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ma_nvgh TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'OPEN',
      cash_total INTEGER NOT NULL DEFAULT 0,
      bank_total INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      cash_receipt_id INTEGER,
      created_at TEXT,
      finalized_at TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS qtgh_debt_collect_customer(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id INTEGER NOT NULL,
      customer_code TEXT NOT NULL,
      ma_kh_dms TEXT,
      ma_kh_mbw TEXT,
      cash_amount INTEGER NOT NULL DEFAULT 0,
      bank_amount INTEGER NOT NULL DEFAULT 0,
      bank_account TEXT,
      bank_txn_id TEXT,
      total_amount INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'DRAFT',
      created_at TEXT,
      FOREIGN KEY(batch_id) REFERENCES qtgh_debt_collect_batch(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS qtgh_debt_collect_allocation(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_collect_id INTEGER NOT NULL,
      customer_debt_id INTEGER NOT NULL,
      ma_don_nguon TEXT,
      allocated_amount INTEGER NOT NULL DEFAULT 0,
      allocation_order INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(customer_collect_id) REFERENCES qtgh_debt_collect_customer(id)
    )""")
    c.commit()

def qtgh_v09_get_open_batch(ma_nvgh,create=False):
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    qtgh_v09_ensure_tables(c)
    b=c.execute("""
      SELECT * FROM qtgh_debt_collect_batch
      WHERE ma_nvgh=? AND status='OPEN'
      ORDER BY id DESC LIMIT 1
    """,(ma_nvgh,)).fetchone()
    if not b and create:
        now=datetime.datetime.now().isoformat(timespec="seconds")
        cur=c.execute("""
          INSERT INTO qtgh_debt_collect_batch(ma_nvgh,status,created_at)
          VALUES(?,'OPEN',?)
        """,(ma_nvgh,now))
        c.commit()
        b=c.execute("SELECT * FROM qtgh_debt_collect_batch WHERE id=?",(cur.lastrowid,)).fetchone()
    result=dict(b) if b else None
    c.close()
    return result

def qtgh_v09_preview_allocation(ma_nvgh,customer_code,cash_amount,bank_amount):
    cash=_v09_money(cash_amount)
    bank=_v09_money(bank_amount)
    if cash<0 or bank<0: raise ValueError("Số tiền không được âm")
    total=cash+bank
    if total<=0: raise ValueError("Số tiền thực thu phải lớn hơn 0")

    rows=qtgh_v09_customer_debts(ma_nvgh,customer_code)["rows"]
    total_debt=sum(r["balance"] for r in rows)
    if total>total_debt:
        raise ValueError(f"Số tiền thu {total:,} vượt tổng công nợ KH {total_debt:,}")

    remain=total
    alloc=[]
    for r in rows:
        if remain<=0: break
        amt=min(remain,r["balance"])
        alloc.append({
          "customer_debt_id":r["debt_id"],
          "ma_don_nguon":r["ma_don_nguon"],
          "ngay_don":r["ngay_don"],
          "balance_before":r["balance"],
          "allocated_amount":amt,
          "balance_after":r["balance"]-amt
        })
        remain-=amt
    return {
      "cash_amount":cash,"bank_amount":bank,"total_amount":total,
      "allocations":alloc,"unallocated":remain
    }

def qtgh_v09_add_customer_to_batch(ma_nvgh,customer_code,cash_amount,bank_amount,bank_account="",bank_txn_id=""):
    cash=_v09_money(cash_amount)
    bank=_v09_money(bank_amount)

    if bank>0 and (not sval(bank_account) or not sval(bank_txn_id)):
        raise ValueError("Có tiền chuyển khoản: bắt buộc chọn tài khoản nhận và nhập mã giao dịch CK")

    preview=qtgh_v09_preview_allocation(ma_nvgh,customer_code,cash,bank)
    debts=qtgh_v09_customer_debts(ma_nvgh,customer_code)["rows"]
    first=debts[0]

    batch=qtgh_v09_get_open_batch(ma_nvgh,create=True)
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    qtgh_v09_ensure_tables(c)

    # One customer once per open batch to prevent accidental duplicate allocation.
    ex=c.execute("""
      SELECT id FROM qtgh_debt_collect_customer
      WHERE batch_id=? AND customer_code=? AND status='DRAFT'
      LIMIT 1
    """,(batch["id"],sval(customer_code))).fetchone()
    if ex:
        c.close()
        raise ValueError("Khách hàng này đã có trong phiên thu nợ hiện tại")

    now=datetime.datetime.now().isoformat(timespec="seconds")
    cur=c.execute("""
      INSERT INTO qtgh_debt_collect_customer(
        batch_id,customer_code,ma_kh_dms,ma_kh_mbw,
        cash_amount,bank_amount,bank_account,bank_txn_id,total_amount,status,created_at
      ) VALUES(?,?,?,?,?,?,?,?,?,'DRAFT',?)
    """,(batch["id"],sval(customer_code),first["ma_kh_dms"],first["ma_kh_mbw"],
         cash,bank,sval(bank_account),sval(bank_txn_id),cash+bank,now))
    cid=cur.lastrowid

    for i,a in enumerate(preview["allocations"],1):
        c.execute("""
          INSERT INTO qtgh_debt_collect_allocation(
            customer_collect_id,customer_debt_id,ma_don_nguon,allocated_amount,allocation_order
          ) VALUES(?,?,?,?,?)
        """,(cid,a["customer_debt_id"],a["ma_don_nguon"],a["allocated_amount"],i))

    c.execute("""
      UPDATE qtgh_debt_collect_batch
      SET cash_total=(SELECT COALESCE(SUM(cash_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT'),
          bank_total=(SELECT COALESCE(SUM(bank_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT'),
          total_amount=(SELECT COALESCE(SUM(total_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT')
      WHERE id=?
    """,(batch["id"],batch["id"],batch["id"],batch["id"]))
    c.commit()
    c.close()
    return qtgh_v09_batch_detail(batch["id"])

def qtgh_v09_batch_detail(batch_id):
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    qtgh_v09_ensure_tables(c)
    b=c.execute("SELECT * FROM qtgh_debt_collect_batch WHERE id=?",(batch_id,)).fetchone()
    if not b:
        c.close(); raise ValueError("Không tìm thấy phiên thu nợ")
    customers=[]
    for r in c.execute("""
      SELECT * FROM qtgh_debt_collect_customer
      WHERE batch_id=? ORDER BY id
    """,(batch_id,)).fetchall():
        d=dict(r)
        d["allocations"]=[dict(a) for a in c.execute("""
          SELECT * FROM qtgh_debt_collect_allocation
          WHERE customer_collect_id=? ORDER BY allocation_order,id
        """,(r["id"],)).fetchall()]
        customers.append(d)
    out=dict(b);out["customers"]=customers
    c.close()
    return out

def qtgh_v09_open_batch_detail(ma_nvgh):
    b=qtgh_v09_get_open_batch(ma_nvgh,create=False)
    if not b:
        return {"batch":None}
    return {"batch":qtgh_v09_batch_detail(b["id"])}

def _v09_apply_customer_debt_allocation(c,debt_id,amount):
    row=c.execute("SELECT * FROM qtgh_customer_debt WHERE id=?",(debt_id,)).fetchone()
    if not row: raise ValueError("Không tìm thấy dòng công nợ KH")
    r=dict(row)
    cols={x["name"] for x in c.execute("PRAGMA table_info(qtgh_customer_debt)").fetchall()}

    original=_v09_money(r.get("original_amount",r.get("amount",0)))
    collected=_v09_money(r.get("collected_amount",0))
    balance=_v09_money(r.get("balance",r.get("remaining_amount",original-collected)))

    if amount>balance:
        raise ValueError("Phân bổ vượt số dư công nợ")

    new_collected=collected+amount
    new_balance=balance-amount

    sets=[];vals=[]
    if "collected_amount" in cols:
        sets.append("collected_amount=?");vals.append(new_collected)
    if "balance" in cols:
        sets.append("balance=?");vals.append(new_balance)
    if "remaining_amount" in cols:
        sets.append("remaining_amount=?");vals.append(new_balance)
    if "status" in cols:
        sets.append("status=?");vals.append("DA_THU" if new_balance==0 else "CON_NO")
    if "updated_at" in cols:
        sets.append("updated_at=?");vals.append(datetime.datetime.now().isoformat(timespec="seconds"))
    vals.append(debt_id)
    c.execute(f"UPDATE qtgh_customer_debt SET {','.join(sets)} WHERE id=?",vals)

def qtgh_v09_finalize_batch(batch_id,user="KE_TOAN"):
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    ensure_schema(c)
    qtgh_v09_ensure_tables(c)
    qtgh_v084_ensure_cash_schema(c)

    try:
        c.execute("BEGIN IMMEDIATE")
        b=c.execute("SELECT * FROM qtgh_debt_collect_batch WHERE id=?",(batch_id,)).fetchone()
        if not b: raise ValueError("Không tìm thấy phiên thu nợ")
        if b["status"]!="OPEN": raise ValueError("Phiên thu nợ đã được chốt")

        custs=c.execute("""
          SELECT * FROM qtgh_debt_collect_customer
          WHERE batch_id=? AND status='DRAFT'
          ORDER BY id
        """,(batch_id,)).fetchall()
        if not custs: raise ValueError("Phiên chưa có khách hàng thu nợ")

        for cust in custs:
            allocs=c.execute("""
              SELECT * FROM qtgh_debt_collect_allocation
              WHERE customer_collect_id=?
              ORDER BY allocation_order,id
            """,(cust["id"],)).fetchall()
            for a in allocs:
                _v09_apply_customer_debt_allocation(c,a["customer_debt_id"],a["allocated_amount"])
            c.execute("UPDATE qtgh_debt_collect_customer SET status='FINALIZED' WHERE id=?",(cust["id"],))

        cash_total=int(b["cash_total"] or 0)
        receipt_id=None
        now=datetime.datetime.now().isoformat(timespec="seconds")
        if cash_total>0:
            cur=c.execute("""
              INSERT INTO qtgh_cash_receipt(
                source_type,source_id,ma_nvgh,expected_amount,actual_amount,
                status,created_at,receipt_kind,variance_amount,session_key
              ) VALUES('THU_NO_KH',?,?,?,0,'CHO_THU',?,'THU_NO_KH',?,?)
            """,(batch_id,b["ma_nvgh"],cash_total,now,cash_total,
                 f"THU_NO_KH|{b['ma_nvgh']}|BATCH|{batch_id}"))
            receipt_id=cur.lastrowid

        c.execute("""
          UPDATE qtgh_debt_collect_batch
          SET status='FINALIZED',cash_receipt_id=?,finalized_at=?
          WHERE id=?
        """,(receipt_id,now,batch_id))
        c.commit()
    except Exception:
        c.rollback();c.close();raise

    c.close()
    return {
      "batch_id":batch_id,
      "cash_receipt_id":receipt_id,
      "cash_total":int(b["cash_total"] or 0),
      "bank_total":int(b["bank_total"] or 0),
      "total_amount":int(b["total_amount"] or 0),
      "message":"Đã chốt thu nợ KH. Phần tiền mặt đã lập 1 phiếu thu sang UI05."
    }

# ===== QTGH V0.9.1 UI07 grouped by customer =====

def _v091_customer_name_lookup(c, ma_kh_chuan="", ma_kh_dms="", ma_kh_mbw=""):
    """
    Best-effort lookup from current Mini App master tables.
    Returns blank if customer name is not present in DB.
    """
    codes=[x for x in [sval(ma_kh_chuan),sval(ma_kh_dms),sval(ma_kh_mbw)] if x]
    if not codes:
        return ""

    name_candidates=["TEN_KH","TEN_KHACH_HANG","TEN_KH_CHUAN","CUSTOMER_NAME","TEN"]
    code_candidates=["MA_KH_CHUAN","MA_KH_DMS","MA_KH_MBW","MA_KH","CUSTOMER_CODE"]

    tables=[r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]

    for tbl in tables:
        try:
            cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
            upper={x.upper():x for x in cols}
            name_col=next((upper[x] for x in name_candidates if x in upper),None)
            code_cols=[upper[x] for x in code_candidates if x in upper]
            if not name_col or not code_cols:
                continue
            for cc in code_cols:
                marks=",".join("?" for _ in codes)
                row=c.execute(
                    f'SELECT "{name_col}" AS ten FROM "{tbl}" '
                    f'WHERE CAST("{cc}" AS TEXT) IN ({marks}) '
                    f'AND COALESCE(CAST("{name_col}" AS TEXT),"")<>"" LIMIT 1',
                    codes
                ).fetchone()
                if row and sval(row["ten"]):
                    return sval(row["ten"])
        except Exception:
            continue
    return ""

def qtgh_v091_ui07_customer_groups(ma_nvgh):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    rows=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()
    groups={}
    for r in rows:
        key=sval(r.get("ma_kh_chuan")) or sval(r.get("ma_kh_dms")) or sval(r.get("ma_kh_mbw"))
        if not key:
            key="KH_KHONG_MA"

        if key not in groups:
            groups[key]={
              "customer_key":key,
              "ma_kh_chuan":sval(r.get("ma_kh_chuan")),
              "ma_kh_dms":sval(r.get("ma_kh_dms")),
              "ma_kh_mbw":sval(r.get("ma_kh_mbw")),
              "ten_kh":"",
              "total_balance":0,
              "orders":[]
            }

        g=groups[key]
        # Preserve any nonblank codes encountered in later rows.
        for f in ("ma_kh_chuan","ma_kh_dms","ma_kh_mbw"):
            if not g[f] and sval(r.get(f)):
                g[f]=sval(r.get(f))

        g["orders"].append(r)
        g["total_balance"]+=int(r.get("balance") or 0)

    for g in groups.values():
        g["ten_kh"]=_v091_customer_name_lookup(
            c,g["ma_kh_chuan"],g["ma_kh_dms"],g["ma_kh_mbw"]
        )
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",x.get("ma_don_nguon") or ""))

    c.close()
    out=sorted(groups.values(),key=lambda g:(g["ten_kh"] or g["customer_key"]))
    return {
      "rows":out,
      "customer_count":len(out),
      "invoice_count":sum(len(g["orders"]) for g in out),
      "total_balance":sum(g["total_balance"] for g in out)
    }

# ===== QTGH V0.9.5 UI08 allocation by debt_id =====

def qtgh_v095_debts_by_ids(ma_nvgh, debt_ids):
    ids=[]
    for x in debt_ids or []:
        try:
            v=int(x)
            if v not in ids: ids.append(v)
        except: pass
    if not ids:
        raise ValueError("Không có hóa đơn công nợ để phân bổ")

    rows=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    byid={int(r["debt_id"]):r for r in rows}
    selected=[byid[i] for i in ids if i in byid]
    if not selected:
        raise ValueError("Không tìm thấy công nợ thuộc NVGH đã chọn")

    selected.sort(key=lambda x:(x["ngay_don"] or "9999-99-99",x["created_at"] or "",x["debt_id"]))
    return selected

def qtgh_v095_preview_allocation(ma_nvgh,debt_ids,cash_amount,bank_amount):
    cash=_v09_money(cash_amount)
    bank=_v09_money(bank_amount)
    if cash<0 or bank<0: raise ValueError("Số tiền không được âm")
    total=cash+bank
    if total<=0: raise ValueError("Số tiền thực thu phải lớn hơn 0")

    rows=qtgh_v095_debts_by_ids(ma_nvgh,debt_ids)
    total_debt=sum(int(r["balance"] or 0) for r in rows)
    if total>total_debt:
        raise ValueError(f"Số tiền thu {total:,} vượt tổng công nợ KH {total_debt:,}")

    remain=total
    alloc=[]
    for r in rows:
        if remain<=0: break
        bal=int(r["balance"] or 0)
        amt=min(remain,bal)
        alloc.append({
          "customer_debt_id":r["debt_id"],
          "ma_don_nguon":r["ma_don_nguon"],
          "ngay_don":r["ngay_don"],
          "balance_before":bal,
          "allocated_amount":amt,
          "balance_after":bal-amt
        })
        remain-=amt
    return {
      "cash_amount":cash,"bank_amount":bank,"total_amount":total,
      "allocations":alloc,"unallocated":remain
    }

def qtgh_v095_add_customer_to_batch(ma_nvgh,customer_code,debt_ids,cash_amount,bank_amount,bank_account="",bank_txn_id=""):
    cash=_v09_money(cash_amount)
    bank=_v09_money(bank_amount)
    if bank>0 and (not sval(bank_account) or not sval(bank_txn_id)):
        raise ValueError("Có tiền chuyển khoản: bắt buộc chọn tài khoản nhận và nhập mã giao dịch CK")

    rows=qtgh_v095_debts_by_ids(ma_nvgh,debt_ids)
    preview=qtgh_v095_preview_allocation(ma_nvgh,debt_ids,cash,bank)
    first=rows[0]

    # stable customer code for batch display, but allocation is by debt_id
    cc=sval(customer_code) or sval(first.get("ma_kh_dms")) or sval(first.get("ma_kh_mbw")) or sval(first.get("ma_kh_chuan")) or f"DEBT_{first['debt_id']}"

    batch=qtgh_v09_get_open_batch(ma_nvgh,create=True)
    c=conn()
    try:c.execute("PRAGMA busy_timeout=8000")
    except:pass
    qtgh_v09_ensure_tables(c)

    ex=c.execute("""
      SELECT id FROM qtgh_debt_collect_customer
      WHERE batch_id=? AND customer_code=? AND status='DRAFT'
      LIMIT 1
    """,(batch["id"],cc)).fetchone()
    if ex:
        c.close()
        raise ValueError("Khách hàng này đã có trong phiên thu nợ hiện tại")

    now=datetime.datetime.now().isoformat(timespec="seconds")
    cur=c.execute("""
      INSERT INTO qtgh_debt_collect_customer(
        batch_id,customer_code,ma_kh_dms,ma_kh_mbw,
        cash_amount,bank_amount,bank_account,bank_txn_id,total_amount,status,created_at
      ) VALUES(?,?,?,?,?,?,?,?,?,'DRAFT',?)
    """,(batch["id"],cc,sval(first.get("ma_kh_dms")),sval(first.get("ma_kh_mbw")),
         cash,bank,sval(bank_account),sval(bank_txn_id),cash+bank,now))
    cid=cur.lastrowid

    for i,a in enumerate(preview["allocations"],1):
        c.execute("""
          INSERT INTO qtgh_debt_collect_allocation(
            customer_collect_id,customer_debt_id,ma_don_nguon,allocated_amount,allocation_order
          ) VALUES(?,?,?,?,?)
        """,(cid,a["customer_debt_id"],a["ma_don_nguon"],a["allocated_amount"],i))

    c.execute("""
      UPDATE qtgh_debt_collect_batch
      SET cash_total=(SELECT COALESCE(SUM(cash_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT'),
          bank_total=(SELECT COALESCE(SUM(bank_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT'),
          total_amount=(SELECT COALESCE(SUM(total_amount),0) FROM qtgh_debt_collect_customer WHERE batch_id=? AND status='DRAFT')
      WHERE id=?
    """,(batch["id"],batch["id"],batch["id"],batch["id"]))
    c.commit();c.close()
    return qtgh_v09_batch_detail(batch["id"])

# ===== QTGH V0.9.6 CUSTOMER IDENTITY + SEARCH =====
import json as _qtgh_json

def _v096_payload_customer_identity(c, order_no):
    """
    Recover customer identity from raw imported source rows by order number.
    Supports payload JSON used by DMS/MBW source loaders.
    """
    result={"ma_kh_dms":"","ma_kh_mbw":"","ma_kh_chuan":"","ten_kh":""}
    order=sval(order_no)
    if not order:
        return result

    tables=[r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]

    order_keys=("SO_HOA_DON","MA_DON_DMS","MA_DON","SO_HD","MA_DON_NGUON")
    dms_keys=("MA_KH_DMS","MA_KH_NGUON","MA_KH")
    mbw_keys=("MA_KH_MBW","MA_KH")
    std_keys=("MA_KH_CHUAN",)
    name_keys=("TEN_KH","TEN_KHACH_HANG","TEN_KH_NGUON","TEN_KH_CHUAN")

    for tbl in tables:
        try:
            cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
            cmap={x.upper():x for x in cols}

            # Direct-column tables.
            direct_order=[cmap[k] for k in order_keys if k in cmap]
            if direct_order:
                where=" OR ".join([f'CAST("{x}" AS TEXT)=?' for x in direct_order])
                row=c.execute(f'SELECT * FROM "{tbl}" WHERE {where} LIMIT 1',
                              [order]*len(direct_order)).fetchone()
                if row:
                    d=dict(row)
                    src=sval(d.get("LOAI_DON") or d.get("SOURCE_TYPE") or d.get("source_type")).upper()
                    def pick(keys):
                        for k in keys:
                            col=cmap.get(k)
                            if col and sval(d.get(col)): return sval(d.get(col))
                        return ""
                    val_std=pick(std_keys)
                    val_name=pick(name_keys)
                    val_dms=pick(dms_keys)
                    val_mbw=pick(mbw_keys)
                    if val_std and not result["ma_kh_chuan"]: result["ma_kh_chuan"]=val_std
                    if val_name and not result["ten_kh"]: result["ten_kh"]=val_name
                    if src=="B" or "MBW" in sval(tbl).upper():
                        if val_mbw and not result["ma_kh_mbw"]: result["ma_kh_mbw"]=val_mbw
                    else:
                        if val_dms and not result["ma_kh_dms"]: result["ma_kh_dms"]=val_dms

            # JSON-payload tables.
            payload_col=next((cmap[k] for k in ("PAYLOAD_JSON","PAYLOAD","DATA_JSON","ROW_JSON") if k in cmap),None)
            if payload_col:
                candidates=c.execute(
                    f'SELECT "{payload_col}" AS payload FROM "{tbl}" '
                    f'WHERE CAST("{payload_col}" AS TEXT) LIKE ? LIMIT 50',
                    (f'%{order}%',)
                ).fetchall()
                for rr in candidates:
                    try:
                        p=_qtgh_json.loads(rr["payload"]) if isinstance(rr["payload"],str) else rr["payload"]
                    except:
                        continue
                    if not isinstance(p,dict): continue
                    up={str(k).upper():v for k,v in p.items()}
                    found_order=next((sval(up.get(k)) for k in order_keys if sval(up.get(k))),"")
                    if found_order!=order: continue

                    src=sval(up.get("LOAI_DON") or up.get("SOURCE_TYPE")).upper()
                    std=next((sval(up.get(k)) for k in std_keys if sval(up.get(k))),"")
                    name=next((sval(up.get(k)) for k in name_keys if sval(up.get(k))),"")
                    dms=next((sval(up.get(k)) for k in dms_keys if sval(up.get(k))),"")
                    mbw=next((sval(up.get(k)) for k in mbw_keys if sval(up.get(k))),"")

                    if std and not result["ma_kh_chuan"]: result["ma_kh_chuan"]=std
                    if name and not result["ten_kh"]: result["ten_kh"]=name
                    if src=="B" or "MBW" in sval(tbl).upper():
                        if mbw and not result["ma_kh_mbw"]: result["ma_kh_mbw"]=mbw
                    else:
                        if dms and not result["ma_kh_dms"]: result["ma_kh_dms"]=dms
        except Exception:
            continue
    return result

def _v096_dm03_enrich(c, ident):
    """
    Map any known customer code through DM03-like master tables and recover
    canonical code / DMS / MBW / customer name where available.
    """
    codes=[x for x in [
      sval(ident.get("ma_kh_chuan")),
      sval(ident.get("ma_kh_dms")),
      sval(ident.get("ma_kh_mbw"))
    ] if x]
    if not codes:
        return ident

    tables=[r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]
    for tbl in tables:
        try:
            cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
            up={x.upper():x for x in cols}
            code_cols=[up[k] for k in ("MA_KH_CHUAN","MA_KH_DMS","MA_KH_MBW","MA_KH","SDT_CHINH") if k in up]
            if not code_cols: continue
            name_col=next((up[k] for k in ("TEN_KH","TEN_KHACH_HANG","TEN_KH_CHUAN","CUSTOMER_NAME","TEN") if k in up),None)

            for cc in code_cols:
                marks=",".join("?" for _ in codes)
                row=c.execute(
                    f'SELECT * FROM "{tbl}" WHERE CAST("{cc}" AS TEXT) IN ({marks}) LIMIT 1',
                    codes
                ).fetchone()
                if not row: continue
                d=dict(row)
                for key,field in [
                  ("ma_kh_chuan","MA_KH_CHUAN"),
                  ("ma_kh_dms","MA_KH_DMS"),
                  ("ma_kh_mbw","MA_KH_MBW")
                ]:
                    col=up.get(field)
                    if col and sval(d.get(col)): ident[key]=sval(d.get(col))
                if name_col and sval(d.get(name_col)): ident["ten_kh"]=sval(d.get(name_col))
                return ident
        except Exception:
            continue
    return ident

def qtgh_v096_customer_groups(ma_nvgh, q=""):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    debts=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()

    groups={}
    for r in debts:
        ident={
          "ma_kh_chuan":sval(r.get("ma_kh_chuan")),
          "ma_kh_dms":sval(r.get("ma_kh_dms")),
          "ma_kh_mbw":sval(r.get("ma_kh_mbw")),
          "ten_kh":""
        }

        if not any(ident.values()):
            recovered=_v096_payload_customer_identity(c,r.get("ma_don_nguon"))
            ident.update({k:v for k,v in recovered.items() if v})

        ident=_v096_dm03_enrich(c,ident)

        key=(ident["ma_kh_chuan"] or ident["ma_kh_dms"] or ident["ma_kh_mbw"]
             or f"DEBT_{r['debt_id']}")

        if key not in groups:
            groups[key]={
              "customer_key":key,
              "ma_kh_chuan":ident["ma_kh_chuan"],
              "ma_kh_dms":ident["ma_kh_dms"],
              "ma_kh_mbw":ident["ma_kh_mbw"],
              "ten_kh":ident["ten_kh"],
              "total_balance":0,
              "orders":[]
            }

        g=groups[key]
        for f in ("ma_kh_chuan","ma_kh_dms","ma_kh_mbw","ten_kh"):
            if not g[f] and ident.get(f): g[f]=ident[f]
        g["orders"].append(r)
        g["total_balance"]+=int(r.get("balance") or 0)

    c.close()

    term=sval(q).upper()
    out=[]
    for g in groups.values():
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",x.get("ma_don_nguon") or ""))
        hay=" ".join([
          g["customer_key"],g["ma_kh_chuan"],g["ma_kh_dms"],g["ma_kh_mbw"],g["ten_kh"]
        ]).upper()
        if term and term not in hay:
            continue
        out.append(g)

    out.sort(key=lambda g:(g["ten_kh"] or g["ma_kh_chuan"] or g["ma_kh_dms"] or g["ma_kh_mbw"] or g["customer_key"]))
    return {
      "rows":out,
      "customer_count":len(out),
      "invoice_count":sum(len(g["orders"]) for g in out),
      "total_balance":sum(g["total_balance"] for g in out)
    }

# ===== QTGH V1.0.1 EXACT CUSTOMER BY INVOICE =====

def _v101_invoice_customer_identity(c, order_no):
    order=sval(order_no)
    ident={"ma_kh_chuan":"","ma_kh_dms":"","ma_kh_mbw":"","ten_kh":""}
    if not order:
        return ident

    try:
        p=c.execute("""
          SELECT
            MAX(COALESCE(ma_kh_chuan,'')) ma_kh_chuan,
            MAX(COALESCE(ma_kh_dms,'')) ma_kh_dms,
            MAX(COALESCE(ma_kh_mbw,'')) ma_kh_mbw
          FROM qtgh_source_projection
          WHERE ma_don_nguon=?
        """,(order,)).fetchone()
        if p:
            ident["ma_kh_chuan"]=sval(p["ma_kh_chuan"])
            ident["ma_kh_dms"]=sval(p["ma_kh_dms"])
            ident["ma_kh_mbw"]=sval(p["ma_kh_mbw"])
    except Exception:
        pass

    try:
        raw=_v096_payload_customer_identity(c,order)
        for k in ("ma_kh_chuan","ma_kh_dms","ma_kh_mbw","ten_kh"):
            if raw.get(k) and not ident.get(k):
                ident[k]=sval(raw[k])
    except Exception:
        pass

    try:
        ident=_v096_dm03_enrich(c,ident)
    except Exception:
        pass

    return ident

def qtgh_v101_customer_groups(ma_nvgh,q=""):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    debts=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()
    groups={}

    for r in debts:
        ident=_v101_invoice_customer_identity(c,r.get("ma_don_nguon"))

        if not ident["ma_kh_chuan"]:
            ident["ma_kh_chuan"]=sval(r.get("ma_kh_chuan"))
        if not ident["ma_kh_dms"]:
            ident["ma_kh_dms"]=sval(r.get("ma_kh_dms"))
        if not ident["ma_kh_mbw"]:
            ident["ma_kh_mbw"]=sval(r.get("ma_kh_mbw"))

        try:
            ident=_v096_dm03_enrich(c,ident)
        except Exception:
            pass

        key=(ident["ma_kh_chuan"] or ident["ma_kh_dms"] or ident["ma_kh_mbw"]
             or f"DEBT_{r['debt_id']}")

        if key not in groups:
            groups[key]={
              "customer_key":key,
              "ma_kh_chuan":ident["ma_kh_chuan"],
              "ma_kh_dms":ident["ma_kh_dms"],
              "ma_kh_mbw":ident["ma_kh_mbw"],
              "ten_kh":ident["ten_kh"],
              "total_balance":0,
              "orders":[]
            }

        g=groups[key]
        for f in ("ma_kh_chuan","ma_kh_dms","ma_kh_mbw","ten_kh"):
            if not g[f] and ident.get(f):
                g[f]=ident[f]

        order_row=dict(r)
        order_row["ma_kh_chuan"]=g["ma_kh_chuan"]
        order_row["ma_kh_dms"]=g["ma_kh_dms"]
        order_row["ma_kh_mbw"]=g["ma_kh_mbw"]
        order_row["ten_kh"]=g["ten_kh"]
        g["orders"].append(order_row)
        g["total_balance"]+=int(r.get("balance") or 0)

    c.close()

    term=sval(q).upper()
    out=[]
    for g in groups.values():
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",
                                         x.get("ma_don_nguon") or ""))
        hay=" ".join([
          g["customer_key"],g["ma_kh_chuan"],g["ma_kh_dms"],
          g["ma_kh_mbw"],g["ten_kh"]
        ]).upper()
        if term and term not in hay:
            continue
        out.append(g)

    out.sort(key=lambda g:(g["ten_kh"] or g["ma_kh_chuan"] or
                           g["ma_kh_dms"] or g["ma_kh_mbw"] or g["customer_key"]))

    return {
      "rows":out,
      "customer_count":len(out),
      "invoice_count":sum(len(g["orders"]) for g in out),
      "total_balance":sum(g["total_balance"] for g in out)
    }

# ===== QTGH V1.0.3 ORIGINAL CUSTOMER CODE + FINAL UI09 =====

def _v103_original_customer_by_invoice(c, order_no):
    """
    Return MA_KH_NGUON exactly as stored on the original delivery invoice row.
    No DM03 mapping, no canonicalization.
    Priority: current COMMITTED raw XB source rows.
    """
    order=sval(order_no)
    if not order:
        return ""

    # Preferred known raw storage.
    try:
        rows=c.execute("""
          SELECT r.payload_json, b.source_type, b.status
          FROM xb_raw_row_v2 r
          JOIN xb_batch_v2 b ON b.id=r.batch_id
          WHERE b.status='COMMITTED'
          ORDER BY b.id DESC, r.id DESC
        """).fetchall()
        for rr in rows:
            try:
                p=json.loads(rr["payload_json"]) if isinstance(rr["payload_json"],str) else rr["payload_json"]
            except Exception:
                continue
            if not isinstance(p,dict):
                continue
            up={str(k).upper():v for k,v in p.items()}
            so=sval(up.get("SO_HOA_DON") or up.get("MA_DON_NGUON") or up.get("MA_DON"))
            if so==order:
                return sval(up.get("MA_KH_NGUON"))
    except Exception:
        pass

    # Fallback: scan any table with direct SO_HOA_DON + MA_KH_NGUON columns.
    try:
        tables=[r["name"] for r in c.execute(
          "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        for tbl in tables:
            try:
                cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
                up={x.upper():x for x in cols}
                oc=up.get("SO_HOA_DON") or up.get("MA_DON_NGUON") or up.get("MA_DON")
                kc=up.get("MA_KH_NGUON")
                if not oc or not kc:
                    continue
                row=c.execute(
                    f'SELECT "{kc}" AS kh FROM "{tbl}" WHERE CAST("{oc}" AS TEXT)=? LIMIT 1',
                    (order,)
                ).fetchone()
                if row and sval(row["kh"]):
                    return sval(row["kh"])
            except Exception:
                continue
    except Exception:
        pass

    # Fallback JSON scan limited to rows containing exact invoice number.
    try:
        tables=[r["name"] for r in c.execute(
          "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        for tbl in tables:
            try:
                info=c.execute(f'PRAGMA table_info("{tbl}")').fetchall()
                text_cols=[r["name"] for r in info if "TEXT" in str(r["type"]).upper()
                           or "CHAR" in str(r["type"]).upper() or not str(r["type"])]
                for tc in text_cols:
                    rs=c.execute(
                      f'SELECT "{tc}" AS v FROM "{tbl}" WHERE CAST("{tc}" AS TEXT) LIKE ? LIMIT 30',
                      (f'%{order}%',)
                    ).fetchall()
                    for rr in rs:
                        raw=rr["v"]
                        if not isinstance(raw,str) or order not in raw:
                            continue
                        try:
                            obj=json.loads(raw)
                        except Exception:
                            continue
                        stack=[obj]
                        while stack:
                            cur=stack.pop()
                            if isinstance(cur,dict):
                                up={str(k).upper():v for k,v in cur.items()}
                                so=sval(up.get("SO_HOA_DON") or up.get("MA_DON_NGUON") or up.get("MA_DON"))
                                if so==order and sval(up.get("MA_KH_NGUON")):
                                    return sval(up.get("MA_KH_NGUON"))
                                stack.extend(cur.values())
                            elif isinstance(cur,list):
                                stack.extend(cur)
            except Exception:
                continue
    except Exception:
        pass

    return ""

def qtgh_v103_customer_groups(ma_nvgh,q=""):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    debts=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()
    groups={}

    for r in debts:
        kh_goc=_v103_original_customer_by_invoice(c,r.get("ma_don_nguon"))
        key=kh_goc or f"NO_MA_KH|{r['debt_id']}"

        if key not in groups:
            groups[key]={
              "customer_key":key,
              "ma_kh_goc":kh_goc,
              "total_balance":0,
              "orders":[]
            }

        o=dict(r)
        o["ma_kh_goc"]=kh_goc
        groups[key]["orders"].append(o)
        groups[key]["total_balance"]+=int(r.get("balance") or 0)

    c.close()

    term=sval(q).upper()
    out=[]
    for g in groups.values():
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",
                                         x.get("ma_don_nguon") or ""))
        hay=(g["ma_kh_goc"] or "").upper()
        if term and term not in hay:
            continue
        out.append(g)

    out.sort(key=lambda g:(g["ma_kh_goc"] or g["customer_key"]))
    return {
      "rows":out,
      "customer_count":len(out),
      "invoice_count":sum(len(g["orders"]) for g in out),
      "total_balance":sum(g["total_balance"] for g in out)
    }

# ===== QTGH V1.0.4 ORIGINAL KH + STANDARD KH =====

def _v104_map_original_to_standard(c, ma_kh_goc):
    """
    Map exact original customer code to DM03 standard customer code.
    Does not alter original code.
    """
    code=sval(ma_kh_goc)
    if not code:
        return {"ma_kh_chuan":"","ten_kh":""}

    tables=[r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]

    for tbl in tables:
        try:
            info=c.execute(f'PRAGMA table_info("{tbl}")').fetchall()
            cols=[r["name"] for r in info]
            up={x.upper():x for x in cols}

            std_col=up.get("MA_KH_CHUAN")
            if not std_col:
                continue

            source_cols=[up[k] for k in (
                "MA_KH_DMS","MA_KH_MBW","MA_KH_NGUON","MA_KH","SDT_CHINH"
            ) if k in up]

            if not source_cols:
                continue

            name_col=next((up[k] for k in (
                "TEN_KH","TEN_KHACH_HANG","TEN_KH_CHUAN","CUSTOMER_NAME","TEN"
            ) if k in up),None)

            for sc in source_cols:
                row=c.execute(
                    f'SELECT "{std_col}" AS std'
                    + (f', "{name_col}" AS ten' if name_col else '')
                    + f' FROM "{tbl}" WHERE CAST("{sc}" AS TEXT)=? LIMIT 1',
                    (code,)
                ).fetchone()
                if row and sval(row["std"]):
                    return {
                        "ma_kh_chuan":sval(row["std"]),
                        "ten_kh":sval(row["ten"]) if name_col else ""
                    }
        except Exception:
            continue

    return {"ma_kh_chuan":"","ten_kh":""}

def qtgh_v104_customer_groups(ma_nvgh,q=""):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    debts=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()
    groups={}

    for r in debts:
        kh_goc=_v103_original_customer_by_invoice(c,r.get("ma_don_nguon"))
        mapped=_v104_map_original_to_standard(c,kh_goc)
        kh_chuan=sval(mapped.get("ma_kh_chuan"))
        ten_kh=sval(mapped.get("ten_kh"))

        # Management group uses standard code when available, otherwise original code.
        group_key=kh_chuan or kh_goc or f"NO_MA_KH|{r['debt_id']}"

        if group_key not in groups:
            groups[group_key]={
                "customer_key":group_key,
                "ma_kh_goc":kh_goc,
                "ma_kh_chuan":kh_chuan,
                "ten_kh":ten_kh,
                "mapped":bool(kh_chuan),
                "total_balance":0,
                "orders":[]
            }

        g=groups[group_key]
        if not g["ma_kh_goc"] and kh_goc:
            g["ma_kh_goc"]=kh_goc
        if not g["ma_kh_chuan"] and kh_chuan:
            g["ma_kh_chuan"]=kh_chuan
        if not g["ten_kh"] and ten_kh:
            g["ten_kh"]=ten_kh

        o=dict(r)
        o["ma_kh_goc"]=kh_goc
        o["ma_kh_chuan"]=kh_chuan
        o["ten_kh"]=ten_kh
        g["orders"].append(o)
        g["total_balance"]+=int(r.get("balance") or 0)

    c.close()

    term=sval(q).upper()
    out=[]
    for g in groups.values():
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",
                                         x.get("ma_don_nguon") or ""))
        hay=" ".join([
            g.get("ma_kh_goc",""),
            g.get("ma_kh_chuan",""),
            g.get("ten_kh","")
        ]).upper()
        if term and term not in hay:
            continue
        out.append(g)

    out.sort(key=lambda g:(g["ma_kh_chuan"] or g["ma_kh_goc"] or g["customer_key"]))

    return {
        "rows":out,
        "customer_count":len(out),
        "invoice_count":sum(len(g["orders"]) for g in out),
        "total_balance":sum(g["total_balance"] for g in out),
        "unmapped_count":sum(1 for g in out if not g["mapped"])
    }

# ===== QTGH V1.0.5 DM03 EXACT ALIAS MAP =====

def _v105_map_original_to_standard(c, ma_kh_goc):
    """
    Map MA_KH_NGUON -> DM03 using actual aliases in current Mini App:
    MA_DMS / MA_MBW -> MA_KH_CHUAN.
    Also supports old aliases MA_KH_DMS / MA_KH_MBW.
    """
    code=sval(ma_kh_goc).strip()
    if not code:
        return {"ma_kh_chuan":"","ma_mbw":"","ma_dms":"","ten_kh":""}

    tables=[r["name"] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]

    for tbl in tables:
        try:
            info=c.execute(f'PRAGMA table_info("{tbl}")').fetchall()
            cols=[r["name"] for r in info]
            up={x.upper():x for x in cols}

            std_col=up.get("MA_KH_CHUAN")
            if not std_col:
                continue

            # Actual DM03 aliases first.
            dms_col=up.get("MA_DMS") or up.get("MA_KH_DMS")
            mbw_col=up.get("MA_MBW") or up.get("MA_KH_MBW")
            name_col=(up.get("TEN_KH") or up.get("TEN_KHACH_HANG") or
                      up.get("TEN_KH_CHUAN") or up.get("CUSTOMER_NAME") or up.get("TEN"))

            source_cols=[x for x in (dms_col,mbw_col) if x]
            if not source_cols:
                continue

            for sc in source_cols:
                select_parts=[
                    f'"{std_col}" AS ma_kh_chuan',
                    f'"{dms_col}" AS ma_dms' if dms_col else "'' AS ma_dms",
                    f'"{mbw_col}" AS ma_mbw' if mbw_col else "'' AS ma_mbw",
                    f'"{name_col}" AS ten_kh' if name_col else "'' AS ten_kh",
                ]
                row=c.execute(
                    f'SELECT {",".join(select_parts)} FROM "{tbl}" '
                    f'WHERE TRIM(CAST("{sc}" AS TEXT))=? LIMIT 1',
                    (code,)
                ).fetchone()
                if row and sval(row["ma_kh_chuan"]):
                    return {
                        "ma_kh_chuan":sval(row["ma_kh_chuan"]),
                        "ma_mbw":sval(row["ma_mbw"]),
                        "ma_dms":sval(row["ma_dms"]),
                        "ten_kh":sval(row["ten_kh"])
                    }
        except Exception:
            continue

    # Generic master-data storage fallback:
    # some installations store DM03 in shared tables with _DATASET/_TABLE markers.
    for tbl in tables:
        try:
            info=c.execute(f'PRAGMA table_info("{tbl}")').fetchall()
            cols=[r["name"] for r in info]
            up={x.upper():x for x in cols}
            if "MA_KH_CHUAN" not in up:
                continue

            candidates=[]
            for alias in ("MA_DMS","MA_KH_DMS","MA_MBW","MA_KH_MBW"):
                if alias in up:
                    candidates.append(up[alias])
            for sc in candidates:
                row=c.execute(
                    f'SELECT * FROM "{tbl}" WHERE TRIM(CAST("{sc}" AS TEXT))=? LIMIT 1',
                    (code,)
                ).fetchone()
                if row:
                    d=dict(row)
                    def gv(*names):
                        for n in names:
                            col=up.get(n)
                            if col and sval(d.get(col)):
                                return sval(d.get(col))
                        return ""
                    return {
                        "ma_kh_chuan":gv("MA_KH_CHUAN"),
                        "ma_mbw":gv("MA_MBW","MA_KH_MBW"),
                        "ma_dms":gv("MA_DMS","MA_KH_DMS"),
                        "ten_kh":gv("TEN_KH","TEN_KHACH_HANG","TEN_KH_CHUAN")
                    }
        except Exception:
            continue

    return {"ma_kh_chuan":"","ma_mbw":"","ma_dms":"","ten_kh":""}

def qtgh_v105_customer_groups(ma_nvgh,q=""):
    if not sval(ma_nvgh):
        raise ValueError("Bắt buộc chọn NVGH")

    debts=_v09_customer_debt_rows(ma_nvgh=ma_nvgh)
    c=conn()
    groups={}

    for r in debts:
        kh_goc=_v103_original_customer_by_invoice(c,r.get("ma_don_nguon"))
        mapped=_v105_map_original_to_standard(c,kh_goc)

        kh_chuan=sval(mapped.get("ma_kh_chuan"))
        ma_dms=sval(mapped.get("ma_dms"))
        ma_mbw=sval(mapped.get("ma_mbw"))
        ten_kh=sval(mapped.get("ten_kh"))

        group_key=kh_chuan or kh_goc or f"NO_MA_KH|{r['debt_id']}"

        if group_key not in groups:
            groups[group_key]={
                "customer_key":group_key,
                "ma_kh_goc":kh_goc,
                "ma_kh_chuan":kh_chuan,
                "ma_dms":ma_dms,
                "ma_mbw":ma_mbw,
                "ten_kh":ten_kh,
                "mapped":bool(kh_chuan),
                "total_balance":0,
                "orders":[]
            }

        g=groups[group_key]
        for f,v in [
            ("ma_kh_goc",kh_goc),("ma_kh_chuan",kh_chuan),
            ("ma_dms",ma_dms),("ma_mbw",ma_mbw),("ten_kh",ten_kh)
        ]:
            if not g.get(f) and v:
                g[f]=v

        o=dict(r)
        o.update({
            "ma_kh_goc":kh_goc,
            "ma_kh_chuan":kh_chuan,
            "ma_dms":ma_dms,
            "ma_mbw":ma_mbw,
            "ten_kh":ten_kh
        })
        g["orders"].append(o)
        g["total_balance"]+=int(r.get("balance") or 0)

    c.close()

    term=sval(q).upper()
    out=[]
    for g in groups.values():
        g["orders"].sort(key=lambda x:(x.get("ngay_don") or "9999-99-99",
                                         x.get("ma_don_nguon") or ""))
        hay=" ".join([
            g.get("ma_kh_goc",""), g.get("ma_kh_chuan",""),
            g.get("ma_dms",""), g.get("ma_mbw",""), g.get("ten_kh","")
        ]).upper()
        if term and term not in hay:
            continue
        out.append(g)

    out.sort(key=lambda g:(g["ma_kh_chuan"] or g["ma_kh_goc"] or g["customer_key"]))
    return {
        "rows":out,
        "customer_count":len(out),
        "invoice_count":sum(len(g["orders"]) for g in out),
        "total_balance":sum(g["total_balance"] for g in out),
        "unmapped_count":sum(1 for g in out if not g["mapped"])
    }
