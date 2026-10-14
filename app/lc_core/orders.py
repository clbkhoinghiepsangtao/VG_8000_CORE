"""Nền tảng độc lập; chưa kết nối cơ sở dữ liệu Mini App."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Tuple

@dataclass(frozen=True)
class Line:
    sku: str
    sale_su: Decimal
    promo_su: Decimal
    weight_per_su: Decimal

    def __post_init__(self):
        values=(self.sale_su,self.promo_su,self.weight_per_su)
        if not self.sku or any(not v.is_finite() or v < 0 for v in values) or self.weight_per_su == 0:
            raise ValueError('SKU, số lượng hoặc trọng lượng không hợp lệ')

@dataclass(frozen=True)
class Order:
    source: str
    code: str
    customer: str
    order_date: str
    amount_due: Decimal
    lines: Tuple[Line, ...]
    committed: bool = False

    def __post_init__(self):
        from datetime import date
        if self.source not in ('DMS','MBW') or not self.code or not self.customer or not self.lines:
            raise ValueError('Đơn thiếu nguồn, mã, khách hoặc dòng hàng')
        date.fromisoformat(self.order_date)
        if not self.amount_due.is_finite() or self.amount_due < 0:
            raise ValueError('Tiền phải trả không hợp lệ; chuyển xử lý ngoại lệ')

    @property
    def key(self):
        return self.source,self.code

    @property
    def kg(self):
        return sum(((x.sale_su+x.promo_su)*x.weight_per_su for x in self.lines),Decimal(0))

@dataclass(frozen=True)
class DeliveryPoint:
    customer: str
    orders: Tuple[Order, ...]

    @property
    def kg(self):
        return sum((o.kg for o in self.orders),Decimal(0))

    @property
    def amount_due(self):
        return sum((o.amount_due for o in self.orders),Decimal(0))

    def is_under_weight(self, threshold):
        return self.kg < threshold


def group_orders(orders):
    """Chỉ nhận tập đơn chờ giao đã chọn, mapping xong; không tự bỏ đơn lỗi."""
    seen=set()
    groups={}
    for o in orders:
        if o.committed:
            raise ValueError('Đơn đã chốt không được ghép lại')
        if o.key in seen:
            raise ValueError('Trùng khóa nguồn + mã đơn')
        seen.add(o.key)
        groups.setdefault(o.customer,[]).append(o)
    return tuple(DeliveryPoint(k,tuple(sorted(v,key=lambda o:(o.source!='DMS',o.order_date,o.code))))
                 for k,v in sorted(groups.items()))


def check_add(current, point, target_kg=None, max_points=None, max_money=None):
    """Kiểm tra thêm nguyên phiếu; bộ gom địa lý phải xử lý dừng khi bị từ chối."""
    if target_kg is not None and (not target_kg.is_finite() or target_kg <= 0):
        raise ValueError('Mục tiêu kg phải dương')
    if max_points is not None and (isinstance(max_points,bool) or not isinstance(max_points,int) or max_points <= 0):
        raise ValueError('Giới hạn điểm phải là số nguyên dương')
    if max_money is not None and (not max_money.is_finite() or max_money <= 0):
        raise ValueError('Giới hạn tiền phải dương')
    if point.customer in {p.customer for p in current}:
        raise ValueError('Một điểm không được thêm hai lần')
    kg=sum((p.kg for p in current),Decimal(0))+point.kg
    money=sum((p.amount_due for p in current),Decimal(0))+point.amount_due
    count=len(current)+1
    exceeded=[]
    if target_kg is not None and kg > target_kg*Decimal('1.10'): exceeded.append('WEIGHT')
    if max_points is not None and count > max_points: exceeded.append('POINTS')
    if max_money is not None and money > max_money: exceeded.append('MONEY')
    reached=[]
    if target_kg is not None and kg >= target_kg: reached.append('WEIGHT_TARGET')
    if max_points is not None and count == max_points: reached.append('POINTS')
    if max_money is not None and money == max_money: reached.append('MONEY')
    return {'allowed':not exceeded,'close_lot':bool(exceeded or reached),
            'reasons':exceeded if exceeded else reached,'kg':kg,'money':money,'points':count}
