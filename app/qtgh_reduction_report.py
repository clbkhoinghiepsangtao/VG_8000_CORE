"""Read-only, source-order reconciliation. Never posts accounting entries."""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from contextlib import closing
from decimal import Decimal, ROUND_HALF_UP
import sqlite3, json

router = APIRouter(prefix='/api/qtgh-stable/ui04/reduction-report', tags=['Chốt giảm trừ cuối đơn'])
DB = Path(__file__).resolve().parents[1] / 'data' / 'miniapp.db'

def dec(v):
    return Decimal(str(v or 0))

def money(v):
    return int(dec(v).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

FIELDS = ('original_due','ck_original','display_original','accum_original','returned_goods_vat',
          'ck_recovered','display_recovered','accum_recovered','reduction_due','final_due')

def total(rows):
    return dict(count=len(rows), **{k:sum(r.get(k,0) for r in rows) for k in FIELDS})

def build(c, lot, day, session_id=None, selected=None):
    # Stable identity: same lot on same delivery date. No employee filter may remove orders.
    src = [dict(r) for r in c.execute('''SELECT s.* FROM qtgh_source_projection s
      WHERE s.source_system='DMS_MBW' AND s.ma_lo=? AND s.ngay_giao=?
      AND COALESCE(s.source_batch_id,0)=(SELECT MAX(COALESCE(s2.source_batch_id,0))
        FROM qtgh_source_projection s2 WHERE s2.source_system=s.source_system
          AND s2.ma_don_nguon=s.ma_don_nguon)
      ORDER BY s.source_row_no,s.id''',(lot,day))]
    if not src:
        raise ValueError('Không có đơn nguồn trong đúng lô và ngày giao đã chọn.')
    groups={}
    for r in src: groups.setdefault(r['ma_don_nguon'],[]).append(r)
    drafts={r['ma_don_nguon']:dict(r) for r in c.execute("SELECT * FROM qtgh_draft_order WHERE source_system='DMS_MBW'") if r['ma_don_nguon'] in groups}
    history={}
    for r in c.execute('''SELECT d.ma_don_nguon,se.id,se.ma_phien_qt,se.locked_at,se.ma_nvgh
      FROM qtgh_session_order so JOIN qtgh_session se ON se.id=so.session_id
      JOIN qtgh_draft_order d ON d.id=so.draft_order_id
      WHERE se.status='DA_KHOA' AND d.source_system='DMS_MBW' ORDER BY se.id'''):
        if r['ma_don_nguon'] in groups:
            if r['ma_don_nguon'] in history:
                raise ValueError('Đơn bị chốt trùng phiên; cần kiểm tra trước khi lập báo cáo.')
            history[r['ma_don_nguon']]=dict(r)
    sessions={v['id']:v for v in history.values()}
    ordered=sorted(sessions)
    session=None
    if session_id is not None:
        if session_id not in sessions: raise ValueError('Lần quyết toán không thuộc lô này.')
        session=sessions[session_id]
        before={o for o,h in history.items() if h['id']<session_id}
        current={o for o,h in history.items() if h['id']==session_id}
        nth=ordered.index(session_id)+1
    else:
        before=set(history)
        current=set(selected or [])
        if not current: raise ValueError('Chọn các đơn đã đi giao để lập bản đối chiếu trước chốt.')
        if not current.issubset(groups): raise ValueError('Có đơn được chọn không thuộc đúng lô/ngày giao này.')
        if before & current: raise ValueError('Có đơn đã chốt ở lần trước; không được tính lại.')
        nth=len(ordered)+1
    staff_codes=sorted({str((session or {}).get('ma_nvgh') or rows[0].get('ma_nvgh') or '') for rows in groups.values() if rows})
    staff_names={}
    if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='master_data_generic'").fetchone():
        for row in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category='dm02-staff'"):
            try: payload=json.loads(row['payload_json'] or '{}')
            except (ValueError,TypeError): continue
            code=str(payload.get('MA_NV') or row['business_key'] or '').strip()
            staff_names[code]=str(payload.get('TEN_NV') or payload.get('HO_TEN') or payload.get('TEN_NHAN_VIEN') or '')
    staff_header=[{'code':code,'name':staff_names.get(code,'')} for code in staff_codes if code]
    opening=[]; performed=[]; remaining=[]; abnormal=[]
    for ono, lines in groups.items():
        if ono in before: continue
        s=lines[0]; d=drafts.get(ono)
        ck=money(sum(dec(x['ck_km_dong_goc']) for x in lines))
        acc=max(money(x['thuong_tich_luy_goc']) for x in lines)
        disp=max(money(x['thuong_trung_bay_goc']) for x in lines)
        # Same baseline as stable draft creation, no change to settlement arithmetic.
        original=max(0,sum(max(0,round(dec(x['sl_hang_ban_dat'])*dec(x['don_gia_co_vat'])-dec(x['ck_km_dong_goc']))) for x in lines)-acc-disp)
        if d: original=int(d['so_phai_thu_goc'])
        base=dict(order=ono,customer=s.get('ma_kh_chuan') or s.get('ma_kh_dms') or s.get('ma_kh_mbw') or '',
          customer_name=s.get('ten_kh') or '',customer_dms=s.get('ma_kh_dms') or '',customer_mbw=s.get('ma_kh_mbw') or '',
          staff=(session or {}).get('ma_nvgh') or s.get('ma_nvgh') or '',
          original_due=original,ck_original=ck,display_original=disp,accum_original=acc,
          final_due=original,returned_goods_vat=0,ck_recovered=0,display_recovered=0,
          accum_recovered=0,reduction_due=0,reason='',status='Chưa giao chuyển lần sau')
        opening.append(dict(base))
        if ono not in current:
            remaining.append(dict(base)); continue
        if not d:
            base.update(status='GIAO_DU',reason='Giao đủ theo số nguồn; chưa có nháp điều chỉnh')
            performed.append(base)
            continue
        dl=[dict(r) for r in c.execute('SELECT * FROM qtgh_draft_line WHERE draft_order_id=?',(d['id'],))]
        if not dl: raise ValueError('Đơn '+ono+' thiếu chi tiết quyết toán.')
        base.update(final_due=int(d['so_phai_thu_sau_qt']),
          returned_goods_vat=money(sum(dec(x['sl_hang_ban_tra'])*dec(x['don_gia_co_vat']) for x in dl)),
          ck_recovered=money(sum(dec(x['ck_km_dong_goc'])-dec(x['ck_km_dong_sau']) for x in dl)),
          display_recovered=disp-int(d['display_after']),accum_recovered=acc-int(d['accumulation_after']),
          reduction_due=original-int(d['so_phai_thu_sau_qt']),status=d['vo_type'],
          reason=d.get('reason') or d.get('ghi_chu') or d.get('note') or '')
        if not base['reason']:
            returned=any(dec(x['sl_hang_ban_tra']) or dec(x['sl_hang_km_tra']) for x in dl)
            full=returned and all(dec(x['sl_hang_ban_tra'])>=dec(x['sl_hang_ban_dat']) and dec(x['sl_hang_km_tra'])>=dec(x['sl_hang_km_dat']) for x in dl)
            base['reason']='Giao không thành công — trả toàn bộ' if full else 'Giao một phần — có trả hàng' if returned else 'Điều chỉnh ưu đãi' if any(base[k] for k in ('ck_recovered','display_recovered','accum_recovered')) else 'Giao đủ'
        performed.append(base)
        if any(base[k] for k in ('returned_goods_vat','ck_recovered','display_recovered','accum_recovered','reduction_due')) or any(dec(x['sl_hang_km_tra']) for x in dl) or d['vo_type']!='GIAO_DU':
            abnormal.append(base)
    return dict(title='chốt giảm trừ cuối đơn',lot=lot,day=day,round=nth,session=session,
      staff_header=staff_header,preview=session is None,opening=opening,performed=performed,abnormal=abnormal,remaining=remaining,
      totals={k:total(v) for k,v in [('opening',opening),('performed',performed),('abnormal',abnormal),('remaining',remaining)]},
      sessions=[dict(sessions[k],round=i+1) for i,k in enumerate(ordered)],
      note='Giảm phải thu = phải thu gốc − phải thu cuối. Giá trị hàng trả có VAT và ưu đãi thu hồi được trình bày riêng; không cộng hai khoản giảm trừ lần nữa. Số âm ở khoản thu hồi là ưu đãi tăng thêm. Báo cáo chỉ đọc dữ liệu.')

@router.get('/lots')
def lots():
    with closing(sqlite3.connect(f'file:{DB}?mode=ro',uri=True)) as c:
        c.row_factory=sqlite3.Row
        return {'rows':[dict(r) for r in c.execute("SELECT DISTINCT ma_lo,ngay_giao FROM qtgh_source_projection WHERE source_system='DMS_MBW' AND COALESCE(ma_lo,'')<>'' ORDER BY ngay_giao DESC,ma_lo")]}

@router.get('')
def report(ma_lo:str,ngay_giao:str,session_id:int=None,order:list[str]=Query(default=[]),catalog:bool=False):
    try:
        with closing(sqlite3.connect(f'file:{DB}?mode=ro',uri=True)) as c:
            c.row_factory=sqlite3.Row
            c.execute('BEGIN')
            if catalog:
                rows=[dict(r) for r in c.execute('''SELECT DISTINCT se.id,se.ma_phien_qt,se.locked_at
                  FROM qtgh_session se JOIN qtgh_session_order so ON so.session_id=se.id
                  JOIN qtgh_draft_order d ON d.id=so.draft_order_id
                  JOIN qtgh_source_projection s ON s.source_system=d.source_system AND s.ma_don_nguon=d.ma_don_nguon
                  WHERE se.status='DA_KHOA' AND s.ma_lo=? AND s.ngay_giao=? ORDER BY se.id''',(ma_lo,ngay_giao))]
                return {'rows':rows}
            return build(c,ma_lo,ngay_giao,session_id,order)
    except ValueError as e: raise HTTPException(400,str(e))
