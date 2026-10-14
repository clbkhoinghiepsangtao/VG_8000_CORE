"""Tiếp nhận các dòng đã đọc từ tệp; mẫu cột tham chiếu UI02 cũ."""
from datetime import datetime,date
from decimal import Decimal, InvalidOperation
from .orders import Line,Order

class IntakeError(ValueError):
    def __init__(self,errors):
        self.errors=errors
        super().__init__('; '.join(f"Dòng {x['row']}: {x['message']}" for x in errors))

def number(value,required=False):
    if value in (None,''):
        if required:raise ValueError('Thiếu số bắt buộc')
        return Decimal(0)
    try:n=Decimal(str(value))
    except InvalidOperation:raise ValueError('Số không hợp lệ')
    if not n.is_finite() or n<0:raise ValueError('Số phải hữu hạn không âm')
    return n

def code(v):
    if isinstance(v,bool) or isinstance(v,float):raise ValueError('Mã phải là văn bản hoặc số nguyên; không nhận số thực')
    return str(v if v is not None else '').strip().upper()

def day(v):
    if isinstance(v,datetime):return v.date().isoformat()
    if isinstance(v,date):return v.isoformat()
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y'):
        try:return datetime.strptime(str(v),fmt).date().isoformat()
        except ValueError:pass
    raise ValueError('Ngày đơn không hợp lệ')

def parse_rows(rows,customers,products):
    """Chặn toàn bộ lần nạp nếu lỗi; giữ payload gốc và thứ tự dòng.
    DOANH_SO_PHAI_THU là tiền cấp dòng theo bộ đọc tham chiếu.
    Thưởng/giảm cấp đơn phải nhất quán giữa các dòng, chỉ trừ một lần.
    """
    if not rows:raise IntakeError([{'row':0,'message':'Không có dữ liệu'}])
    aliases={}
    for customer in customers:
        canonical=code(customer.get('MA_KH_CHUAN'))
        if not canonical or canonical=='XY00':continue
        for field in ('MA_KH_CHUAN','MA_KH_DMS','MA_KH_MBW'):
            alias=code(customer.get(field))
            if alias:
                aliases.setdefault(alias,set()).add(canonical)
    grouped={};errors=[];raw=[]
    for i,r in enumerate(rows,2):
        try:
            if not isinstance(r,dict):raise ValueError('Dòng không phải đối tượng dữ liệu')
            i=int(r.get('_SOURCE_ROW',i))
            source={'L':'DMS','B':'MBW','DMS':'DMS','MBW':'MBW'}.get(code(r.get('LOAI_DON')))
            oid=code(r.get('SO_HOA_DON'));kh=code(r.get('MA_KH_NGUON'));sku=code(r.get('MA_SKU'))
            if not source or not oid:raise ValueError('Thiếu/sai loại đơn hoặc mã đơn')
            matches=aliases.get(kh,set())
            if len(matches)!=1:raise ValueError('Khách chưa mapping hoặc mapping nhiều khách')
            customer=next(iter(matches));od=day(r.get('NGAY_DON'))
            product=products.get(sku)
            if not product:raise ValueError('SKU chưa có danh mục')
            ratio=number(product.get('SO_SU_THUNG'),True);weight=number(product.get('TRONG_LUONG_SU'),True)
            if ratio<=0 or weight<=0:raise ValueError('Quy đổi/trọng lượng phải dương')
            # Số lượng nguồn là SU. Đóng gói DMS là Unit/thùng, chỉ lưu đối chiếu.
            # Thùng -> SU và kg luôn theo danh mục, kể cả sản phẩm dạng dây.
            sale=number(r.get('SL_SU'))+number(r.get('SL_THUNG'))*ratio
            promo=number(r.get('SL_KM_SU'))+number(r.get('SL_KM_THUNG'))*ratio
            if sale+promo<=0:raise ValueError('Dòng không có số lượng')
            line=Line(sku,sale,promo,weight)
            due=number(r.get('DOANH_SO_PHAI_THU'),True)
            if source=='MBW' and r.get('DON_GIA_CO_VAT') not in (None,''):
                expected=sale*number(r['DON_GIA_CO_VAT'],True)-number(r.get('TIEN_CK_DONG'))
                if abs(expected-due)>1:raise ValueError('Tiền MBW không khớp SU theo danh mục × giá − chiết khấu')
            rewards=tuple(number(r.get(f)) for f in ('THUONG_TICH_LUY','THUONG_TRUNG_BAY','GIAM_TRU_CAP_DON_KHAC'))
            meta=(customer,od,rewards);key=(source,oid)
            if key in grouped and grouped[key]['meta']!=meta:raise ValueError('Thông tin khách/ngày/giảm cấp đơn không nhất quán')
            g=grouped.setdefault(key,{'meta':meta,'lines':[],'due':Decimal(0)})
            g['lines'].append(line);g['due']+=due
            raw.append({'row':i,'source':source,'code':oid,'data':dict(r)})
        except (ValueError,TypeError) as e:errors.append({'row':i,'message':str(e)})
    orders=[]
    for (source,oid),g in grouped.items():
        customer,od,rewards=g['meta'];due=g['due']-sum(rewards,Decimal(0))
        if due<0:errors.append({'row':0,'message':f'{source}/{oid}: giảm cấp đơn vượt tiền dòng'})
        else:orders.append(Order(source,oid,customer,od,due,tuple(g['lines'])))
    if errors:raise IntakeError(errors)
    return tuple(orders),raw
