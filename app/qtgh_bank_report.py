"""Settlement bank allocations. Reconciliation writes only to two dedicated tables."""
from pathlib import Path
from contextlib import closing
from datetime import date, datetime, timezone, timedelta
import json, sqlite3, io, zipfile
from xml.sax.saxutils import escape
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router=APIRouter(prefix='/api/qtgh-stable/ui04/bank-report', tags=['Mã Ngân Hàng'])
DB=Path(__file__).resolve().parents[1]/'data'/'miniapp.db'
STATUS={'CHUA_DOI_CHIEU':'Chưa đối chiếu','DA_KHOP':'Đã khớp','CHENH_LECH':'Chênh lệch'}
SCHEMA='''
CREATE TABLE IF NOT EXISTS qtgh_bank_reconciliation(
 draft_order_id INTEGER PRIMARY KEY, status TEXT NOT NULL,
 statement_date TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
 updated_by TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL,
 source_fingerprint TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS qtgh_bank_reconciliation_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, draft_order_id INTEGER NOT NULL,
 old_json TEXT NOT NULL, new_json TEXT NOT NULL,
 updated_by TEXT NOT NULL, updated_at TEXT NOT NULL);
'''

def has_table(c,name):
    return bool(c.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name=?',(name,)).fetchone())

def check_date(s):
    if s and date.fromisoformat(s).isoformat()!=s: raise ValueError('Ngày không hợp lệ.')
    return s

def fingerprints(r):
    return json.dumps([r['session_id'],r['amount'],r['bank_key'],r['txn'],r['staff']],ensure_ascii=False)

def rows(c):
    """One allocation per locked draft; never multiply money by SKU/session join."""
    banks={}
    if has_table(c,'qtgh_receiving_bank_account'):
        for x in c.execute('SELECT * FROM qtgh_receiving_bank_account'):
            b=dict(x);banks[str(b['id'])]=b
            # Account number lookup only when unambiguous across banks.
        groups={}
        for b in list(banks.values()): groups.setdefault(str(b['account_no']),[]).append(b)
        banks.update({k:v[0] for k,v in groups.items() if len(v)==1 and k not in banks})
    names={}
    if has_table(c,'master_data_generic'):
        for x in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category='dm02-staff'"):
            try: p=json.loads(x['payload_json'] or '{}')
            except (ValueError,TypeError): continue
            names[str(p.get('MA_NV') or x['business_key'] or '')]=str(p.get('TEN_NV') or p.get('HO_TEN') or p.get('TEN_NHAN_VIEN') or '')
    rec={}
    if has_table(c,'qtgh_bank_reconciliation'):
        rec={x['draft_order_id']:dict(x) for x in c.execute('SELECT * FROM qtgh_bank_reconciliation')}
    sources={}
    for x in c.execute('''SELECT s.* FROM qtgh_source_projection s
      WHERE COALESCE(s.source_batch_id,0)=(SELECT MAX(COALESCE(t.source_batch_id,0))
       FROM qtgh_source_projection t WHERE t.source_system=s.source_system AND t.ma_don_nguon=s.ma_don_nguon)
      ORDER BY s.id'''):
        x=dict(x);sources.setdefault((x['source_system'],x['ma_don_nguon']),[]).append(x)
    result=[];used=set()
    for x in c.execute('''SELECT d.*,se.id AS session_id,se.ma_phien_qt,se.ma_nvgh AS actual_staff,
      se.locked_at AS settled_at FROM qtgh_draft_order d
      JOIN qtgh_session_order so ON so.draft_order_id=d.id
      JOIN qtgh_session se ON se.id=so.session_id
      WHERE se.status='DA_KHOA' AND d.status='DA_KHOA' AND d.tien_ck_xac_nhan>0
      ORDER BY se.locked_at,d.id'''):
        d=dict(x);did=d['id']
        if did in used: raise ValueError('Đơn '+d['ma_don_nguon']+' thuộc nhiều phiên chốt; cần kiểm tra trước khi đối chiếu.')
        used.add(did);s=sources.get((d['source_system'],d['ma_don_nguon']),[])
        first=s[0] if s else {};warnings=[]
        if not s: warnings.append('Thiếu đơn nguồn')
        def unique(key):
            vals=sorted({str(v.get(key) or '').strip() for v in s if v.get(key)})
            if len(vals)>1: warnings.append('Đơn có nhiều '+key)
            return ', '.join(vals)
        key=str(d.get('bank_account') or '').strip();b=banks.get(key,{})
        if not b: warnings.append('Chưa xác định danh mục ngân hàng nhận')
        if not d.get('bank_txn_id'): warnings.append('Thiếu mã giao dịch')
        settled=str(d.get('settled_at') or d.get('locked_at') or '')
        if not settled: warnings.append('Thiếu thời gian chốt')
        staff=str(d.get('actual_staff') or '')
        r=dict(id=did,session_id=d['session_id'],source_system=d['source_system'],order=d['ma_don_nguon'],
          settled_at=settled,settlement_date=settled[:10],session=d['ma_phien_qt'],
          customer=first.get('ma_kh_chuan') or first.get('ma_kh_dms') or first.get('ma_kh_mbw') or '',
          customer_dms=first.get('ma_kh_dms') or '',customer_mbw=first.get('ma_kh_mbw') or '',
          customer_name=first.get('ten_kh') or '',lot=unique('ma_lo'),delivery_date=unique('ngay_giao'),
          staff=staff,staff_name=names.get(staff,''),bank_key=key,bank_name=b.get('bank_name',''),
          account=b.get('account_no') or key,account_name=b.get('account_name',''),
          txn=str(d.get('bank_txn_id') or ''),amount=int(d['tien_ck_xac_nhan']),warnings=warnings)
        v=rec.get(did,{})
        stale=bool(v and v.get('source_fingerprint')!=fingerprints(r))
        if stale: warnings.append('Dữ liệu quyết toán đã thay đổi; cần đối chiếu lại')
        r.update(status='CHUA_DOI_CHIEU' if stale else v.get('status','CHUA_DOI_CHIEU'),
          statement_date='' if stale else v.get('statement_date',''),note=v.get('note',''),
          updated_by=v.get('updated_by',''),updated_at=v.get('updated_at',''),version=v.get('version',0))
        r['fingerprint']=fingerprints(r)
        result.append(r)
    return result

def report(c,params):
    start=check_date(params.get('date_from',''));end=check_date(params.get('date_to',''))
    if start and end and start>end: raise ValueError('Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.')
    status=params.get('status','')
    if status and status not in STATUS: raise ValueError('Trạng thái không hợp lệ.')
    all_rows=rows(c)
    def contains(r,key,fields):
        q=params.get(key,'').strip().casefold()
        return not q or q in ' '.join(str(r.get(f) or '') for f in fields).casefold()
    selected=[r for r in all_rows if (not start or r['settlement_date']>=start)
      and (not end or r['settlement_date']<=end)
      and (not params.get('bank_key') or r['bank_key']==params['bank_key'])
      and (not status or r['status']==status)
      and contains(r,'staff',('staff','staff_name'))
      and contains(r,'customer',('customer','customer_name','customer_dms','customer_mbw'))
      and contains(r,'lot',('lot',)) and contains(r,'txn',('txn','order','session'))]
    return dict(rows=selected,count=len(selected),total=sum(r['amount'] for r in selected),
      status_totals={k:sum(r['amount'] for r in selected if r['status']==k) for k in STATUS},
      filters=dict(params),banks=[dict(key=k,label=' / '.join(filter(None,[r['bank_name'],r['account']])))
        for k,r in sorted({r['bank_key']:r for r in all_rows}.items()) if k],
      warning_count=sum(bool(r['warnings']) for r in selected))

def connect_read():
    c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('BEGIN');return c

@router.get('')
def get_report(request:Request):
    try:
        with closing(connect_read()) as c: return report(c,dict(request.query_params))
    except (ValueError,sqlite3.Error) as e: raise HTTPException(400,str(e))

def save_reconciliation(c,did,p,user):
    status=str(p.get('status') or '')
    if status not in STATUS: raise ValueError('Trạng thái không hợp lệ.')
    sd=check_date(str(p.get('statement_date') or ''));note=str(p.get('note') or '').strip()
    if len(note)>2000: raise ValueError('Ghi chú tối đa 2.000 ký tự.')
    if status=='DA_KHOP' and not sd: raise ValueError('Nhập ngày chuyển tiền trên sao kê trước khi xác nhận đã khớp.')
    if status=='CHENH_LECH' and not note: raise ValueError('Nhập ghi chú chênh lệch.')
    if sd and sd>datetime.now(timezone(timedelta(hours=7))).date().isoformat(): raise ValueError('Ngày trên sao kê không được ở tương lai.')
    c.execute('BEGIN IMMEDIATE')
    try:
        r=next((r for r in rows(c) if r['id']==did),None)
        if not r: raise ValueError('Không có khoản chuyển khoản đã chốt cho đơn này.')
        if p.get('version')!=r['version']: raise HTTPException(409,'Người khác đã cập nhật. Tải lại báo cáo trước khi lưu.')
        if p.get('fingerprint')!=fingerprints(r): raise HTTPException(409,'Dữ liệu quyết toán đã thay đổi. Tải lại báo cáo.')
        if status=='DA_KHOP' and any(w!='Dữ liệu quyết toán đã thay đổi; cần đối chiếu lại' for w in r['warnings']): raise ValueError('Cần kiểm tra cảnh báo dữ liệu trước khi xác nhận đã khớp.')
        old=dict(c.execute('SELECT * FROM qtgh_bank_reconciliation WHERE draft_order_id=?',(did,)).fetchone() or {})
        now=datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
        new=dict(draft_order_id=did,status=status,statement_date=sd,note=note,updated_by=user,updated_at=now,
                 version=r['version']+1,source_fingerprint=fingerprints(r))
        c.execute('''INSERT INTO qtgh_bank_reconciliation VALUES(:draft_order_id,:status,:statement_date,:note,:updated_by,:updated_at,:version,:source_fingerprint)
        ON CONFLICT(draft_order_id) DO UPDATE SET status=excluded.status,statement_date=excluded.statement_date,
         note=excluded.note,updated_by=excluded.updated_by,updated_at=excluded.updated_at,version=excluded.version,
         source_fingerprint=excluded.source_fingerprint''',new)
        c.execute('INSERT INTO qtgh_bank_reconciliation_log(draft_order_id,old_json,new_json,updated_by,updated_at) VALUES(?,?,?,?,?)',
          (did,json.dumps(old,ensure_ascii=False),json.dumps(new,ensure_ascii=False),user,now))
        c.commit();return new
    except Exception:
        c.rollback();raise

@router.post('/{did}/reconcile')
async def reconcile(did:int,request:Request):
    # Same explicit UI04 permission as middleware, also supports cookie sessions.
    from .security import get_user_by_token
    from .access_control_v1 import allowed
    auth=request.headers.get('authorization','')
    token=auth.split(' ',1)[1].strip() if auth.lower().startswith('bearer ') else request.cookies.get('vg_session')
    user=get_user_by_token(token) if token else None
    if not user: raise HTTPException(401,'Chưa đăng nhập')
    if not allowed(user,'QTGH_UI04','POST'): raise HTTPException(403,'Cần quyền sửa UI04 để xác nhận đối chiếu.')
    try:
        p=await request.json()
        if not isinstance(p,dict): raise ValueError('Dữ liệu đối chiếu không hợp lệ.')
        with closing(sqlite3.connect(DB.resolve().as_uri()+'?mode=rw',uri=True,timeout=15)) as c:
            c.row_factory=sqlite3.Row
            return save_reconciliation(c,did,p,user['username'])
    except (ValueError,sqlite3.Error) as e: raise HTTPException(400,str(e))

COLUMNS=[('settled_at','Thời gian quyết toán'),('statement_date','Ngày trên sao kê'),('customer','Mã KH'),
 ('customer_dms','Mã KH DMS'),('customer_mbw','Mã KH MBW'),('customer_name','Tên KH'),('order','Đơn nguồn'),
 ('lot','Mã lô'),('session','Phiếu QT'),('staff','Mã NVGH'),('staff_name','Tên NVGH'),('bank_name','Ngân hàng nhận'),
 ('account','Tài khoản nhận'),('txn','Mã giao dịch'),('amount','Số tiền CK'),('status','Đối chiếu'),
 ('note','Ghi chú'),('updated_by','Người đối chiếu'),('updated_at','Thời gian đối chiếu'),('warnings','Cảnh báo')]

def xlsx(data):
    def col(n):
        s=''
        while n: n,k=divmod(n-1,26);s=chr(65+k)+s
        return s
    def row(values,i):
        cells=[]
        for n,v in enumerate(values,1):
            ref=col(n)+str(i)
            if isinstance(v,int):cells.append(f'<c r="{ref}" t="n"><v>{v}</v></c>')
            else:
                v=''.join(ch for ch in str(v or '') if ord(ch)>=32 or ch in '\n\t')
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(v)}</t></is></c>')
        return '<row>'+''.join(cells)+'</row>'
    vals=[['CTY CP Vĩnh Giang — Mã Ngân Hàng'],['Bộ lọc: '+json.dumps(data['filters'],ensure_ascii=False)],
      [label for _,label in COLUMNS]]
    for r in data['rows']:
        vals.append([STATUS.get(r[k],r[k]) if k=='status' else '; '.join(r[k]) if k=='warnings' else r[k] for k,_ in COLUMNS])
    vals.append(['TỔNG']+['']*13+[data['total']])
    xml='<?xml version="1.0" encoding="UTF-8"?>'
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',xml+'''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>''')
        z.writestr('_rels/.rels',xml+'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>''')
        z.writestr('xl/workbook.xml',xml+f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Ma Ngan Hang" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',xml+'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>''')
        z.writestr('xl/worksheets/sheet1.xml',xml+f'<worksheet xmlns="{ns}"><cols><col min="1" max="20" width="22" customWidth="1"/></cols><sheetData>'+''.join(row(v,i) for i,v in enumerate(vals,1))+f'</sheetData><autoFilter ref="A3:T{len(vals)-1}"/></worksheet>')
    return buf.getvalue()

@router.get('/export.xlsx')
def export(request:Request):
    try:
        with closing(connect_read()) as c: data=report(c,dict(request.query_params))
        return Response(xlsx(data),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          headers={'Content-Disposition':'attachment; filename="MA_NGAN_HANG.xlsx"'})
    except (ValueError,sqlite3.Error) as e: raise HTTPException(400,str(e))
