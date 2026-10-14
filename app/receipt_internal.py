"""Persistent receipt numbers and internal receipt print data; no ledger writes."""
import datetime
import html
import json
from pathlib import Path


def migrate(c):
    cols={r[1] for r in c.execute('PRAGMA table_info(qtgh_cash_receipt)')}
    if not cols:
        raise ValueError('Missing qtgh_cash_receipt')
    if 'receipt_no' not in cols:
        c.execute('ALTER TABLE qtgh_cash_receipt ADD COLUMN receipt_no TEXT')
    c.execute('CREATE TABLE IF NOT EXISTS receipt_daily_sequence(day TEXT PRIMARY KEY, last_seq INTEGER NOT NULL CHECK(last_seq>0))')
    c.execute('''CREATE TABLE IF NOT EXISTS receipt_number_registry(
      receipt_id INTEGER PRIMARY KEY, receipt_no TEXT NOT NULL UNIQUE,
      day TEXT NOT NULL, seq INTEGER NOT NULL, assigned_at TEXT NOT NULL,
      UNIQUE(day,seq))''')
    # Backfill in creation order; registry remains even if a receipt is cancelled/deleted.
    rows=c.execute('SELECT id,created_at,receipt_no FROM qtgh_cash_receipt ORDER BY created_at,id').fetchall()
    today=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=7)).date().isoformat()
    for rid,created,existing in rows:
        reg=c.execute('SELECT receipt_no FROM receipt_number_registry WHERE receipt_id=?',(rid,)).fetchone()
        if reg:
            if existing!=reg[0]:
                c.execute('UPDATE qtgh_cash_receipt SET receipt_no=? WHERE id=?',(reg[0],rid))
            continue
        if existing:
            raise ValueError('Unregistered receipt number; manual review required')
        day=str(created or '')[:10]
        try:datetime.date.fromisoformat(day)
        except ValueError:day=today
        c.execute('INSERT INTO receipt_daily_sequence(day,last_seq) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET last_seq=last_seq+1',(day,))
        seq=c.execute('SELECT last_seq FROM receipt_daily_sequence WHERE day=?',(day,)).fetchone()[0]
        no=day[2:].replace('-','_')+'_'+str(seq).zfill(3)
        c.execute("INSERT INTO receipt_number_registry VALUES(?,?,?,?,datetime('now'))",(rid,no,day,seq))
        c.execute('UPDATE qtgh_cash_receipt SET receipt_no=? WHERE id=?',(no,rid))
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_cash_receipt_no ON qtgh_cash_receipt(receipt_no) WHERE receipt_no IS NOT NULL')
    c.execute('''CREATE TRIGGER IF NOT EXISTS receipt_number_assign AFTER INSERT ON qtgh_cash_receipt
    BEGIN
      INSERT INTO receipt_daily_sequence(day,last_seq) VALUES(date('now','+7 hours'),1)
        ON CONFLICT(day) DO UPDATE SET last_seq=last_seq+1;
      INSERT INTO receipt_number_registry(receipt_id,receipt_no,day,seq,assigned_at)
        SELECT NEW.id, substr(day,3,2)||'_'||substr(day,6,2)||'_'||substr(day,9,2)||'_'||printf('%03d',last_seq), day,last_seq,datetime('now')
        FROM receipt_daily_sequence WHERE day=date('now','+7 hours');
      UPDATE qtgh_cash_receipt SET receipt_no=(SELECT receipt_no FROM receipt_number_registry WHERE receipt_id=NEW.id) WHERE id=NEW.id;
    END''')
    c.execute('''CREATE TRIGGER IF NOT EXISTS receipt_number_immutable BEFORE UPDATE OF receipt_no ON qtgh_cash_receipt
      WHEN OLD.receipt_no IS NOT NULL AND NEW.receipt_no IS NOT OLD.receipt_no
      BEGIN SELECT RAISE(ABORT,'Receipt number is immutable'); END''')
    for op in ('UPDATE','DELETE'):
        c.execute(f'''CREATE TRIGGER IF NOT EXISTS receipt_registry_no_{op.lower()} BEFORE {op} ON receipt_number_registry
          BEGIN SELECT RAISE(ABORT,'Receipt number registry is permanent'); END''')


_DIGITS=['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín']
def _triple(n,full=False):
    h,t,u=n//100,(n//10)%10,n%10
    out=[]
    if h or full:out += [_DIGITS[h],'trăm']
    if t>=2:out += [_DIGITS[t],'mươi']
    elif t==1:out += ['mười']
    elif u and (h or full):out += ['lẻ']
    if u:out += ['mốt' if u==1 and t>=2 else 'lăm' if u==5 and t else _DIGITS[u]]
    return ' '.join(out)

def money_words(amount):
    n=int(amount)
    if n==0:return 'Không đồng.'
    sign='Âm ' if n<0 else '';n=abs(n);groups=[]
    while n:groups.append(n%1000);n//=1000
    units=['','nghìn','triệu','tỷ','nghìn tỷ','triệu tỷ']
    parts=[]
    for i in range(len(groups)-1,-1,-1):
        if groups[i]:parts.append(_triple(groups[i],bool(parts))+(' '+units[i] if i else ''))
    text=sign+' '.join(parts)+' đồng.'
    return text[0].upper()+text[1:]

def _dict_row(c,table,where,args):
    # Table names are hard-coded internal callers, never request input.
    if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():return {}
    row=c.execute('SELECT * FROM '+table+' WHERE '+where,args).fetchone()
    if not row:return {}
    return dict(zip([x[1] for x in c.execute('PRAGMA table_info('+table+')')],row))

def print_data(c,rid):
    r=_dict_row(c,'qtgh_cash_receipt','id=?',(rid,))
    if not r:raise ValueError('Không tìm thấy phiếu thu')
    if not r.get('receipt_no'):raise ValueError('Phiếu chưa được cấp số; cần cài cập nhật phiếu thu')
    staff={}
    if c.execute("SELECT 1 FROM sqlite_master WHERE name='master_data_generic'").fetchone():
        for row in c.execute("SELECT payload_json FROM master_data_generic WHERE category='dm02-staff'"):
            try:p=json.loads(row[0] or '{}')
            except (ValueError,TypeError):continue
            if str(p.get('MA_NV') or '').strip().upper()==str(r.get('ma_nvgh') or '').strip().upper():staff=p;break
    r['payer_name']=r.get('payer_name') or staff.get('TEN_NV') or staff.get('HO_TEN') or staff.get('TEN_NHAN_VIEN') or ''
    r['payer_address']=r.get('payer_address') or staff.get('DIA_CHI') or ''
    kind=r.get('source_type') or r.get('receipt_kind') or ''
    reasons={'QT_PHIEN_NVGH':'Nộp tiền thu bán hàng theo quyết toán giao hàng.','QT_DON':'Nộp tiền thu bán hàng theo quyết toán giao hàng.','THU_NO_KH':'Nộp tiền thu công nợ khách hàng.','THU_NO_NVGH':'Nộp tiền thanh toán công nợ nhân viên.'}
    r['reason']=r.get('description') or r.get('content') or reasons.get(kind,'Nộp tiền theo chứng từ '+str(kind)+'.')
    sid=r.get('source_id');refs=[];count=None
    if kind=='QT_PHIEN_NVGH':
        se=_dict_row(c,'qtgh_session','id=?',(sid,))
        if se.get('ma_lo'):refs.append('Lô '+str(se['ma_lo']))
        refs.append('Phiếu QT '+str(se.get('ma_phien_qt') or '#'+str(sid)))
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='qtgh_session_order'").fetchone():count=c.execute('SELECT COUNT(*) FROM qtgh_session_order WHERE session_id=?',(sid,)).fetchone()[0]
    elif kind=='QT_DON':
        draft=_dict_row(c,'qtgh_draft_order','id=?',(sid,))
        if draft.get('ma_don_nguon'):refs.append('Đơn '+str(draft['ma_don_nguon']))
        if draft.get('ma_lo'):refs.append('Lô '+str(draft['ma_lo']))
        refs.append('Phiếu QT #'+str(sid));count=1
    elif kind=='THU_NO_KH':refs.append('Phiên thu nợ khách hàng #'+str(sid))
    elif kind=='THU_NO_NVGH':refs.append('Phiên thu nợ nhân viên #'+str(sid))
    else:refs.append(str(kind)+' #'+str(sid))
    r['source_reference']=' / '.join(refs);r['document_count']=count
    r['shortage']=max(0,int(r.get('expected_amount') or 0)-int(r.get('actual_amount') or 0))
    r['amount_words']=money_words(int(r.get('actual_amount') or 0))
    r['print_html']=render(r)
    return r


def render(r):
    template=Path(__file__).with_name('receipt_internal_template.html').read_text(encoding='utf-8')
    day=str(r.get('created_at') or '')[:10]
    try:
        d=datetime.date.fromisoformat(day);date_label=f'Ngày {d.day:02d} tháng {d.month:02d} năm {d.year}'
    except ValueError:date_label='Ngày lập: chưa có dữ liệu'
    resolution={'NOP_SAU':'Nộp sau','TRU_LUONG':'Trừ lương','XIN_Y_KIEN_LANH_DAO':'Xin ý kiến lãnh đạo','XIN_Y_KIEN':'Xin ý kiến lãnh đạo'}
    actual=int(r.get('actual_amount') or 0)
    received=str(r.get('received_at') or r.get('locked_at') or '')
    if received:
        try:received=datetime.datetime.fromisoformat(received).strftime('%d/%m/%Y %H:%M:%S')
        except ValueError:pass
    values={'receipt_no':r['receipt_no'],'date_label':date_label,'payer_name':r.get('payer_name') or '........................................',
      'staff_code':r.get('ma_nvgh') or r.get('payer_code') or '', 'payer_address':r.get('payer_address') or '................................................................................',
      'reason':r['reason'],'actual':f'{actual:,}'.replace(',','.'),'amount_words':r['amount_words'],
      'document_count':r.get('document_count') if r.get('document_count') is not None else '............',
      'source_reference':r['source_reference'],'expected':f"{int(r.get('expected_amount') or 0):,}".replace(',','.'),
      'shortage':f"{r['shortage']:,}".replace(',','.'),'resolution':resolution.get(r.get('resolution_code'),r.get('resolution_code') or 'Không phát sinh'),
      'note':r.get('resolution_note') or r.get('note') or '', 'received_at':received or 'Chưa thu tiền',
      'received_words':r['amount_words'] if received else 'Chưa thu tiền.',
      'status_note':'PHIẾU CHỜ THU - chưa xác nhận nhận tiền' if r.get('status')=='CHO_THU' else ('PHIẾU ĐÃ HỦY' if str(r.get('status') or '').upper() in ('HUY','DA_HUY','CANCELLED') else '')}
    for key,value in values.items():template=template.replace('{{'+key+'}}',html.escape(str(value)))
    return template
