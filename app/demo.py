from .db import connect

def seed_demo():
    metrics={
      'CONG_NO_KH':(1240000000,'VND'),'CONG_NO_NVGH':(182000000,'VND'),'XA_CHUA_BU_SU':(12840,'SU'),
      'CKKM_TON':(286500000,'VND'),'GSS_THUC_TE':(8420000000,'VND'),'DOANH_SO_THUC_GIAO':(9015000000,'VND'),
      'KHOI_LUONG_GIAO':(86420,'KG'),'TI_LE_GIAO_SLA':(88.6,'PERCENT'),'BOC_XEP_KG':(222700,'KG'),'BOC_XEP_TIEN':(37470000,'VND')
    }
    with connect() as con:
        for k,(v,u) in metrics.items():
            con.execute('INSERT INTO result_snapshot(metric_key,metric_value,unit) VALUES(?,?,?) ON CONFLICT(metric_key) DO UPDATE SET metric_value=excluded.metric_value,unit=excluded.unit,updated_at=CURRENT_TIMESTAMP',(k,v,u))
    return metrics

def dashboard():
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT metric_key,metric_value,unit,updated_at FROM result_snapshot ORDER BY metric_key')]
