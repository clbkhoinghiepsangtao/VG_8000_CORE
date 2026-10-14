"""Ghép thưởng cấp đơn DMS; chỉ trừ một lần qua parse_rows.

Bảng đầy đủ: đơn không liệt kê có thưởng 0, được người dùng chốt 30/09/2026.
missing_as_zero=False dành cho kiểm tra bảng chưa xác nhận đầy đủ.
"""
from .intake import code,day,number
from .sources import norm

FIELDS=('THUONG_TRUNG_BAY','THUONG_TICH_LUY')
HEADERS={'SO_HOA_DON','NGAY_DON','MA_NV_KD_NGHIEP_VU',*FIELDS}

def attach_rewards(detail_rows,reward_rows,*,missing_as_zero=True):
    orders={};staff_by_order={}
    for row in detail_rows:
        if code(row.get('LOAI_DON')) not in ('L','DMS'):
            raise ValueError('Bảng thưởng DMS chỉ ghép với nguồn DMS')
        key=code(row.get('SO_HOA_DON'))
        meta=(day(row.get('NGAY_DON')),code(row.get('MA_KH_NGUON')))
        if not key:raise ValueError('Chi tiết thiếu số hóa đơn')
        if key in orders and orders[key]!=meta:
            raise ValueError(f'{key}: ngày/khách chi tiết không nhất quán')
        orders[key]=meta
        staff_by_order.setdefault(key,set()).add(code(row.get('MA_NV_KD_NGHIEP_VU')))
    rewards={}
    for original in reward_rows:
        row={norm(k):v for k,v in original.items()}
        missing=HEADERS-set(row)
        if missing:raise ValueError('Bảng thưởng thiếu cột: '+', '.join(sorted(missing)))
        key=code(row['SO_HOA_DON'])
        if not key or key not in orders:raise ValueError(f'Thưởng không có đơn chi tiết tương ứng: {key}')
        if key in rewards:raise ValueError(f'Trùng thưởng cấp đơn: {key}')
        if day(row['NGAY_DON'])!=orders[key][0] or code(row['MA_NV_KD_NGHIEP_VU']) not in staff_by_order[key]:
            raise ValueError(f'{key}: ngày/nhân viên thưởng không khớp chi tiết')
        rewards[key]={field:number(row[field],True) for field in FIELDS}
        rewards[key]['_RAW_ORDER_REWARD']=dict(original)
    unlisted=sorted(set(orders)-set(rewards))
    if unlisted and not missing_as_zero:
        raise ValueError(f'{len(unlisted)} đơn chưa có dòng thưởng; cần xác nhận bảng đầy đủ trước khi dùng thưởng bằng 0')
    result=[]
    for original in detail_rows:
        row=dict(original);key=code(row['SO_HOA_DON'])
        values=rewards.get(key,{field:number(0) for field in FIELDS})
        for field in FIELDS:
            if row.get(field) not in (None,'') and number(row[field])!=values[field]:
                raise ValueError(f'{key}: thưởng trong chi tiết khác bảng thưởng')
        row.update(values)
        row['_REWARD_STATUS']='MATCHED' if key in rewards else 'CONFIRMED_ZERO'
        result.append(row)
    return result,{'matched_orders':len(rewards),'unlisted_orders':unlisted,
                   'multiple_staff_orders':sorted(key for key,staff in staff_by_order.items() if len(staff)>1),
                   'total_reward':str(sum(sum(value[field] for field in FIELDS) for value in rewards.values()))}
