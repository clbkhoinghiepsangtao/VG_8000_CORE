"""Đối chiếu mã và đơn vị nguồn trước khi tính kg; không sửa danh mục."""
from .intake import code,number

class MappingError(ValueError):
    def __init__(self,report):
        self.report=report
        super().__init__('Danh mục hoặc đơn vị nguồn chưa khớp; xem báo cáo đối chiếu')

def audit_mapping(rows,customers,products):
    aliases={}
    for customer in customers:
        key=code(customer.get('MA_KH_CHUAN'))
        if not key or key=='XY00':continue
        for field in ('MA_KH_CHUAN','MA_KH_DMS','MA_KH_MBW'):
            alias=code(customer.get(field))
            if alias:aliases.setdefault(alias,set()).add(key)
    issues={};blocked=set();pack_notes={}
    def add(kind,key,row,**extra):
        issue=issues.setdefault((kind,key),{'type':kind,'code':key,'rows':[], 'orders':set(),**extra})
        issue['rows'].append(row.get('_SOURCE_ROW'))
        issue['orders'].add((code(row.get('LOAI_DON')),code(row.get('SO_HOA_DON'))))
        blocked.add((code(row.get('LOAI_DON')),code(row.get('SO_HOA_DON'))))
    for row in rows:
        kh=code(row.get('MA_KH_NGUON'));sku=code(row.get('MA_SKU'))
        matches=aliases.get(kh,set())
        if len(matches)!=1:add('CUSTOMER_MISSING' if not matches else 'CUSTOMER_AMBIGUOUS',kh,row,candidates=sorted(matches))
        product=products.get(sku)
        if not product:
            add('SKU_MISSING',sku,row,source_name=str(row.get('TEN_SKU') or ''));continue
        try:
            ratio=number(product.get('SO_SU_THUNG'),True);weight=number(product.get('TRONG_LUONG_SU'),True)
            if ratio<=0 or weight<=0:raise ValueError('Quy đổi và trọng lượng phải dương')
        except ValueError as e:
            add('PRODUCT_INVALID',sku,row,message=str(e),master_ratio=product.get('SO_SU_THUNG'),weight=product.get('TRONG_LUONG_SU'))
        if row.get('SO_SU_THUNG_NGUON') not in (None,''):
            try:
                source_ratio=number(row['SO_SU_THUNG_NGUON'],True)
                master_ratio=number(product.get('SO_SU_THUNG'),True)
                if source_ratio<=0 or source_ratio!=master_ratio:
                    # Đây là khác đơn vị Unit/SU, không phải lỗi quy đổi số lượng.
                    note=pack_notes.setdefault(sku,{'sku':sku,'master_su_per_case':str(master_ratio),'source_pack_values':set()})
                    note['source_pack_values'].add(str(source_ratio))
            except ValueError as e:add('SOURCE_PACK_INVALID',sku,row,message=str(e))
    result=[]
    for _,issue in sorted(issues.items()):
        item=dict(issue);item['orders']=[{'source':s,'code':c} for s,c in sorted(item['orders'])]
        if 'source_ratios' in item:item['source_ratios']=sorted(item['source_ratios'])
        result.append(item)
    orders={(code(r.get('LOAI_DON')),code(r.get('SO_HOA_DON'))) for r in rows}
    notes=[]
    for _,note in sorted(pack_notes.items()):
        notes.append({**note,'source_pack_values':sorted(note['source_pack_values'])})
    return {'issue_count':len(result),'order_count':len(orders),'blocked_order_count':len(blocked),
            'quantity_policy':'SOURCE_SU_MASTER_CASE_RATIO','unit_pack_notes':notes,
            'ready_order_count':len(orders-blocked),'issues':result}
