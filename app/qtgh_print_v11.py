from fastapi import APIRouter, HTTPException, Query, Body
from pathlib import Path
from decimal import Decimal, InvalidOperation
import sqlite3, datetime, json

router = APIRouter(prefix="/api/qtgh-v11", tags=["QTGH BA V1.1"])

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "miniapp.db"

def conn():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=5000")
    return c

def ensure_schema():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS qtgh_prep_batch(
      prep_batch_id TEXT PRIMARY KEY,
      source_file_name TEXT NOT NULL,
      source_checksum TEXT NOT NULL,
      uploaded_by TEXT,
      uploaded_at TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'DA_NAP_HOP_LE',
      total_orders INTEGER NOT NULL DEFAULT 0,
      total_lines INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      validation_json TEXT,
      UNIQUE(source_checksum)
    );

    CREATE TABLE IF NOT EXISTS qtgh_prep_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      prep_batch_id TEXT NOT NULL,
      source_row_no INTEGER,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      order_date TEXT NOT NULL,
      planned_delivery_date TEXT NOT NULL,
      planned_delivery_staff_code TEXT,
      planned_driver_code TEXT,
      planned_vehicle_code TEXT,
      planned_lot_code TEXT,
      delivery_sequence INTEGER,
      receiving_bank_id INTEGER,
      ma_nvtt TEXT,
      ma_kh_chuan TEXT,
      ma_kh_mbw TEXT,
      ma_kh_dms TEXT,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sale_qty_su TEXT NOT NULL DEFAULT '0',
      promo_qty_su TEXT NOT NULL DEFAULT '0',
      unit_price_vat INTEGER NOT NULL DEFAULT 0,
      line_discount INTEGER NOT NULL DEFAULT 0,
      order_reward_accum INTEGER NOT NULL DEFAULT 0,
      order_reward_display INTEGER NOT NULL DEFAULT 0,
      amount_due_order INTEGER NOT NULL DEFAULT 0,
      raw_payload_json TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(prep_batch_id) REFERENCES qtgh_prep_batch(prep_batch_id),
      UNIQUE(prep_batch_id,source_row_no,ma_sku)
    );

    CREATE TABLE IF NOT EXISTS qtgh_print_lot(
      print_lot_id TEXT PRIMARY KEY,
      prep_batch_id TEXT NOT NULL,
      planned_delivery_date TEXT NOT NULL,
      planned_delivery_staff_code TEXT,
      planned_driver_code TEXT,
      planned_vehicle_code TEXT,
      planned_lot_code TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'DA_NAP_HOP_LE',
      order_count INTEGER NOT NULL DEFAULT 0,
      customer_count INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      created_by TEXT,
      created_at TEXT NOT NULL,
      version INTEGER NOT NULL DEFAULT 1,
      FOREIGN KEY(prep_batch_id) REFERENCES qtgh_prep_batch(prep_batch_id)
    );

    CREATE TABLE IF NOT EXISTS qtgh_print_lot_order(
      print_lot_id TEXT NOT NULL,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      PRIMARY KEY(print_lot_id,loai_don,ma_don_nguon),
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id)
    );

    CREATE TABLE IF NOT EXISTS qtgh_print_batch(
      print_batch_id TEXT PRIMARY KEY,
      print_lot_id TEXT NOT NULL,
      print_version INTEGER NOT NULL,
      pdf_path TEXT,
      pdf_checksum TEXT,
      snapshot_json TEXT NOT NULL,
      created_by TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id),
      UNIQUE(print_lot_id,print_version)
    );

    CREATE TABLE IF NOT EXISTS qtgh_payment_qr_snapshot(
      qr_snapshot_id TEXT PRIMARY KEY,
      print_batch_id TEXT NOT NULL,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      bank_id INTEGER NOT NULL,
      bank_name TEXT NOT NULL,
      account_no TEXT NOT NULL,
      account_name TEXT,
      amount INTEGER NOT NULL,
      transfer_content TEXT NOT NULL,
      payload_text TEXT NOT NULL,
      payload_checksum TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY(print_batch_id) REFERENCES qtgh_print_batch(print_batch_id),
      UNIQUE(print_batch_id,loai_don,ma_don_nguon)
    );

    CREATE TABLE IF NOT EXISTS qtgh_delivery_finalization(
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
      version INTEGER NOT NULL,
      handoff_id TEXT,
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id)
    );

    CREATE TABLE IF NOT EXISTS qtgh_handoff(
      handoff_id TEXT PRIMARY KEY,
      print_lot_id TEXT NOT NULL UNIQUE,
      finalization_id TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL,
      order_count INTEGER NOT NULL DEFAULT 0,
      line_count INTEGER NOT NULL DEFAULT 0,
      performed_by TEXT,
      performed_at TEXT,
      error_text TEXT,
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id),
      FOREIGN KEY(finalization_id) REFERENCES qtgh_delivery_finalization(finalization_id)
    );

    CREATE TABLE IF NOT EXISTS qtgh_delivery_audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL,
      object_type TEXT NOT NULL,
      object_id TEXT NOT NULL,
      username TEXT,
      occurred_at TEXT NOT NULL,
      before_json TEXT,
      after_json TEXT,
      reason TEXT,
      source_note TEXT
    );

    CREATE INDEX IF NOT EXISTS ix_qtgh_prep_line_order
      ON qtgh_prep_line(loai_don,ma_don_nguon);

    CREATE INDEX IF NOT EXISTS ix_qtgh_prep_line_planned_lot
      ON qtgh_prep_line(planned_delivery_date,planned_lot_code,planned_delivery_staff_code);

    CREATE INDEX IF NOT EXISTS ix_qtgh_delivery_audit_obj
      ON qtgh_delivery_audit(object_type,object_id,occurred_at);
    """)
    c.commit()
    c.close()

ensure_schema()

@router.get("/meta")
def meta():
    return {
      "ba":"QTGH BA PRINT LOT 01 V1.1",
      "status":"DA_PHE_DUYET",
      "d0_rule":"NGAY_DON",
      "ui03_ui11_unchanged":True,
      "phase":"PHASE2C_UI_FLOW"
    }

@router.get("/schema-status")
def schema_status():
    c=conn()
    names=[
      "qtgh_prep_batch","qtgh_prep_line","qtgh_print_lot","qtgh_print_lot_order",
      "qtgh_print_batch","qtgh_payment_qr_snapshot","qtgh_delivery_finalization",
      "qtgh_handoff","qtgh_delivery_audit"
    ]
    rows={t:c.execute(f'SELECT COUNT(*) n FROM "{t}"').fetchone()["n"] for t in names}
    c.close()
    return {"tables":rows}

@router.get("/banks")
def banks():
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT id,bank_name,account_no,account_name,status
      FROM qtgh_receiving_bank_account
      WHERE status='ACTIVE'
      ORDER BY id
    """).fetchall()]
    c.close()
    return {"rows":rows}

@router.get("/prep-batches")
def prep_batches():
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT * FROM qtgh_prep_batch
      ORDER BY uploaded_at DESC
      LIMIT 100
    """).fetchall()]
    c.close()
    return {"rows":rows}

@router.get("/print-lots")
def print_lots():
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT * FROM qtgh_print_lot
      ORDER BY created_at DESC
      LIMIT 200
    """).fetchall()]
    c.close()
    return {"rows":rows}


HC_GROUPS = {"101", "102", "103", "104", "105"}
PC_GROUPS = {"106", "107", "108", "109", "111", "112", "113", "114",
             "144", "315", "316", "731", "824"}


def vehicle_pick_list(c, lot_ids, order_keys=None, arrange=False):
    """Read-only pick list. A new selection always recalculates from source lines."""
    ids = list(dict.fromkeys(str(x).strip() for x in lot_ids))
    selected_orders = []
    for item in order_keys or []:
        if not isinstance(item, dict):
            raise ValueError("Danh sách đơn không hợp lệ")
        key = tuple(str(item.get(k) or '').strip() for k in ('print_lot_id', 'loai_don', 'ma_don_nguon'))
        if not all(key):
            raise ValueError("Đơn được chọn thiếu lô, loại hoặc mã đơn")
        selected_orders.append(key)
    selected_orders = list(dict.fromkeys(selected_orders))
    lookup_ids = list(dict.fromkeys(ids + [key[0] for key in selected_orders]))
    if not lookup_ids or any(not x for x in lookup_ids) or len(lookup_ids) > 100 or len(selected_orders) > 5000:
        raise ValueError("Chọn tối đa 100 lô và 5.000 đơn để in")
    marks = ",".join("?" for _ in lookup_ids)
    lots = [dict(x) for x in c.execute(f"""
      SELECT l.*, f.actual_delivery_date, f.actual_vehicle_code
      FROM qtgh_print_lot l
      LEFT JOIN qtgh_delivery_finalization f ON f.print_lot_id=l.print_lot_id
      WHERE l.print_lot_id IN ({marks})""", lookup_ids)]
    if len(lots) != len(lookup_ids):
        raise ValueError("Có lô không tồn tại")
    by_id = {x["print_lot_id"]: x for x in lots}
    lots = [by_id[x] for x in lookup_ids]
    def vehicle(x):
        return str(x["actual_vehicle_code"] or x["planned_vehicle_code"] or "").strip().upper()
    def day(x):
        return str(x["actual_delivery_date"] or x["planned_delivery_date"] or "")[:10]
    if not arrange and any(not vehicle(x) or not day(x) for x in lots):
        raise ValueError("Có lô thiếu xe hoặc ngày giao")
    all_orders = set()
    for lot in lots:
        for order in c.execute("SELECT loai_don,ma_don_nguon FROM qtgh_print_lot_order WHERE print_lot_id=?", (lot['print_lot_id'],)):
            all_orders.add((lot['print_lot_id'], order['loai_don'], order['ma_don_nguon']))
    if any(key not in all_orders for key in selected_orders):
        raise ValueError("Có đơn không thuộc lô đã chọn")
    selected = {key for key in all_orders if key[0] in ids} | set(selected_orders)

    products = {}
    for r in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category='dm01-product'"):
        try:
            p = json.loads(r["payload_json"] or "{}")
        except (TypeError, ValueError):
            continue
        products[str(p.get("MA_SKU") or r["business_key"] or "").strip().upper()] = p

    totals = {}
    for lot in lots:
        for line in c.execute("""SELECT p.ma_sku,p.ten_sku,p.sale_qty_su,p.promo_qty_su,
                         p.unit_price_vat,p.raw_payload_json,o.loai_don,o.ma_don_nguon
          FROM qtgh_print_lot_order o
          JOIN qtgh_prep_line p ON p.prep_batch_id=?
            AND p.loai_don=o.loai_don AND p.ma_don_nguon=o.ma_don_nguon
          WHERE o.print_lot_id=?""", (lot["prep_batch_id"], lot["print_lot_id"])):
            if (lot['print_lot_id'], line['loai_don'], line['ma_don_nguon']) not in selected:
                continue
            sku = str(line["ma_sku"] or "").strip().upper()
            prod = products.get(sku)
            if not prod:
                raise ValueError(f"SKU {sku} thiếu danh mục DM01")
            group = str(prod.get("MA_NHAN") or "").strip()
            try:
                pack = Decimal(str(prod.get("SO_SU_THUNG") or ""))
                sale = Decimal(str(line["sale_qty_su"] or "0"))
                promo = Decimal(str(line["promo_qty_su"] or "0"))
            except InvalidOperation:
                raise ValueError(f"SKU {sku} có quy cách hoặc số lượng không hợp lệ")
            if pack <= 0 or pack != int(pack) or sale < 0 or promo < 0 or sale != int(sale) or promo != int(promo):
                raise ValueError(f"SKU {sku} cần quy cách và số lượng SU nguyên không âm")
            if sku not in totals:
                totals[sku] = {"sku": sku, "name": str(prod.get("TEN_SKU") or line["ten_sku"] or sku),
                               "group": group, "pack_su": int(pack), "sale_su": 0,
                               "promo_su": 0, "source_cases": 0, "source_loose_su": 0, "sort_price": None}
            item = totals[sku]
            if item["pack_su"] != int(pack) or item["group"] != group:
                raise ValueError(f"SKU {sku} có quy cách hoặc nhóm không nhất quán")
            if arrange:
                # VG_PICK_SOURCE_CASES_V1: preserve full cases separately from pooled loose SU.
                try:
                    raw = json.loads(line["raw_payload_json"] or "{}")
                    keys = ("SL_THUNG", "SL_SU", "SL_KM_THUNG", "SL_KM_SU")
                    if not isinstance(raw, dict) or not any(k in raw for k in keys):
                        raise ValueError("Thiếu cột thùng/SU của đơn nguồn")
                    numbers = [Decimal(str(raw.get(k) or 0)) for k in keys]
                    if any(not n.is_finite() or n < 0 or n != int(n) for n in numbers):
                        raise ValueError("Số thùng/SU nguồn phải nguyên không âm")
                    sale_cases, sale_loose, promo_cases, promo_loose = map(int, numbers)
                    if sale_cases * int(pack) + sale_loose != int(sale) or promo_cases * int(pack) + promo_loose != int(promo):
                        raise ValueError("Số thùng/SU nguồn không khớp số lượng đã nạp hoặc QC")
                except (TypeError, ValueError, InvalidOperation) as e:
                    raise ValueError(f"Đơn {line['ma_don_nguon']}, SKU {sku}: {e}")
                item["source_cases"] += sale_cases + promo_cases
                item["source_loose_su"] += sale_loose + promo_loose
            item["sale_su"] += int(sale)
            item["promo_su"] += int(promo)
            price = int(line["unit_price_vat"] or 0)
            if price > 0 and (item["sort_price"] is None or price < item["sort_price"]):
                item["sort_price"] = price

    if not totals:
        raise ValueError("Các lô đã chọn không có dòng hàng để in")
    sheets = {"HC": [], "PC": [], "KHÁC": []}
    for item in totals.values():
        qty = item["sale_su"] + item["promo_su"]
        if qty <= 0:
            continue
        if arrange:
            item["loose_cases"], item["remaining_loose_su"] = divmod(item["source_loose_su"], item["pack_su"])
            if (item["source_cases"] + item["loose_cases"]) * item["pack_su"] + item["remaining_loose_su"] != qty:
                raise ValueError("SKU " + item["sku"] + " không khớp tổng SU")
        item["total_su"] = qty
        item["cases"] = qty // item["pack_su"]
        item["loose_su"] = qty % item["pack_su"]
        warehouse = "HC" if item["group"] in HC_GROUPS else "PC" if item["group"] in PC_GROUPS else "KHÁC"
        sheets[warehouse].append(item)
    for items in sheets.values():
        items.sort(key=lambda x: (not x["group"].isdigit(), int(x["group"]) if x["group"].isdigit() else x["group"], x["sort_price"] is None,
                                  x["sort_price"] or 0, x["sku"]))
    used_lots = [x for x in lots if any(key[0] == x['print_lot_id'] for key in selected)]
    return {"vehicles": list(dict.fromkeys(vehicle(x) for x in used_lots)),
            "delivery_dates": sorted({day(x) for x in used_lots}),
            "lot_ids": [x['print_lot_id'] for x in used_lots], "lot_codes": [x["planned_lot_code"] for x in used_lots],
            "order_count": len(selected),
            "sheets": sheets}


@router.get("/vehicle-pick-list")
def vehicle_pick_list_preview(lot_ids: list[str] = Query(...)):
    c = conn()
    try:
        return vehicle_pick_list(c, lot_ids)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    finally:
        c.close()

@router.get("/vehicle-pick-orders")
def vehicle_pick_orders(lot_ids: list[str] = Query(...)):
    ids = list(dict.fromkeys(lot_ids))
    if not ids or len(ids) > 100:
        raise HTTPException(400, "Chọn từ 1 đến 100 lô")
    c = conn()
    try:
        marks = ','.join('?' for _ in ids)
        rows = [dict(r) for r in c.execute(f"""SELECT o.print_lot_id,o.loai_don,o.ma_don_nguon
          FROM qtgh_print_lot_order o WHERE o.print_lot_id IN ({marks})
          ORDER BY o.print_lot_id,o.loai_don,o.ma_don_nguon""", ids)]
        return {"rows": rows}
    finally:
        c.close()

@router.post("/vehicle-pick-list")
def vehicle_pick_list_selection(payload: dict = Body(...)):
    c = conn()
    try:
        return vehicle_pick_list(c, payload.get('lot_ids') or [], payload.get('orders') or [])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    finally:
        c.close()

@router.get("/audit")
def audit_rows(limit:int=200):
    limit=max(1,min(limit,1000))
    c=conn()
    rows=[dict(r) for r in c.execute("""
      SELECT * FROM qtgh_delivery_audit
      ORDER BY id DESC LIMIT ?
    """,(limit,)).fetchall()]
    c.close()
    return {"rows":rows}

def warehouse_lot_staff(c, lot_id):
    row = c.execute("""SELECT l.planned_delivery_staff_code, f.actual_delivery_staff_code
        FROM qtgh_print_lot l LEFT JOIN qtgh_delivery_finalization f
        ON f.print_lot_id=l.print_lot_id WHERE l.print_lot_id=?""", (lot_id,)).fetchone()
    code = str((row["actual_delivery_staff_code"] or row["planned_delivery_staff_code"] or "") if row else "").strip()
    staff, aliases = {}, {}
    for r in c.execute("SELECT category,business_key,payload_json FROM master_data_generic WHERE category IN ('dm02-staff','dm02a-staff-map')"):
        try:
            p = json.loads(r["payload_json"] or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(p, dict):
            continue
        if r["category"] == 'dm02-staff':
            key = str(p.get("MA_NV") or r["business_key"] or "").strip().upper()
            if key:
                staff[key] = p
        else:
            for k in ("MA_NGHIEP_VU", "MA_NV_NGHIEP_VU", "MA_MAY", "MA_NV_MAY"):
                key = str(p.get(k) or "").strip().upper()
                if key:
                    aliases[key] = str(p.get("MA_NV") or "").strip().upper()
    key = code.upper()
    person = staff.get(key) or staff.get(aliases.get(key, "")) or {}
    name = str(person.get("TEN_NV") or person.get("HO_TEN") or "").strip()
    return {"code": code, "name": name}


def warehouse_arrange_split(c, lot_ids):
    """Sum full cases from each lot's delivery sheet; keep its SU remainder separate."""
    combined = vehicle_pick_list(c, lot_ids, arrange=True)
    expected = {r["sku"]: r["total_su"] for rows in combined["sheets"].values() for r in rows}
    common = {w: {} for w in combined["sheets"]}
    loose_lots = []
    for lot_id in combined["lot_ids"]:
        lot = vehicle_pick_list(c, [lot_id], arrange=True)
        loose_sheets = {w: [] for w in lot["sheets"]}
        for warehouse, rows in lot["sheets"].items():
            for row in rows:
                # These are exactly the cases / loose_su columns on this lot's vehicle sheet.
                cases, remainder = divmod(row["total_su"], row["pack_su"])
                if cases:
                    item = common[warehouse].setdefault(row["sku"], dict(row, source_cases=0,
                        cases=0, source_loose_su=0, loose_cases=0, remaining_loose_su=0,
                        loose_su=0, total_su=0))
                    item["source_cases"] += cases
                    item["cases"] += cases
                    item["total_su"] += cases * row["pack_su"]
                if remainder:
                    loose_sheets[warehouse].append(dict(row, source_cases=0, cases=0,
                        source_loose_su=remainder, loose_cases=0,
                        remaining_loose_su=remainder, loose_su=remainder, total_su=remainder))
        lot["delivery_staff"] = warehouse_lot_staff(c, lot_id)
        lot["sheets"] = loose_sheets
        if any(loose_sheets.values()):
            loose_lots.append(lot)
    # Retain the original group / price / SKU order on the common sheets.
    combined["sheets"] = {w: [common[w][r["sku"]] for r in rows if r["sku"] in common[w]]
                          for w, rows in combined["sheets"].items()}
    actual = {sku: 0 for sku in expected}
    for part in [combined] + loose_lots:
        for rows in part["sheets"].values():
            for row in rows:
                actual[row["sku"]] += row["total_su"]
    if actual != expected:
        raise ValueError("Phiếu chẵn và phiếu lẻ không khớp tổng SU nguồn")
    combined["loose_lots"] = loose_lots
    combined["reconciliation"] = {"source_su": sum(expected.values()), "printed_su": sum(actual.values()), "matched": True}
    return combined


# VG_ARRANGE_LOTS_V1
@router.post("/warehouse-arrange-list")
def warehouse_arrange_list(payload: dict = Body(...)):
    c = conn()
    try:
        return warehouse_arrange_split(c, payload.get('lot_ids') or [])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    finally:
        c.close()
