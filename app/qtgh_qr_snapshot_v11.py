from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
import sqlite3, json, hashlib, datetime, uuid, urllib.parse, urllib.request, unicodedata

router=APIRouter(prefix="/api/qtgh-v11",tags=["QTGH BA V1.1"])
ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"data"/"miniapp.db"
QR_ROOT=ROOT/"data"/"qtgh_print_assets"/"qr"
QR_ROOT.mkdir(parents=True,exist_ok=True)

BANK_BINS={
    "0301100913003":"970422",
    "112704070669999":"970437",
    "114604844888":"970415",
    "2803032006":"970436",
    "8600851999":"970418",
}

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

def ascii_text(s):
    s=unicodedata.normalize("NFD",str(s or ""))
    s="".join(ch for ch in s if unicodedata.category(ch)!="Mn")
    return " ".join(s.replace("Đ","D").replace("đ","d").split())

def ensure_schema():
    c=conn()
    bcols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_receiving_bank_account)")}
    if "bank_bin" not in bcols:
        c.execute("ALTER TABLE qtgh_receiving_bank_account ADD COLUMN bank_bin TEXT")
    if "qr_service_code" not in bcols:
        c.execute("ALTER TABLE qtgh_receiving_bank_account ADD COLUMN qr_service_code TEXT DEFAULT 'QRIBFTTA'")
    for acc,bin_code in BANK_BINS.items():
        c.execute("""UPDATE qtgh_receiving_bank_account
                     SET bank_bin=?,qr_service_code='QRIBFTTA'
                     WHERE account_no=? OR ma_tknh=?""",(bin_code,acc,acc))

    pcols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_print_batch)")}
    if "snapshot_checksum" not in pcols:
        c.execute("ALTER TABLE qtgh_print_batch ADD COLUMN snapshot_checksum TEXT")
    if "status" not in pcols:
        c.execute("ALTER TABLE qtgh_print_batch ADD COLUMN status TEXT DEFAULT 'SNAPSHOT_LOCKED'")

    qcols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_payment_qr_snapshot)")}
    for name,ddl in [
        ("qr_image_path","TEXT"),
        ("qr_image_checksum","TEXT"),
        ("quicklink_url","TEXT"),
    ]:
        if name not in qcols:
            c.execute(f"ALTER TABLE qtgh_payment_qr_snapshot ADD COLUMN {name} {ddl}")
    c.commit();c.close()

ensure_schema()

def build_order_snapshot(c,lot,order_no,loai,product_names_for_lot=None):
    # VG_PRODUCT_NAMES_V1
    from .qtgh_product_print_names import product_names, display_name
    if product_names_for_lot is None:
        product_names_for_lot=product_names(c)
    lines=[dict(r) for r in c.execute("""SELECT * FROM qtgh_prep_line
        WHERE prep_batch_id=? AND ma_don_nguon=? ORDER BY id""",
        (lot["prep_batch_id"],order_no)).fetchall()]
    if not lines:
        raise HTTPException(400,f"Đơn {order_no}: không có staging")
    first=lines[0]
    bank=c.execute("""SELECT id,ma_tknh,bank_name,account_no,account_name,status,
        bank_bin,COALESCE(qr_service_code,'QRIBFTTA') qr_service_code
        FROM qtgh_receiving_bank_account WHERE id=? AND status='ACTIVE'""",
        (first["receiving_bank_id"],)).fetchone()
    if not bank:
        raise HTTPException(400,f"Đơn {order_no}: thiếu tài khoản nhận hợp lệ")
    bd=dict(bank)
    if not bd.get("bank_bin"):
        raise HTTPException(400,f"Đơn {order_no}: tài khoản {bd.get('account_no')} chưa có BANK_BIN")
    A=sum(int(x["amount_due_order"] or 0) for x in lines)
    B=max(int(x["order_reward_accum"] or 0) for x in lines)
    C=max(int(x["order_reward_display"] or 0) for x in lines)
    D=max(0,A-B-C)
    return {
        "loai_don":loai,"so_hoa_don":order_no,"order_date":first["order_date"],
        "planned":{
            "delivery_date":first["planned_delivery_date"],
            "delivery_staff_code":first["planned_delivery_staff_code"],
            "driver_code":first["planned_driver_code"],
            "vehicle_code":first["planned_vehicle_code"],
            "lot_code":first["planned_lot_code"],
        },
        "bank":bd,
        "amount":{"A":A,"B":B,"C":C,"D":D},
        "lines":[{
            "source_row_no":x["source_row_no"],"ma_sku":x["ma_sku"],"ten_sku":display_name(product_names_for_lot, x["ma_sku"], x["ten_sku"]),
            "source_ten_sku":x["ten_sku"],
            "sale_qty_su":x["sale_qty_su"],"promo_qty_su":x["promo_qty_su"],
            "unit_price_vat":x["unit_price_vat"],"line_discount":x["line_discount"],
            "amount_due_order":x["amount_due_order"],"raw_payload_json":x["raw_payload_json"]
        } for x in lines]
    }

def make_quicklink(order):
    b=order["bank"]
    info=f"VG {order['so_hoa_don']}"[:25]
    q=urllib.parse.urlencode({
        "amount":order["amount"]["D"],
        "addInfo":info,
    })
    url=f"https://img.vietqr.io/image/{b['bank_bin']}-{b['account_no']}-qr_only.png?{q}"
    return url,info

def download_png(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=25) as r:
        data=r.read()
    if len(data)<100 or not data.startswith(b"\x89PNG"):
        raise RuntimeError("VietQR không trả về PNG hợp lệ")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

@router.get("/bank-qr-readiness")
def bank_qr_readiness():
    c=conn()
    rows=[dict(r) for r in c.execute("""SELECT id,ma_tknh,bank_name,account_no,account_name,
        status,bank_bin,qr_service_code FROM qtgh_receiving_bank_account ORDER BY id""")]
    c.close()
    for r in rows:
        r["qr_ready"]=bool(r.get("bank_bin") and r.get("account_no") and r.get("account_name"))
    return {"rows":rows}

def download_vietqr_image(url,path):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0",
        "Accept":"image/png",
        "Referer":"https://vietqr.io/",
    })
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            data=r.read()
            status=getattr(r,"status",200)
            ctype=str(r.headers.get("Content-Type") or "").lower()
    except Exception as e:
        raise RuntimeError(f"Lỗi tải VietQR: {type(e).__name__}: {e}")
    # VietQR can send JPEG bytes from a .png URL with image/png Content-Type.
    # Trust the actual image signature and save with the matching extension.
    png=data.startswith(b"\x89PNG\r\n\x1a\n")
    jpeg=data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")
    if len(data)<100 or not (png or jpeg):
        raise RuntimeError(f"VietQR không trả về PNG/JPEG hợp lệ; HTTP={status}; Content-Type={ctype}; Size={len(data)}; First16={data[:16].hex()}")
    saved_path=path.with_suffix(".png" if png else ".jpg")
    saved_path.parent.mkdir(parents=True,exist_ok=True)
    saved_path.write_bytes(data)
    return hashlib.sha256(data).hexdigest(),saved_path

@router.post("/print-lot/{print_lot_id}/lock-snapshot")
async def lock_snapshot(print_lot_id:str,request:Request):
    body=await request.json()
    user=str(body.get("username") or "pilot")
    c=conn()
    lot=c.execute("SELECT * FROM qtgh_print_lot WHERE print_lot_id=?",(print_lot_id,)).fetchone()
    if not lot:
        c.close();raise HTTPException(404,"Không tìm thấy PRINT LOT")

    old=c.execute("""SELECT * FROM qtgh_print_batch WHERE print_lot_id=?
                     ORDER BY print_version DESC LIMIT 1""",(print_lot_id,)).fetchone()
    if old:
        d=dict(old);c.close()
        return {"print_batch_id":d["print_batch_id"],"print_lot_id":print_lot_id,
                "snapshot_checksum":d.get("snapshot_checksum"),"status":d.get("status"),
                "idempotent":True}

    refs=[dict(r) for r in c.execute("""SELECT loai_don,ma_don_nguon
        FROM qtgh_print_lot_order WHERE print_lot_id=? ORDER BY ma_don_nguon""",(print_lot_id,))]
    from .qtgh_product_print_names import product_names
    names_for_lot=product_names(c)
    orders=[build_order_snapshot(c,lot,r["ma_don_nguon"],r["loai_don"],names_for_lot) for r in refs]

    print_batch_id="PRINT-"+uuid.uuid4().hex[:12].upper()
    final_dir=QR_ROOT/print_batch_id
    created=[]
    qr_rows=[]
    try:
        for o in orders:
            url,content=make_quicklink(o)
            qid="QR-"+uuid.uuid4().hex[:12].upper()
            fn=f"{o['loai_don']}_{o['so_hoa_don']}.png".replace("/","_").replace("\\","_")
            path=final_dir/fn
            img_hash,path=download_vietqr_image(url,path)
            created.append(path)
            qr_rows.append((qid,o,content,url,path,img_hash))

        snapshot={"product_name_mapping_version":1,"ba":"QTGH BA PRINT LOT 01 V1.1","print_lot_id":print_lot_id,
                  "prep_batch_id":lot["prep_batch_id"],"print_batch_id":print_batch_id,
                  "created_at":now(),"orders":orders}
        raw=canon(snapshot)
        shash=hashlib.sha256(raw.encode("utf-8")).hexdigest()

        c.execute("BEGIN IMMEDIATE")
        c.execute("""INSERT INTO qtgh_print_batch(
            print_batch_id,print_lot_id,print_version,pdf_path,pdf_checksum,
            snapshot_json,created_by,created_at,snapshot_checksum,status)
            VALUES(?,?,1,NULL,NULL,?,?,?,?, 'SNAPSHOT_LOCKED')""",
            (print_batch_id,print_lot_id,raw,user,now(),shash))

        for qid,o,content,url,path,img_hash in qr_rows:
            b=o["bank"]
            phash=hashlib.sha256(url.encode("utf-8")).hexdigest()
            c.execute("""INSERT INTO qtgh_payment_qr_snapshot(
              qr_snapshot_id,print_batch_id,loai_don,ma_don_nguon,bank_id,bank_name,
              account_no,account_name,amount,transfer_content,payload_text,payload_checksum,
              created_at,qr_image_path,qr_image_checksum,quicklink_url)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (qid,print_batch_id,o["loai_don"],o["so_hoa_don"],b["id"],b["bank_name"],
               b["account_no"],b["account_name"],o["amount"]["D"],content,url,phash,now(),
               str(path.relative_to(ROOT)),img_hash,url))

        c.execute("UPDATE qtgh_print_lot SET status='DA_IN' WHERE print_lot_id=?",(print_lot_id,))
        c.execute("""INSERT INTO qtgh_delivery_audit(
          event_type,object_type,object_id,username,occurred_at,after_json)
          VALUES('PRINT_SNAPSHOT_LOCK','PRINT_LOT',?,?,?,?)""",
          (print_lot_id,user,now(),canon({"print_batch_id":print_batch_id,
            "snapshot_checksum":shash,"order_count":len(orders)})))
        c.commit()
    except Exception as e:
        c.rollback()
        for p in created:
            try:p.unlink()
            except Exception:pass
        c.close()
        raise HTTPException(400,f"Không thể tạo snapshot/QR: {e}")

    c.close()
    return {"print_batch_id":print_batch_id,"print_lot_id":print_lot_id,
            "snapshot_checksum":shash,"status":"SNAPSHOT_LOCKED",
            "order_count":len(orders),"qr_count":len(qr_rows),"idempotent":False}

@router.get("/print-lot/{print_lot_id}/qr-map")
def qr_map(print_lot_id:str):
    c=conn()
    pb=c.execute("""SELECT print_batch_id,status,snapshot_checksum FROM qtgh_print_batch
        WHERE print_lot_id=? ORDER BY print_version DESC LIMIT 1""",(print_lot_id,)).fetchone()
    if not pb:
        c.close();raise HTTPException(404,"PRINT LOT chưa khóa snapshot")
    rows=[]
    for r in c.execute("""SELECT qr_snapshot_id,loai_don,ma_don_nguon,amount,
        transfer_content,qr_image_checksum FROM qtgh_payment_qr_snapshot
        WHERE print_batch_id=? ORDER BY ma_don_nguon""",(pb["print_batch_id"],)):
        d=dict(r);d["qr_url"]=f"/api/qtgh-v11/qr-image/{d['qr_snapshot_id']}";rows.append(d)
    out={"print_batch_id":pb["print_batch_id"],"status":pb["status"],
         "snapshot_checksum":pb["snapshot_checksum"],"rows":rows}
    c.close();return out

@router.get("/qr-image/{qr_snapshot_id}")
def qr_image(qr_snapshot_id:str):
    c=conn()
    r=c.execute("SELECT qr_image_path FROM qtgh_payment_qr_snapshot WHERE qr_snapshot_id=?",
                (qr_snapshot_id,)).fetchone()
    c.close()
    if not r or not r["qr_image_path"]:raise HTTPException(404,"Không tìm thấy QR snapshot")
    p=(ROOT/r["qr_image_path"]).resolve()
    asset_root=(ROOT/"data"/"qtgh_print_assets").resolve()
    if not p.is_relative_to(asset_root):
        raise HTTPException(404,"Đường dẫn ảnh QR ngoài vùng tài nguyên")
    if not p.is_file():raise HTTPException(404,"File QR snapshot không tồn tại")
    try:
        signature=p.read_bytes()[:8]
    except OSError as exc:
        raise HTTPException(404,"Không đọc được file QR snapshot") from exc
    media_type="image/png" if signature.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if signature.startswith(b"\xff\xd8\xff") else None
    if not media_type:raise HTTPException(500,"Ảnh QR snapshot không hợp lệ")
    return FileResponse(p,media_type=media_type,filename=p.name)
