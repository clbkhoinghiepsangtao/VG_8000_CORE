"""UI10 monetary adjustment pilot. Original locked documents remain immutable."""
from datetime import datetime
from pathlib import Path
import sqlite3
import re

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/qtgh-stable/ui10/money", tags=["QTGH UI10 money Candidate"])
DB = Path(__file__).resolve().parents[1] / "data" / "miniapp.db"


def connect():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS qtgh_money_adjust_candidate(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_no TEXT UNIQUE,
      source_type TEXT NOT NULL CHECK(source_type IN ('ORDER','SESSION')),
      source_id INTEGER NOT NULL,
      source_ref TEXT NOT NULL,
      case_ref TEXT,
      delta_amount INTEGER NOT NULL CHECK(delta_amount<>0),
      before_amount INTEGER NOT NULL,
      after_amount INTEGER NOT NULL CHECK(after_amount>=0),
      reason TEXT NOT NULL,
      note TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_at TEXT NOT NULL,
      submitted_at TEXT,
      approved_at TEXT,
      approved_by TEXT
    );
    CREATE INDEX IF NOT EXISTS ix_qtgh_money_adjust_source_candidate
      ON qtgh_money_adjust_candidate(source_type,source_id,status);
    CREATE TABLE IF NOT EXISTS qtgh_money_effect_candidate(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_id INTEGER NOT NULL,
      party TEXT NOT NULL CHECK(party IN ('KH','NVGH')),
      effect_type TEXT NOT NULL CHECK(effect_type IN ('DEBT_ADD','DEBT_REDUCE','CREDIT')),
      debt_id INTEGER,
      amount INTEGER NOT NULL CHECK(amount>0),
      FOREIGN KEY(adjustment_id) REFERENCES qtgh_money_adjust_candidate(id)
    );
    """)
    c.close()


def now():
    return datetime.now().isoformat(timespec="seconds")


def exact_money(value):
    if isinstance(value, bool):
        raise ValueError("Số tiền phải là số nguyên VND")
    try:
        v = int(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError("Số tiền phải là số nguyên VND")
    if v == 0:
        raise ValueError("Số điều chỉnh phải khác 0")
    return v


def row(c, table, idv):
    return c.execute(f"SELECT * FROM {table} WHERE id=?", (idv,)).fetchone()


def order_session(c, did):
    return c.execute("""SELECT se.id FROM qtgh_session se
      JOIN qtgh_session_order so ON so.session_id=se.id
      WHERE so.draft_order_id=? AND se.status='DA_KHOA'
      ORDER BY se.id LIMIT 1""", (did,)).fetchone()


def current(c, source_type, source_id):
    if source_type == "ORDER":
        d = row(c, "qtgh_draft_order", source_id)
        if not d or d["status"] != "DA_KHOA" or not order_session(c, source_id):
            raise ValueError("Chỉ điều chỉnh đơn thuộc phiên đã khóa")
        base = int(d["so_phai_thu_sau_qt"] or 0)
        ref = str(d["ma_don_nguon"])
        nv = c.execute("""SELECT ma_nvgh FROM qtgh_session
          WHERE id=?""", (order_session(c, source_id)[0],)).fetchone()[0]
    elif source_type == "SESSION":
        d = row(c, "qtgh_session", source_id)
        if not d or d["status"] != "DA_KHOA":
            raise ValueError("Chỉ điều chỉnh phiên đã khóa")
        receipts = c.execute("""SELECT * FROM qtgh_cash_receipt
          WHERE source_id=? AND source_type IN ('QT_PHIEN','QT_PHIEN_NVGH')""",
          (source_id,)).fetchall()
        if len(receipts) > 1:
            raise ValueError("Phiên có nhiều phiếu thu gốc; cần đối chiếu trước")
        base = int(receipts[0]["expected_amount"] or 0) if receipts else 0
        ref = str(d["ma_phien_qt"])
        nv = str(d["ma_nvgh"] or "")
        # Order adjustments are already part of the employee's obligation.
        base += int(c.execute("""SELECT COALESCE(SUM(a.delta_amount),0)
          FROM qtgh_money_adjust_candidate a JOIN qtgh_session_order so
            ON so.draft_order_id=a.source_id
          WHERE so.session_id=? AND a.source_type='ORDER' AND a.status='DA_DUYET'""",
          (source_id,)).fetchone()[0])
    else:
        raise ValueError("Loại chứng từ tiền không hợp lệ")
    adjustment = int(c.execute("""SELECT COALESCE(SUM(delta_amount),0)
      FROM qtgh_money_adjust_candidate
      WHERE source_type=? AND source_id=? AND status='DA_DUYET'""",
      (source_type, source_id)).fetchone()[0])
    return {"source_type": source_type, "source_id": source_id,
            "source_ref": ref, "ma_nvgh": nv, "base_amount": base,
            "current_amount": base + adjustment}


def _debt_add(c, adjustment_id, party, amount, source_id, session_id):
    if party == "KH":
        d = row(c, "qtgh_draft_order", source_id)
        src = c.execute("""SELECT MAX(ma_kh_chuan) ma_kh_chuan,MAX(ma_nvgh) ma_nvgh
          FROM qtgh_source_projection WHERE source_system=? AND ma_don_nguon=?""",
          (d["source_system"],d["ma_don_nguon"])).fetchone()
        # The new receivable is a separate line; original debt amount is intact.
        cur = c.execute("""INSERT INTO qtgh_customer_debt
          (draft_order_id,ma_kh_chuan,ma_don_nguon,ma_nvgh,
           original_amount,balance,status,created_at)
          VALUES(?,?,?,?,?,?,'CON_NO',?)""",
          (source_id,src["ma_kh_chuan"],d["ma_don_nguon"],src["ma_nvgh"],
           amount,amount,now()))
        debt_id = cur.lastrowid
    else:
        session = row(c,"qtgh_session",session_id)
        receipt = c.execute("""SELECT id FROM qtgh_cash_receipt
          WHERE source_id=? AND source_type IN ('QT_PHIEN','QT_PHIEN_NVGH')
          ORDER BY id LIMIT 1""",(session_id,)).fetchone()
        # A positive money adjustment is a receivable; it does not make a cash receipt.
        cur = c.execute("""INSERT INTO qtgh_employee_debt
          (cash_receipt_id,ma_nvgh,original_amount,balance,status,created_at)
          VALUES(?,?,?,?,'CON_NO',?)""",
          (receipt[0] if receipt else 0,session["ma_nvgh"],amount,amount,now()))
        debt_id = cur.lastrowid
    c.execute("""INSERT INTO qtgh_money_effect_candidate
      (adjustment_id,party,effect_type,debt_id,amount)
      VALUES(?,?,'DEBT_ADD',?,?)""",(adjustment_id,party,debt_id,amount))


def _debt_reduce(c, adjustment_id, party, amount, source_id, session_id):
    if party == "KH":
        debts = c.execute("""SELECT * FROM qtgh_customer_debt
          WHERE draft_order_id=? AND balance>0 ORDER BY id DESC""",(source_id,)).fetchall()
        table = "qtgh_customer_debt"
    else:
        s = row(c,"qtgh_session",session_id)
        debts = c.execute("""SELECT e.* FROM qtgh_employee_debt e
          WHERE e.ma_nvgh=? AND e.balance>0 AND EXISTS
            (SELECT 1 FROM qtgh_cash_receipt r WHERE r.id=e.cash_receipt_id
             AND r.source_id=? AND r.source_type IN ('QT_PHIEN','QT_PHIEN_NVGH'))
          ORDER BY e.id DESC""",(s["ma_nvgh"],session_id)).fetchall()
        table = "qtgh_employee_debt"
    remain = amount
    for debt in debts:
        used = min(remain,int(debt["balance"]))
        c.execute(f"UPDATE {table} SET balance=balance-?,status=? WHERE id=?",
                  (used,"DA_THU_DU" if used==int(debt["balance"]) else "CON_NO",debt["id"]))
        c.execute("""INSERT INTO qtgh_money_effect_candidate
          (adjustment_id,party,effect_type,debt_id,amount)
          VALUES(?,?,'DEBT_REDUCE',?,?)""",(adjustment_id,party,debt["id"],used))
        remain -= used
        if remain == 0:
            break
    if remain:
        c.execute("""INSERT INTO qtgh_money_effect_candidate
          (adjustment_id,party,effect_type,amount)
          VALUES(?,?,'CREDIT',?)""",(adjustment_id,party,remain))


def create(c, x):
    source_type=str(x.get("source_type") or "").strip()
    source_id=int(x.get("source_id"))
    delta=exact_money(x.get("delta_amount"))
    reason=str(x.get("reason") or "").strip()
    if not reason:
        raise ValueError("Bắt buộc nhập lý do")
    p=current(c,source_type,source_id)
    after=p["current_amount"]+delta
    if after<0:
        raise ValueError("Tiền sau điều chỉnh không được âm")
    cur=c.execute("""INSERT INTO qtgh_money_adjust_candidate
      (source_type,source_id,source_ref,case_ref,delta_amount,before_amount,
       after_amount,reason,note,status,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,'NHAP',?)""",
      (source_type,source_id,p["source_ref"],None,
       delta,p["current_amount"],after,reason,str(x.get("note") or "").strip(),now()))
    aid=cur.lastrowid
    day=datetime.now().strftime("%Y%m%d")
    number=f"DCT-{day}-{aid:06d}"
    source_code=re.sub(r"[^A-Z0-9]+","",p["source_ref"].upper())[:32] or str(source_id)
    case_ref=f"VV-{day}-{'D' if source_type=='ORDER' else 'P'}-{source_code}-{aid:06d}"
    c.execute("UPDATE qtgh_money_adjust_candidate SET adjustment_no=?,case_ref=? WHERE id=?",(number,case_ref,aid))
    return dict(row(c,"qtgh_money_adjust_candidate",aid))


def approve(c, aid, approver):
    a=row(c,"qtgh_money_adjust_candidate",aid)
    if not a or a["status"]!="CHO_DUYET":
        raise ValueError("Chỉ phiếu chờ duyệt mới được duyệt")
    p=current(c,a["source_type"],a["source_id"])
    if p["current_amount"]!=a["before_amount"]:
        raise ValueError("Tiền hiện tại đã đổi; cần lập lại phiếu")
    if a["after_amount"]<0:
        raise ValueError("Tiền sau điều chỉnh không được âm")
    sid=a["source_id"] if a["source_type"]=="SESSION" else order_session(c,a["source_id"])[0]
    if a["source_type"]=="ORDER" and current(c,"SESSION",sid)["current_amount"]+a["delta_amount"]<0:
        raise ValueError("Tiền hiệu lực của phiên NVGH không được âm")
    duplicate=c.execute("""SELECT other.id FROM qtgh_money_adjust_candidate other
      WHERE other.id<>? AND other.status='DA_DUYET' AND other.case_ref=?
        AND ((other.source_type='SESSION' AND other.source_id=?)
          OR (other.source_type='ORDER' AND EXISTS
            (SELECT 1 FROM qtgh_session_order so
             WHERE so.session_id=? AND so.draft_order_id=other.source_id)))
      LIMIT 1""",(aid,a["case_ref"],sid,sid)).fetchone()
    if duplicate:
        raise ValueError("Vụ việc này đã có phiếu tiền được duyệt trong cùng phiên; tránh cộng chênh lệch hai lần")
    if a["source_type"]=="ORDER":
        party_effects=("KH","NVGH")
    else:
        party_effects=("NVGH",)
    for party in party_effects:
        if a["delta_amount"]>0:
            _debt_add(c,aid,party,a["delta_amount"],a["source_id"],sid)
        else:
            _debt_reduce(c,aid,party,-a["delta_amount"],a["source_id"],sid)
    c.execute("""UPDATE qtgh_money_adjust_candidate SET status='DA_DUYET',
      approved_at=?,approved_by=? WHERE id=?""",(now(),approver,aid))
    return {"adjustment":dict(row(c,"qtgh_money_adjust_candidate",aid)),
            "effects":[dict(r) for r in c.execute(
              "SELECT * FROM qtgh_money_effect_candidate WHERE adjustment_id=?",(aid,))]}


@router.get("/documents")
def documents(q:str=""):
    c=connect()
    try:
        rows=[]
        needle="%"+q.strip()+"%"
        for t, table in (("ORDER","qtgh_draft_order"),("SESSION","qtgh_session")):
            if t=="ORDER" and q.strip():
                ids=c.execute("""SELECT d.id FROM qtgh_draft_order d
                  WHERE d.status='DA_KHOA' AND
                    (d.ma_don_nguon LIKE ? OR EXISTS
                      (SELECT 1 FROM qtgh_session_order so JOIN qtgh_session s
                       ON s.id=so.session_id WHERE so.draft_order_id=d.id
                       AND s.ma_nvgh LIKE ?))
                  ORDER BY d.id DESC LIMIT 300""",(needle,needle))
            elif t=="SESSION" and q.strip():
                ids=c.execute("""SELECT id FROM qtgh_session
                  WHERE status='DA_KHOA' AND (ma_phien_qt LIKE ? OR ma_nvgh LIKE ?)
                  ORDER BY id DESC LIMIT 300""",(needle,needle))
            else:
                ids=c.execute(f"SELECT id FROM {table} WHERE status='DA_KHOA' ORDER BY id DESC LIMIT 100")
            for r in ids:
                try:
                    p=current(c,t,r["id"])
                except ValueError:
                    continue
                if not q or q.upper() in (p["source_ref"]+" "+p["ma_nvgh"]).upper():
                    rows.append(p)
        return {"rows":rows}
    finally:
        c.close()


@router.get("/adjustments")
def adjustments(q:str=""):
    c=connect()
    try:
        needle="%"+q.strip()+"%"
        return {"rows":[dict(r) for r in c.execute(
          """SELECT * FROM qtgh_money_adjust_candidate
          WHERE case_ref LIKE ? OR adjustment_no LIKE ? OR source_ref LIKE ? OR reason LIKE ?
          ORDER BY id DESC LIMIT 300""",(needle,needle,needle,needle))],
          "effects":[dict(r) for r in c.execute("""SELECT a.adjustment_no,a.source_ref,
            e.party,e.effect_type,e.debt_id,e.amount FROM qtgh_money_effect_candidate e
            JOIN qtgh_money_adjust_candidate a ON a.id=e.adjustment_id
            ORDER BY e.id DESC LIMIT 500""")],
          "credits":[dict(r) for r in c.execute("""SELECT a.adjustment_no,a.source_ref,
            e.party,e.amount FROM qtgh_money_effect_candidate e
            JOIN qtgh_money_adjust_candidate a ON a.id=e.adjustment_id
            WHERE e.effect_type='CREDIT' ORDER BY e.id DESC LIMIT 300""")]}
    finally:
        c.close()


@router.post("/adjustments")
async def create_api(request:Request):
    c=connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        result=create(c,await request.json())
        c.commit()
        return result
    except (ValueError,TypeError,sqlite3.Error) as e:
        c.rollback();raise HTTPException(400,str(e))
    finally:
        c.close()


@router.post("/adjustments/{aid}/submit")
def submit_api(aid:int):
    c=connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        changed=c.execute("""UPDATE qtgh_money_adjust_candidate
          SET status='CHO_DUYET',submitted_at=? WHERE id=? AND status='NHAP'""",
          (now(),aid)).rowcount
        if changed!=1:
            raise ValueError("Chỉ phiếu nháp mới được gửi duyệt")
        c.commit();return {"ok":True}
    except (ValueError,sqlite3.Error) as e:
        c.rollback();raise HTTPException(400,str(e))
    finally:
        c.close()


@router.post("/adjustments/{aid}/cancel")
def cancel_api(aid:int):
    c=connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        changed=c.execute("""UPDATE qtgh_money_adjust_candidate SET status='DA_HUY'
          WHERE id=? AND status='NHAP'""",(aid,)).rowcount
        if changed!=1:
            raise ValueError("Chỉ phiếu nháp mới được hủy")
        c.commit();return {"ok":True}
    except (ValueError,sqlite3.Error) as e:
        c.rollback();raise HTTPException(400,str(e))
    finally:
        c.close()


@router.post("/adjustments/{aid}/approve")
async def approve_api(aid:int,request:Request):
    from .access_control_v1 import auth_user
    user=auth_user(request.headers.get("authorization"))
    if str(user.get("role") or "").upper()!="KE_TOAN_TRUONG":
        raise HTTPException(403,"Chỉ Kế toán trưởng được duyệt điều chỉnh tiền")
    approver=user["username"]
    c=connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        result=approve(c,aid,approver)
        c.commit();return result
    except (ValueError,sqlite3.Error) as e:
        c.rollback();raise HTTPException(400,str(e))
    finally:
        c.close()
