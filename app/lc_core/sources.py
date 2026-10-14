"""Ánh xạ hai mẫu nguyên bản nhận ngày 30/09; không suy ra thưởng thiếu."""
import unicodedata
from .intake import number

def norm(s):return unicodedata.normalize('NFC',str(s)).strip().upper()
DMS={'Ngày lập hoá đơn':'NGAY_DON','Mã hàng hóa':'MA_SKU','Mô tả mặt hàng':'TEN_SKU','Mã nhân viên':'MA_NV_KD_NGHIEP_VU','Số hóa đơn':'SO_HOA_DON','Doanh số mỗi ngày':'DOANH_SO_PHAI_THU','Mã cửa hàng':'MA_KH_NGUON','Số lượng SU':'SL_SU','Số lượng khuyến mãi theo thùng/ Số thùng':'SL_KM_THUNG','Số lượng thùng':'SL_THUNG','Đơn giá':'DON_GIA_NGUON','Đóng gói':'SO_SU_THUNG_NGUON','Số lượng khuyến mãi theo SU/ Số SU khuyế':'SL_KM_SU'}
MBW={'Ngày lập hoá đơn':'NGAY_DON','Số hóa đơn':'SO_HOA_DON','Mã hàng hóa':'MA_SKU','Tên hàng hoá':'TEN_SKU','Đơn vị tính':'DVT','Mã nhân viên bán hàng':'MA_NV_KD_NGHIEP_VU','Tổng tiền phải thu':'DOANH_SO_PHAI_THU','Mã cửa hàng':'MA_KH_NGUON','Tên cửa hàng':'TEN_KH','Địa điểm giao hàng':'DIA_CHI','Số lượng lẻ (hàng bán)':'SL_SU','Số lượng thùng (hàng bán)':'SL_THUNG','Số lượng lẻ (hàng khuyến mại)':'SL_KM_SU','Số lượng thùng (hàng khuyến mại)':'SL_KM_THUNG','Đơn giá sau thuế':'DON_GIA_CO_VAT','Đóng gói':'SO_SU_THUNG_NGUON','Tỷ lệ chiết khấu':'TY_LE_CK','Tổng tiền chiết khấu':'TIEN_CK_DONG'}

def adapt(rows,source):
    mapping=DMS if source=='DMS' else MBW if source=='MBW' else None
    if not mapping:raise ValueError('Nguồn không hợp lệ')
    mapping={norm(k):v for k,v in mapping.items()}
    accepted=[];summaries=[];exceptions=[]
    for index,row in enumerate(rows,2):
        original={norm(k):v for k,v in row.items()};rn=row.get('_SOURCE_ROW',index)
        missing=set(mapping)-set(original)
        if missing:raise ValueError('Thiếu cột nguồn: '+', '.join(sorted(missing)))
        out={v:original[k] for k,v in mapping.items()};out.update({'LOAI_DON':'L' if source=='DMS' else 'B','_SOURCE_ROW':rn,'_RAW_SOURCE':row})
        out['_QUANTITY_BASIS']='SU'
        out['_SOURCE_PACK_BASIS']='UNIT_PER_CASE' if source=='DMS' else 'SOURCE_REFERENCE'
        if source=='DMS' and all(out.get(k) in (None,'') for k in ('SO_HOA_DON','MA_SKU','MA_KH_NGUON')):
            if out['NGAY_DON'] in (None,'','Loại tuyến bán hàng HPCF','Loại tuyến bán hàng NC'):
                summaries.append({'row':rn,'data':row});continue
        try:
            for k in ('SL_SU','SL_THUNG','SL_KM_SU','SL_KM_THUNG','DOANH_SO_PHAI_THU','SO_SU_THUNG_NGUON'):
                number(out[k],k in ('DOANH_SO_PHAI_THU','SO_SU_THUNG_NGUON'))
            number(out['DON_GIA_NGUON' if source=='DMS' else 'DON_GIA_CO_VAT'])
            if source=='MBW':number(out['TIEN_CK_DONG'])
            accepted.append(out)
        except ValueError as e:exceptions.append({'row':rn,'order':out['SO_HOA_DON'],'message':str(e),'data':row})
    # Không cho nạp một phần đơn nếu đơn có dòng ngoại lệ.
    blocked={e['order'] for e in exceptions};valid=[]
    for r in accepted:
        if r['SO_HOA_DON'] in blocked:exceptions.append({'row':r['_SOURCE_ROW'],'order':r['SO_HOA_DON'],'message':'Đơn có dòng ngoại lệ; giữ lại toàn bộ đơn','data':r['_RAW_SOURCE']})
        else:valid.append(r)
    return {'rows':valid,'summaries':summaries,'exceptions':exceptions,'money_status':'NEEDS_ORDER_REWARD_RECONCILIATION' if source=='DMS' else 'RECONCILE_WITH_MASTER_SU'}
