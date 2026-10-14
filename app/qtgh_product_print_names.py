"""Only print labels. Never updates source lines, prices, balances or locked snapshots."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABEL_FILE = ROOT / 'data' / 'qtgh_product_print_names_v1.json'

def product_names(c):
    result = {}
    for row in c.execute("SELECT business_key,payload_json FROM master_data_generic WHERE category='dm01-product'"):
        p = json.loads(row['payload_json'] or '{}')
        sku = str(p.get('MA_SKU') or row['business_key'] or '').strip().upper()
        name = str(p.get('TEN_SKU') or '').strip()
        if sku and name:
            if sku in result and result[sku] != name:
                raise ValueError('Danh mục có tên khác nhau cho cùng SKU: ' + sku)
            result[sku] = name
    return result

def lot_names(c, print_lot_id, current_names):
    pb = c.execute('SELECT print_batch_id,snapshot_json FROM qtgh_print_batch WHERE print_lot_id=? ORDER BY print_version DESC LIMIT 1', (print_lot_id,)).fetchone()
    if not pb:
        return current_names
    snapshot = json.loads(pb['snapshot_json'])
    if snapshot.get('product_name_mapping_version') == 1:
        return {str(x['ma_sku']).strip().upper(): x['ten_sku']
                for o in snapshot['orders'] for x in o['lines']}
    saved = json.loads(LABEL_FILE.read_text(encoding='utf-8')) if LABEL_FILE.exists() else {}
    batch = saved.get('batches', {}).get(pb['print_batch_id'])
    if batch is None:
        # A legacy lock created by an old worker: retain its historical names.
        return {str(x['ma_sku']).strip().upper(): x.get('ten_sku')
                for o in snapshot['orders'] for x in o['lines']}
    return batch['names']

def display_name(names, sku, source):
    key = str(sku or '').strip().upper()
    return names.get(key) or source or ''
