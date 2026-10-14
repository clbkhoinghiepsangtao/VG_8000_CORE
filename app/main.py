from .qtgh_v02 import qtgh_v105_customer_groups
from .qtgh_v02 import qtgh_v104_customer_groups
from .qtgh_v02 import qtgh_v103_customer_groups
from .qtgh_v02 import qtgh_v101_customer_groups
from .qtgh_v02 import qtgh_v096_customer_groups
from .qtgh_v02 import qtgh_v095_preview_allocation,qtgh_v095_add_customer_to_batch
from .qtgh_v02 import qtgh_v091_ui07_customer_groups
from .qtgh_v02 import qtgh_v09_ui07_debts,qtgh_v09_customer_debts,qtgh_v09_preview_allocation,qtgh_v09_add_customer_to_batch,qtgh_v09_open_batch_detail,qtgh_v09_finalize_batch
from .qtgh_v02 import qtgh_v085_receive_cash
from .qtgh_v02 import qtgh_v084_cash_list,qtgh_v084_cash_detail,qtgh_v084_receive_cash
from .qtgh_v02 import qtgh_v082_pending_orders_readonly,qtgh_v082_finalize_selected
from .qtgh_v02 import qtgh_v08_saved_drafts,qtgh_v08_pending_orders
from .qtgh_v02 import ui02_saved_drafts
from .qtgh_v02 import ui04_employee_suggestions,ui04_lot_suggestions,ui04_pending_orders,finalize_selected_employee_orders
from .qtgh_v02 import suggest_delivery_employees,suggest_delivery_lots
from .qtgh_v02 import update_draft as qtgh_v02_update_draft
from .qtgh_v02 import receiving_banks,add_receiving_bank,set_draft_full_break,set_draft_payment_mode,abnormal_drafts_scoped,delivery_context,finalize_lot_session,qtgh_v03_rebuild_projection
from .qtgh_v02 import order_list,context_options,order_list_scoped,ui01_search_orders,ui04_lot_orders,ui04_finalize_lot,create_or_get_draft,get_draft,update_draft,lock_draft,cash_receipts,receive_cash,return_notes,receive_return,customer_debts,collect_customer_debt,employee_debts,plan_employee_debt_collection,adjustments,create_adjustment,approve_adjustment,cash_inventory,lock_cash_inventory
from .gh_v1 import list_orders,create_draft,get_settlement,update_draft,commit_settlement,customer_debts,collect_customer_debt,delivery_debts,collect_delivery_debt,cashier_list,cashier_receive,admin_export
from .gh_ui01 import gh_ui01_orders, gh_ui01_xlsx
from .xb_ui02 import quantity_report_v5, ckkm_report_v5, quantity_v5_xlsx, ckkm_v5_xlsx, report_options_v5
from .xb_ui02 import quantity_v3, ckkm_v3, quantity_v3_xlsx, ckkm_v3_xlsx, _v3_options
from .xb_ui02 import quantity_v2, ckkm_v2, filter_options_v2
from .xb_ui02 import quantity_group_report
from .xb_ui02 import quantity_report, quantity_report_xlsx, ckkm_report, ckkm_report_xlsx, exception_report, history_report
from .xb_replace_batch import prepare_replacement, finalize_replacement, replacement_history
from .xb_mapping_audit import run_mapping_audit, mapping_errors_xlsx, missing_master_xlsx
from .xb_history_v6 import unified_history_v6
from .xb_misa_bu import preview_misa_bu, commit_misa_bu, history_misa_bu
from .xb_history_v5 import unified_history, unified_commit
from .dms_mbw_template_v2 import build_dms_mbw_v2_template
from .xb_dms_mbw import preview_dms_mbw, commit_dms_mbw, history_dms_mbw
from .xb_v4 import vg_xb_v4_history, vg_xb_v4_commit, vg_xb_v4_diag
from .xb_commit_v3 import vg_xb_v3_commit_batch, vg_xb_v3_history
from .xb_source_v2 import preview_dms_xa, commit_batch, history, error_file
from .source_import_runtime import preview_source, commit_source, list_batches, error_xlsx
from .master_data_runtime import preview_upload, commit_upload, export_master, list_master_rows, delete_master_row
from fastapi import Request
from .master_templates import MASTER_TEMPLATES, build_master_template
from pathlib import Path
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .db import init_db, connect
from .template_defs import TEMPLATES
from .template_service import build_template
from .validator import validate_workbook, commit_batch
from .demo import seed_demo, dashboard
from .security import verify_password, create_session, get_user_by_token, has_permission, audit, hash_password
from .access_control_v1 import router as access_control_v1_router, authorize_request
ROOT=Path(__file__).resolve().parents[1]; FRONT=ROOT/'frontend'
app=FastAPI(title='Mini App Vĩnh Giang V1.0 Runtime',version='1.0.0')
app.include_router(access_control_v1_router)

# VG_DMS_MBW_TEMPLATE_V2_EARLY_ROUTE

































@app.get("/api/qtgh-v105/ui08/customers")
def qtgh_v105_customers_api(ma_nvgh:str,q:str=""):
    try:
        return qtgh_v105_customer_groups(ma_nvgh,q)
    except Exception as e:
        print(f"[QTGH V105 DM03 MAP ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v104/ui08/customers")
def qtgh_v104_customers_api(ma_nvgh:str,q:str=""):
    try:
        return qtgh_v104_customer_groups(ma_nvgh,q)
    except Exception as e:
        print(f"[QTGH V104 CUSTOMER MAP ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v103/ui08/customers")
def qtgh_v103_customers_api(ma_nvgh:str,q:str=""):
    try:return qtgh_v103_customer_groups(ma_nvgh,q)
    except Exception as e:
        print(f"[QTGH V103 CUSTOMER ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v101/ui08/customers")
def qtgh_v101_customers_api(ma_nvgh:str,q:str=""):
    try:
        return qtgh_v101_customer_groups(ma_nvgh,q)
    except Exception as e:
        print(f"[QTGH V101 CUSTOMER GROUP ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v096/ui08/customers")
def qtgh_v096_customers_api(ma_nvgh:str,q:str=""):
    try:return qtgh_v096_customer_groups(ma_nvgh,q)
    except Exception as e:
        print(f"[QTGH V096 UI08 CUSTOMER SEARCH ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v095/ui08/preview")
async def qtgh_v095_preview_api(request:Request):
    try:
        x=await request.json()
        return qtgh_v095_preview_allocation(
          x["ma_nvgh"],x.get("debt_ids",[]),x.get("cash_amount",0),x.get("bank_amount",0)
        )
    except Exception as e:
        print(f"[QTGH V095 UI08 PREVIEW ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v095/ui08/add-customer")
async def qtgh_v095_add_customer_api(request:Request):
    try:
        x=await request.json()
        return qtgh_v095_add_customer_to_batch(
          x["ma_nvgh"],x.get("customer_code",""),x.get("debt_ids",[]),
          x.get("cash_amount",0),x.get("bank_amount",0),
          x.get("bank_account",""),x.get("bank_txn_id","")
        )
    except Exception as e:
        print(f"[QTGH V095 UI08 ADD ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v091/ui07/customer-groups")
def qtgh_v091_ui07_customer_groups_api(ma_nvgh:str):
    try:return qtgh_v091_ui07_customer_groups(ma_nvgh)
    except Exception as e:
        print(f"[QTGH V091 UI07 GROUP ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v09/ui07/debts")
def qtgh_v09_ui07_debts_api(ma_nvgh:str):
    try:return qtgh_v09_ui07_debts(ma_nvgh)
    except Exception as e:
        print(f"[QTGH V09 UI07 ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v09/ui08/customer-debts")
def qtgh_v09_customer_debts_api(ma_nvgh:str,customer_code:str):
    try:return qtgh_v09_customer_debts(ma_nvgh,customer_code)
    except Exception as e:
        print(f"[QTGH V09 UI08 DEBT ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v09/ui08/preview")
async def qtgh_v09_preview_api(request:Request):
    try:
        x=await request.json()
        return qtgh_v09_preview_allocation(
          x["ma_nvgh"],x["customer_code"],x.get("cash_amount",0),x.get("bank_amount",0)
        )
    except Exception as e:
        print(f"[QTGH V09 UI08 PREVIEW ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v09/ui08/add-customer")
async def qtgh_v09_add_customer_api(request:Request):
    try:
        x=await request.json()
        return qtgh_v09_add_customer_to_batch(
          x["ma_nvgh"],x["customer_code"],x.get("cash_amount",0),x.get("bank_amount",0),
          x.get("bank_account",""),x.get("bank_txn_id","")
        )
    except Exception as e:
        print(f"[QTGH V09 UI08 ADD ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v09/ui08/open-batch")
def qtgh_v09_open_batch_api(ma_nvgh:str):
    try:return qtgh_v09_open_batch_detail(ma_nvgh)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v09/ui08/finalize/{batch_id}")
def qtgh_v09_finalize_api(batch_id:int):
    try:return qtgh_v09_finalize_batch(batch_id)
    except Exception as e:
        print(f"[QTGH V09 UI08 FINALIZE ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v085/ui05/cash/{rid}/receive")
async def qtgh_v085_ui05_receive(rid:int,request:Request):
    try:
        x=await request.json()
        return qtgh_v085_receive_cash(
          rid,
          x.get("actual_amount",0),
          x.get("resolution_code"),
          x.get("resolution_note","")
        )
    except Exception as e:
        print(f"[QTGH V085 UI05 RECEIVE ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v084/ui05/cash")
def qtgh_v084_ui05_cash():
    try:return qtgh_v084_cash_list()
    except Exception as e:
        print(f"[QTGH V084 UI05 LIST ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v084/ui05/cash/{rid}")
def qtgh_v084_ui05_cash_detail(rid:int):
    try:return qtgh_v084_cash_detail(rid)
    except Exception as e:
        print(f"[QTGH V084 UI05 DETAIL ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v084/ui05/cash/{rid}/receive")
async def qtgh_v084_ui05_receive(rid:int,request:Request):
    try:
        x=await request.json()
        return qtgh_v084_receive_cash(
          rid,
          x.get("actual_amount",0),
          x.get("resolution_code"),
          x.get("resolution_note","")
        )
    except Exception as e:
        print(f"[QTGH V084 UI05 RECEIVE ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v082/ui04/pending-orders")
def qtgh_v082_ui04_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        return qtgh_v082_pending_orders_readonly(ma_nvgh,ngay_giao,ma_lo)
    except Exception as e:
        print(f"[QTGH V082 UI04 LIST ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v082/ui04/finalize-selected")
async def qtgh_v082_ui04_finalize_selected(request:Request):
    try:
        x=await request.json()
        return qtgh_v082_finalize_selected(x["ma_nvgh"],x.get("items",[]))
    except Exception as e:
        print(f"[QTGH V082 UI04 FINALIZE ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v08/ui02/drafts")
def qtgh_v08_ui02_drafts(ma_nvgh:str=None):
    try:
        return qtgh_v08_saved_drafts(ma_nvgh)
    except Exception as e:
        print(f"[QTGH V08 UI02 LIST ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v08/ui04/pending-orders")
def qtgh_v08_ui04_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        return qtgh_v08_pending_orders(ma_nvgh,ngay_giao,ma_lo)
    except Exception as e:
        print(f"[QTGH V08 UI04 LIST ERROR] {e}")
        raise HTTPException(400,str(e))

@app.get("/api/qtgh-v07/ui02/drafts")
def qtgh_v07_ui02_drafts(ma_nvgh:str=None,q:str=""):
    try:return ui02_saved_drafts(ma_nvgh,q)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v06/ui04/suggest-nvgh")
def qtgh_v06_ui04_suggest_nvgh(q:str="",ngay_giao:str=None):
    try:return ui04_employee_suggestions(q,ngay_giao)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v06/ui04/suggest-lo")
def qtgh_v06_ui04_suggest_lo(ma_nvgh:str,q:str="",ngay_giao:str=None):
    try:return ui04_lot_suggestions(ma_nvgh,q,ngay_giao)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v06/ui04/pending-orders")
def qtgh_v06_ui04_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:return ui04_pending_orders(ma_nvgh,ngay_giao,ma_lo)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v06/ui04/finalize-selected")
async def qtgh_v06_ui04_finalize_selected(request:Request):
    try:
        x=await request.json()
        return finalize_selected_employee_orders(x["ma_nvgh"],x.get("draft_ids",[]),note=x.get("note",""))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v05/suggest-nvgh")
def qtgh_v05_suggest_nvgh(ngay_giao:str,q:str=""):
    try:return suggest_delivery_employees(ngay_giao,q)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v05/suggest-lo")
def qtgh_v05_suggest_lo(ngay_giao:str,ma_nvgh:str,q:str=""):
    try:return suggest_delivery_lots(ngay_giao,ma_nvgh,q)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v03/banks")
def qtgh_v03_banks():
    try:return receiving_banks()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v03/banks")
async def qtgh_v03_add_bank(request:Request):
    try:
        x=await request.json()
        return add_receiving_bank(x.get("bank_name",""),x.get("account_no",""),x.get("account_name",""))
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v03/draft/{did}/full-break")
def qtgh_v03_full_break(did:int):
    try:return set_draft_full_break(did)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v03/draft/{did}/payment-mode")
async def qtgh_v03_payment_mode(did:int,request:Request):
    try:
        x=await request.json()
        return set_draft_payment_mode(did,x.get("mode"),x.get("bank_account",""),x.get("bank_txn_id",""))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v03/drafts")
def qtgh_v03_drafts(ngay_giao:str=None,ma_nvgh:str=None,ma_lo:str=None):
    try:return abnormal_drafts_scoped(ngay_giao,ma_nvgh,ma_lo)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v03/delivery-context")
def qtgh_v03_delivery_context(ngay_giao:str=None,ma_nvgh:str=None):
    try:return delivery_context(ngay_giao,ma_nvgh)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v03/finalize-lot")
async def qtgh_v03_finalize_lot(request:Request):
    try:
        x=await request.json()
        return finalize_lot_session(x["ngay_giao"],x["ma_nvgh"],x["ma_lo"])
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui01/search")
def qtgh_v02_ui01_search(q:str):
    try:return ui01_search_orders(q)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui04/lot-orders")
def qtgh_v02_ui04_lot_orders(ngay_giao:str,ma_nvgh:str,ma_lo:str):
    try:return ui04_lot_orders(ngay_giao,ma_nvgh,ma_lo)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui04/finalize")
async def qtgh_v02_ui04_finalize(request:Request):
    try:
        x=await request.json()
        return ui04_finalize_lot(x["ngay_giao"],x["ma_nvgh"],x["ma_lo"])
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/context")
def qtgh_v02_context(ngay_don:str=None,ma_nvgh:str=None):
    try:return context_options(ngay_don,ma_nvgh)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui01/orders-scoped")
def qtgh_v02_ui01_orders_scoped(ngay_don:str=None,ma_nvgh:str=None,ma_lo:str=None):
    try:return order_list_scoped(ngay_don,ma_nvgh,ma_lo)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui01/orders")
def qtgh_v02_ui01_orders(date_from:str=None,date_to:str=None):
    try:return order_list(date_from,date_to)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui02/draft")
async def qtgh_v02_ui02_draft(request: Request):
    try:
        x=await request.json()
        return create_or_get_draft(x["source_system"],x["ma_don_nguon"])
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui02/draft/{did}")
def qtgh_v02_ui02_get(did:int):
    try:return get_draft(did)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui02/draft/{did}/update")
async def qtgh_v02_ui02_update(did:int,request:Request):
    payload={}
    try:
        payload=await request.json()
        return qtgh_v02_update_draft(did,payload)
    except Exception as e:
        print(f"[QTGH UI02 UPDATE ERROR] draft={did} error={e}")
        print(f"[QTGH UI02 PAYLOAD] {payload}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui04/draft/{did}/lock")
def qtgh_v02_ui04_lock(did:int):
    try:return lock_draft(did)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui05/cash")
def qtgh_v02_ui05_cash():
    try:return cash_receipts()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui05/cash/{rid}/receive")
async def qtgh_v02_ui05_receive(rid:int,request:Request):
    try:
        x=await request.json();return receive_cash(rid,x.get("actual_amount",0))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui06/returns")
def qtgh_v02_ui06_returns():
    try:return return_notes()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui06/returns/{nid}/receive")
async def qtgh_v02_ui06_receive(nid:int,request:Request):
    try:return receive_return(nid,(await request.json()).get("lines",[]))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui07/debts")
def qtgh_v02_ui07_debts():
    try:return customer_debts()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui08/debt/{did}/collect")
async def qtgh_v02_ui08_collect(did:int,request:Request):
    try:
        x=await request.json();return collect_customer_debt(did,x.get("cash_amount",0),x.get("bank_amount",0),x.get("overpay_reason",""))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui09/debts")
def qtgh_v02_ui09_debts():
    try:return employee_debts()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui09/debt/{did}/plan")
async def qtgh_v02_ui09_plan(did:int,request:Request):
    try:return plan_employee_debt_collection(did,(await request.json()).get("amount",0))
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui10/adjustments")
def qtgh_v02_ui10_adjustments():
    try:return adjustments()
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui10/adjustment")
async def qtgh_v02_ui10_create(request:Request):
    try:
        x=await request.json();return create_adjustment(x["source_doc_type"],x["source_doc_id"],x["adjustment_type"],x["delta_amount"],x["reason"])
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui10/adjustment/{aid}/approve")
def qtgh_v02_ui10_approve(aid:int):
    try:return approve_adjustment(aid)
    except Exception as e:raise HTTPException(400,str(e))

@app.get("/api/qtgh-v02/ui11/cash-inventory/{date}")
def qtgh_v02_ui11_inventory(date:str):
    try:return cash_inventory(date)
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v02/ui11/cash-inventory/{date}/lock")
async def qtgh_v02_ui11_lock(date:str,request:Request):
    try:return lock_cash_inventory(date,(await request.json()).get("actual_count",0))
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/orders')
def api_gh_v1_orders(date_from:str=None,date_to:str=None,status:str=None):
    try:return list_orders(date_from,date_to,status)
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/order/{order_no}/draft')
def api_gh_v1_draft(order_no:str):
    try:return create_draft(order_no)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/settlement/{sid}')
def api_gh_v1_get(sid:int):
    try:return get_settlement(sid)
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/settlement/{sid}/update')
async def api_gh_v1_update(sid:int, request: Request):
    try:
        x=await request.json()
        return update_draft(sid,x.get('lines',[]),x.get('cash_amount'),x.get('bank_amount'),x.get('customer_debt_amount'),x.get('overpay_reason'))
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/settlement/{sid}/commit')
def api_gh_v1_commit(sid:int):
    try:return commit_settlement(sid)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/customer-debts')
def api_gh_v1_customer_debts():
    try:return customer_debts()
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/customer-debt/{debt_id}/collect')
async def api_gh_v1_customer_collect(debt_id:int, request: Request):
    try:
        x=await request.json()
        return collect_customer_debt(debt_id,x.get('cash_amount',0),x.get('bank_amount',0),x.get('overpay_reason',''))
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/delivery-debts')
def api_gh_v1_delivery_debts():
    try:return delivery_debts()
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/delivery-debt/{debt_id}/collect')
async def api_gh_v1_delivery_collect(debt_id:int, request: Request):
    try:
        x=await request.json()
        return collect_delivery_debt(debt_id,x.get('cash_amount',0),x.get('bank_amount',0))
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/cashier')
def api_gh_v1_cashier():
    try:return cashier_list()
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/gh-v1/cashier/{receipt_id}/receive')
def api_gh_v1_cashier_receive(receipt_id:int):
    try:return cashier_receive(receipt_id)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/gh-v1/admin.xlsx')
def api_gh_v1_admin_xlsx():
    try:filename,data=admin_export()
    except Exception as e:raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(content=data,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{filename}"'})
@app.get('/api/gh-ui01/orders')
def api_gh_ui01_orders(date_from:str=None,date_to:str=None,nv_giao:str=None,lai_xe:str=None,phuong_tien:str=None,lo_giao:str=None):
    try:
        return gh_ui01_orders(date_from,date_to,nv_giao,lai_xe,phuong_tien,lo_giao)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/gh-ui01/orders.xlsx')
def api_gh_ui01_orders_xlsx(date_from:str=None,date_to:str=None,nv_giao:str=None,lai_xe:str=None,phuong_tien:str=None,lo_giao:str=None):
    try:
        filename,data=gh_ui01_xlsx(date_from=date_from,date_to=date_to,nv_giao=nv_giao,lai_xe=lai_xe,phuong_tien=phuong_tien,lo_giao=lo_giao)
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(content=data,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{filename}"'})
@app.get('/api/xb-ui02/v5/options')
def api_xb_ui02_v5_options():
    try:
        return report_options_v5()
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v5/quantity')
def api_xb_ui02_v5_quantity(date_from:str=None,date_to:str=None,month:str=None,report_type:str="employee",ma_nv:str=None,bu:str=None,nhan_hieu:str=None):
    try:
        return quantity_report_v5(date_from,date_to,month,report_type,ma_nv,bu,nhan_hieu)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v5/ckkm')
def api_xb_ui02_v5_ckkm(date_from:str=None,date_to:str=None,month:str=None,ma_nv:str=None):
    try:
        return ckkm_report_v5(date_from,date_to,month,ma_nv)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v5/export')
def api_xb_ui02_v5_export(metric:str="quantity",date_from:str=None,date_to:str=None,month:str=None,report_type:str="employee",ma_nv:str=None,bu:str=None,nhan_hieu:str=None):
    try:
        if metric=="ckkm":
            filename,data=ckkm_v5_xlsx(date_from=date_from,date_to=date_to,month=month,ma_nv=ma_nv)
        else:
            filename,data=quantity_v5_xlsx(date_from=date_from,date_to=date_to,month=month,report_type=report_type,ma_nv=ma_nv,bu=bu,nhan_hieu=nhan_hieu)
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )
@app.get('/api/xb-ui02/v3/options')
def api_xb_ui02_v3_options():
    try:return _v3_options()
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v3/quantity')
def api_xb_ui02_v3_quantity(date_from:str=None,date_to:str=None,month:str=None,report_type:str="detail",ma_nv:str=None,ma_sku:str=None,bu:str=None,nhan_hieu:str=None):
    try:return quantity_v3(date_from,date_to,month,report_type,ma_nv,ma_sku,bu,nhan_hieu)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v3/ckkm')
def api_xb_ui02_v3_ckkm(date_from:str=None,date_to:str=None,month:str=None,ma_nv:str=None):
    try:return ckkm_v3(date_from,date_to,month,ma_nv)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v3/export')
def api_xb_ui02_v3_export(metric:str="quantity",date_from:str=None,date_to:str=None,month:str=None,report_type:str="detail",ma_nv:str=None,ma_sku:str=None,bu:str=None,nhan_hieu:str=None):
    try:
        if metric=="ckkm":
            filename,data=ckkm_v3_xlsx(date_from=date_from,date_to=date_to,month=month,ma_nv=ma_nv)
        else:
            filename,data=quantity_v3_xlsx(date_from=date_from,date_to=date_to,month=month,report_type=report_type,ma_nv=ma_nv,ma_sku=ma_sku,bu=bu,nhan_hieu=nhan_hieu)
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(content=data,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{filename}"'})
@app.get('/api/xb-ui02/v2/options')
def api_xb_ui02_v2_options():
    try:return filter_options_v2()
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v2/quantity')
def api_xb_ui02_v2_quantity(date_from:str=None,date_to:str=None,month:str=None,ma_nv:str=None,ma_sku:str=None,bu:str=None,nhom_san_pham:str=None,view:str="detail"):
    try:return quantity_v2(date_from,date_to,month,ma_nv,ma_sku,bu,nhom_san_pham,view)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/v2/ckkm')
def api_xb_ui02_v2_ckkm(date_from:str=None,date_to:str=None,month:str=None,ma_nv:str=None):
    try:return ckkm_v2(date_from,date_to,month,ma_nv)
    except Exception as e:raise HTTPException(400,str(e))
@app.get('/api/xb-ui02/quantity-group')
def api_xb_ui02_quantity_group(date_from:str=None,date_to:str=None,mode:str="detail",ma_nv:str=None,ma_sku:str=None,bu:str=None,nhom_nhan_hieu:str=None):
    try:
        return quantity_group_report(date_from,date_to,mode,ma_nv,ma_sku,bu,nhom_nhan_hieu)
    except Exception as e:
        raise HTTPException(400,str(e))
@app.get('/api/xb-ui02/ckkm')
def api_xb_ui02_ckkm(date_from:str=None,date_to:str=None,ma_nv:str=None):
    try:return ckkm_report(date_from,date_to,ma_nv)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/exceptions')
def api_xb_ui02_exceptions():
    try:return exception_report()
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/history')
def api_xb_ui02_history():
    try:return history_report()
    except Exception as e:raise HTTPException(400,str(e))
@app.get('/api/xb-ui02/quantity')
def api_xb_ui02_quantity(date_from:str=None,date_to:str=None,ma_nv:str=None,ma_sku:str=None):
    try:
        return quantity_report(date_from,date_to,ma_nv,ma_sku)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-ui02/quantity.xlsx')
def api_xb_ui02_quantity_xlsx(date_from:str=None,date_to:str=None,ma_nv:str=None,ma_sku:str=None):
    try:
        filename,data=quantity_report_xlsx(date_from,date_to,ma_nv,ma_sku)
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )
@app.get('/api/xb-replace/history')
def api_xb_replace_history():
    try:
        return {"rows":replacement_history()}
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-replace/{source_type}/{old_batch_id}/prepare')
def api_xb_replace_prepare(source_type:str,old_batch_id:int):
    try:
        if source_type == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        return prepare_replacement(source_type,old_batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-replace/{source_type}/{old_batch_id}/{new_batch_id}/finalize')
def api_xb_replace_finalize(source_type:str,old_batch_id:int,new_batch_id:int):
    try:
        if source_type == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        return finalize_replacement(source_type,old_batch_id,new_batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))
@app.get('/api/xb-mapping/missing-master.xlsx')
def api_xb_mapping_missing_master():
    try:
        filename,data=missing_master_xlsx()
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )
@app.get('/api/xb-mapping/audit')
def api_xb_mapping_audit():
    try:
        return run_mapping_audit()
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-mapping/errors.xlsx')
def api_xb_mapping_errors():
    try:
        filename,data=mapping_errors_xlsx()
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )
@app.get('/api/xb-v6/history')
def api_xb_v6_history():
    try:
        return {"rows":unified_history_v6()}
    except Exception as e:
        raise HTTPException(400,str(e))
@app.post('/api/xb-misa-bu/preview')
async def api_xb_misa_bu_preview(request: Request):
    try:
        return preview_misa_bu(
            request.headers.get("X-File-Name","MISA_Ban_Bu.xlsx"),
            await request.body(),
            request.headers.get("X-Uploaded-By","pilot")
        )
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-misa-bu/batch/{batch_id}/commit')
def api_xb_misa_bu_commit(batch_id:int):
    try:
        return commit_misa_bu(batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))
@app.get('/api/xb-v5/history')
def api_xb_v5_history():
    try:
        return {"rows":unified_history()}
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-v5/{storage}/batch/{batch_id}/commit')
def api_xb_v5_commit(storage:str,batch_id:int):
    try:
        if storage == "xb_dms_mbw_batch": raise ValueError(_XB_DELIVERY_DISABLED)
        if storage == "src_batch":
            from .source_import_runtime import _conn as _src_conn
            with _src_conn() as conn:
                batch = conn.execute("SELECT source_type FROM src_batch WHERE batch_id=?", (batch_id,)).fetchone()
            if batch and batch["source_type"] == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        return unified_commit(storage,batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))
@app.get("/api/templates/dms-mbw-v2.xlsx")
def vg_template_dms_mbw_v2_early():
    filename, data = build_dms_mbw_v2_template()
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.on_event('startup')
def startup():
    init_db()

def current_user(request:Request,authorization:str|None=Header(default=None)):
    token=(authorization.split(' ',1)[1].strip() if authorization and authorization.lower().startswith('bearer ') else request.cookies.get('vg_session'))
    if not token: raise HTTPException(401,'Chưa đăng nhập')
    user=get_user_by_token(token)
    if not user: raise HTTPException(401,'Phiên đăng nhập hết hạn/không hợp lệ')
    return user

def require(permission:str):
    def dep(user=Depends(current_user)):
        if not has_permission(user['role'],permission): raise HTTPException(403,f'Không có quyền {permission}')
        return user
    return dep

@app.post('/api/auth/login')
def login(payload:dict):
    username=(payload.get('username') or '').strip(); password=payload.get('password') or ''
    with connect() as con:u=con.execute('SELECT * FROM app_user WHERE username=? AND is_active=1',(username,)).fetchone()
    if not u or not verify_password(password,u['password_hash']): raise HTTPException(401,'Sai tài khoản hoặc mật khẩu')
    token=create_session(username); audit(username,'LOGIN')
    response=JSONResponse({'token':token,'user':{'username':username,'full_name':u['full_name'],'role':u['role'],'must_change_password':bool(u['must_change_password'])}})
    response.set_cookie('vg_session',token,max_age=12*60*60,httponly=True,samesite='strict',path='/')
    return response

@app.get('/api/auth/me')
def me(user=Depends(current_user)): return user

@app.post('/api/auth/change-password')
def change_password(payload:dict,user=Depends(current_user)):
    currentp=payload.get('current_password') or ''
    newp=payload.get('new_password') or ''
    if len(newp)<10: raise HTTPException(400,'Mật khẩu mới tối thiểu 10 ký tự')
    with connect() as con:
        u=con.execute('SELECT password_hash FROM app_user WHERE username=?',(user['username'],)).fetchone()
        if not u or not verify_password(currentp,u['password_hash']): raise HTTPException(400,'Mật khẩu hiện tại không đúng')
        if verify_password(newp,u['password_hash']): raise HTTPException(400,'Mật khẩu mới phải khác mật khẩu hiện tại')
        con.execute('UPDATE app_user SET password_hash=?,must_change_password=0 WHERE username=?',(hash_password(newp),user['username']))
        con.execute('DELETE FROM auth_session WHERE username=?',(user['username'],))
    audit(user['username'],'CHANGE_PASSWORD')
    return {'status':'ok','relogin_required':True}

@app.post('/api/auth/logout')
def logout(request:Request,authorization:str|None=Header(default=None)):
    token=(authorization.split(' ',1)[1].strip() if authorization and authorization.lower().startswith('bearer ') else request.cookies.get('vg_session'))
    if token:
        with connect() as con: con.execute('DELETE FROM auth_session WHERE token=?',(token,))
    response=JSONResponse({'status':'ok'})
    response.delete_cookie('vg_session',path='/')
    return response

@app.get('/change-password')
def change_password_page(): return FileResponse(FRONT/'change_password.html')

@app.get('/api/audit')
def audit_list(limit:int=100,user=Depends(require('VIEW_DASHBOARD'))):
    with connect() as con:return [dict(r) for r in con.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?',(min(limit,500),))]

@app.post('/api/adjustments')
def create_adjustment(payload:dict,user=Depends(require('CREATE_ADJUSTMENT'))):
    import uuid,json
    for k in ['original_doc_type','original_doc_id','direction','reason']:
        if not payload.get(k): raise HTTPException(400,'Thiếu thông tin phiếu điều chỉnh')
    aid='ADJ-'+uuid.uuid4().hex[:12].upper()
    with connect() as con: con.execute('INSERT INTO adjustment_doc(adjustment_id,original_doc_type,original_doc_id,direction,amount,quantity,reason,created_by) VALUES(?,?,?,?,?,?,?,?)',(aid,payload['original_doc_type'],payload['original_doc_id'],payload['direction'],float(payload.get('amount') or 0),float(payload.get('quantity') or 0),payload['reason'],user['username']))
    audit(user['username'],'CREATE_ADJUSTMENT','ADJUSTMENT',aid,payload['reason'],new_json=json.dumps(payload,ensure_ascii=False)); return {'adjustment_id':aid,'status':'DRAFT'}

@app.post('/api/admin/unlock')
def unlock(payload:dict,user=Depends(current_user)):
    if user['role']!='SUPER_ADMIN': raise HTTPException(403,'Chỉ SUPER_ADMIN được mở khóa')
    reason=(payload.get('reason') or '').strip()
    if not reason: raise HTTPException(400,'Bắt buộc nhập lý do mở khóa')
    with connect() as con: con.execute('INSERT INTO lock_event(doc_type,doc_id,action,reason,username) VALUES(?,?,?,?,?)',(payload.get('doc_type'),payload.get('doc_id'),'UNLOCK',reason,user['username']))
    audit(user['username'],'UNLOCK_DOC',payload.get('doc_type'),payload.get('doc_id'),reason); return {'status':'ok'}


@app.get('/api/health')
def health(): return {'status':'ok','app':'VĨNH GIANG Mini App','version':'1.0.0'}
@app.get('/api/templates')
def templates(): return [{'key':k,'version':v['version'],'filename':v['filename']} for k,v in TEMPLATES.items()]
@app.get('/api/templates/{template_key}.xlsx')
def template(template_key:str):
    if template_key not in TEMPLATES: raise HTTPException(404,'Template không tồn tại')
    data=build_template(template_key); spec=TEMPLATES[template_key]
    return StreamingResponse(BytesIO(data),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{spec["filename"]}"'})
@app.post('/api/uploads/{template_key}/validate')
async def upload_validate(template_key:str,file:UploadFile=File(...),user=Depends(require('UPLOAD_SOURCE'))):
    if template_key not in TEMPLATES: raise HTTPException(404,'Template không tồn tại')
    if not (file.filename or '').lower().endswith('.xlsx'): raise HTTPException(400,'Chỉ nhận file .xlsx')
    data=await file.read(); result=validate_workbook(template_key,file.filename,data); audit(user['username'],'UPLOAD_VALIDATE','IMPORT_BATCH',result.get('batch_id'),new_json=str({'template':template_key,'filename':file.filename}))
    if result.get('rejected'): raise HTTPException(422,result)
    return result
@app.post('/api/uploads/{batch_id}/commit')
def commit(batch_id:str,user=Depends(require('UPLOAD_SOURCE'))):
    r=commit_batch(batch_id)
    if not r: raise HTTPException(404,'Batch không tồn tại')
    audit(user['username'],'COMMIT_BATCH','IMPORT_BATCH',batch_id)
    return r
@app.get('/api/uploads')
def list_batches():
    with connect() as con: return [dict(r) for r in con.execute('SELECT batch_id,template_key,template_version,filename,status,total_rows,valid_rows,error_rows,created_at,committed_at FROM import_batch ORDER BY created_at DESC LIMIT 100')]
@app.get('/api/uploads/{batch_id}')
def get_batch(batch_id:str):
    with connect() as con:
        b=con.execute('SELECT * FROM import_batch WHERE batch_id=?',(batch_id,)).fetchone()
        if not b: raise HTTPException(404,'Batch không tồn tại')
        rows=[dict(r) for r in con.execute('SELECT sheet_name,row_no,is_valid,errors_json,payload_json FROM import_row WHERE batch_id=? ORDER BY sheet_name,row_no LIMIT 200',(batch_id,))]
        return {'batch':dict(b),'rows':rows}
@app.post('/api/demo/seed')
def demo_seed():
    raise HTTPException(410, 'Demo seed bị vô hiệu trong PILOT_CANDIDATE')
@app.get('/api/dashboard/summary')
def dashboard_summary(): return {'metrics':dashboard(),'rule':'Dashboard chỉ đọc dữ liệu đã chốt từ phân hệ nguồn.'}
@app.get('/login')
def login_page(): return FileResponse(FRONT/'login.html')

@app.get('/api/master-templates')
def list_master_templates():
    return [{"key":k,"filename":v["filename"],"sheet":v["sheet"]} for k,v in MASTER_TEMPLATES.items() if k != "users"]

@app.get('/api/master-templates/{template_key}.xlsx')
def download_master_template(template_key:str):
    if template_key == "users" or template_key not in MASTER_TEMPLATES:
        raise HTTPException(404,"Template danh mục không tồn tại")
    filename,data = build_master_template(template_key)
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":f'attachment; filename="{filename}"'}
    )

@app.get('/')
def index(): return FileResponse(FRONT/'index.html')
app.mount('/ui',StaticFiles(directory=FRONT/'ui',html=True),name='ui')
app.mount('/templates-static',StaticFiles(directory=FRONT/'templates'),name='templates-static')

@app.middleware("http")
async def vg_screen_rbac_v1(request, call_next):
    denied=authorize_request(request)
    if denied is not None: return denied
    return await call_next(request)

# VG_UI_NO_CACHE_MIDDLEWARE
@app.middleware("http")
async def vg_no_cache_ui_html(request, call_next):
    response = await call_next(request)
    path = request.url.path.lower()
    if path == "/" or path.endswith(".html") or path.startswith("/ui/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.post('/api/master-data/{category}/preview')
async def master_preview(category: str, request: Request):
    if category == "users": raise HTTPException(410, "Quan ly tai khoan tai Tai khoan & Phan quyen")
    raw = await request.body()
    if not raw:
        raise HTTPException(400, 'Thiếu file')
    try:
        return preview_upload(category, raw)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post('/api/master-data/{category}/commit')
async def master_commit(category: str, request: Request):
    if category == "users": raise HTTPException(410, "Quan ly tai khoan tai Tai khoan & Phan quyen")
    try:
        body = await request.json()
        return commit_upload(category, body.get('rows', []))
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get('/api/master-data/{category}/export.xlsx')
def master_export(category: str):
    if category == "users": raise HTTPException(410, "Quan ly tai khoan tai Tai khoan & Phan quyen")
    try:
        filename,data = export_master(category)
    except Exception as e:
        raise HTTPException(400, str(e))
    from fastapi.responses import Response
    return Response(content=data, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition':f'attachment; filename="{filename}"'})

@app.get('/api/master-data/{category}/rows')
def master_rows(category: str):
    if category == "users": raise HTTPException(410, "Quan ly tai khoan tai Tai khoan & Phan quyen")
    try:
        return {'rows': list_master_rows(category)}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post('/api/master-data/{category}/delete')
async def master_delete(category: str, request: Request):
    if category == "users": raise HTTPException(410, "Quan ly tai khoan tai Tai khoan & Phan quyen")
    try:
        body = await request.json()
        return delete_master_row(category, body.get('business_key', ''))
    except Exception as e:
        raise HTTPException(400, str(e))


_XB_DELIVERY_DISABLED = 'Đơn giao thật chỉ được nạp tại UI02 – Chuẩn bị, In & Chốt giao hàng.'

@app.post('/api/source-import/{source_type}/preview')
async def api_source_preview(source_type: str, request: Request):
    try:
        if source_type == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        raw=await request.body()
        file_name=request.headers.get("X-File-Name","upload.xlsx")
        uploaded_by=request.headers.get("X-Uploaded-By","pilot")
        return preview_source(source_type,file_name,raw,uploaded_by)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/source-import/{batch_id}/commit')
def api_source_commit(batch_id: int):
    try:
        from .source_import_runtime import _conn as _src_conn
        with _src_conn() as conn:
            batch = conn.execute("SELECT source_type FROM src_batch WHERE batch_id=?", (batch_id,)).fetchone()
        if batch and batch["source_type"] == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        return commit_source(batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/source-import/batches')
def api_source_batches():
    try:
        return {"rows":list_batches()}
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/source-import/{batch_id}/errors.xlsx')
def api_source_errors(batch_id: int):
    try:
        filename,data=error_xlsx(batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )

@app.post('/api/xb-v2/dms-xa/preview')
async def xb_v2_preview_dms_xa(request: Request):
    try:
        return preview_dms_xa(request.headers.get("X-File-Name","DMS_Xa.xlsx"),await request.body(),request.headers.get("X-Uploaded-By","pilot"))
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-v2/batch/{batch_id}/commit')
def xb_v2_commit(batch_id: int):
    try: return commit_batch(batch_id)
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/xb-v2/history')
def xb_v2_history():
    try: return {"rows":history()}
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/xb-v2/batch/{batch_id}/errors.xlsx')
def xb_v2_errors(batch_id: int):
    try: filename,data=error_file(batch_id)
    except Exception as e: raise HTTPException(400,str(e))
    from fastapi.responses import Response
    return Response(content=data,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{filename}"'})

@app.post('/api/xb-v3/batch/{batch_id}/commit')
def api_vg_xb_v3_commit(batch_id: int):
    try:
        return vg_xb_v3_commit_batch(batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-v3/history')
def api_vg_xb_v3_history():
    try:
        return {"rows":vg_xb_v3_history()}
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-v4/history')
def api_vg_xb_v4_history():
    try:
        return {"rows":vg_xb_v4_history(),"diag":vg_xb_v4_diag()}
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-v4/{storage}/batch/{batch_id}/commit')
def api_vg_xb_v4_commit(storage: str, batch_id: int):
    try:
        if storage == "src_batch":
            from .source_import_runtime import _conn as _src_conn
            with _src_conn() as conn:
                batch = conn.execute("SELECT source_type FROM src_batch WHERE batch_id=?", (batch_id,)).fetchone()
            if batch and batch["source_type"] == "dms-mbw": raise ValueError(_XB_DELIVERY_DISABLED)
        return vg_xb_v4_commit(storage,batch_id)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.get('/api/xb-v4/diag')
def api_vg_xb_v4_diag():
    try:
        return vg_xb_v4_diag()
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-dms-mbw/preview')
async def api_xb_dms_mbw_preview(request: Request):
    try:
        raise ValueError(_XB_DELIVERY_DISABLED)
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post('/api/xb-dms-mbw/batch/{batch_id}/commit')
def api_xb_dms_mbw_commit(batch_id:int):
    try:raise ValueError(_XB_DELIVERY_DISABLED)
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/xb-dms-mbw/history')
def api_xb_dms_mbw_history():
    try:return {"rows":history_dms_mbw()}
    except Exception as e:raise HTTPException(400,str(e))

@app.get('/api/templates/dms-mbw-v2.xlsx')
def api_template_dms_mbw_v2():
    filename,data=build_dms_mbw_v2_template()
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':f'attachment; filename="{filename}"'}
    )


# ===== QTGH V1.0.11 STANDALONE DRAFT API =====
from app.qtgh_v02 import create_or_get_draft as _v111_create_or_get_draft
from app.qtgh_v02 import get_draft as _v111_get_draft
from app.qtgh_v02 import update_draft as _v111_update_draft

@app.post("/api/qtgh-v111/ui04/open-draft")
async def qtgh_v111_open_draft(request: Request):
    try:
        x=await request.json()
        source=str(x.get("source_system") or "").strip() or "DMS_MBW"
        order=str(x.get("ma_don_nguon") or "").strip()
        if not order: raise ValueError("Thiếu ma_don_nguon")
        d=_v111_create_or_get_draft(source,order)
        if isinstance(d,dict): return d
        if isinstance(d,int): return _v111_get_draft(d)
        return d
    except Exception as e:
        print(f"[QTGH V111 OPEN DRAFT ERROR] {e}")
        raise HTTPException(400,str(e))

@app.post("/api/qtgh-v111/ui04/draft/{did}/update")
async def qtgh_v111_update_draft(did:int,request:Request):
    try:return _v111_update_draft(did,await request.json())
    except Exception as e:
        print(f"[QTGH V111 UPDATE DRAFT ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.12 RECALC + PAYMENT + TRACE =====
import sqlite3 as _v112_sqlite3
from pathlib import Path as _v112_Path
from app.qtgh_v02 import create_or_get_draft as _v112_create_or_get_draft
from app.qtgh_v02 import get_draft as _v112_get_draft
from app.qtgh_v02 import update_draft as _v112_update_draft
from app.qtgh_v02 import set_draft_full_break as _v112_full_break

def _v112_db():
    return _v112_Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

def _v112_trace_init():
    c=_v112_sqlite3.connect(_v112_db())
    c.execute("""CREATE TABLE IF NOT EXISTS qtgh_ui04_draft_trace(
      source_system TEXT NOT NULL, ma_don_nguon TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'QT_NHAP', saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(source_system,ma_don_nguon))""")
    c.commit();c.close()

def _v112_trace(source,order):
    _v112_trace_init()
    c=_v112_sqlite3.connect(_v112_db())
    c.execute("""INSERT INTO qtgh_ui04_draft_trace(source_system,ma_don_nguon,status,saved_at)
      VALUES(?,?,'QT_NHAP',CURRENT_TIMESTAMP)
      ON CONFLICT(source_system,ma_don_nguon)
      DO UPDATE SET status='QT_NHAP',saved_at=CURRENT_TIMESTAMP""",(source,order))
    c.commit();c.close()

def _v112_src_order(did):
    c=_v112_sqlite3.connect(_v112_db());c.row_factory=_v112_sqlite3.Row
    r=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone();c.close()
    if not r:return ("DMS_MBW","")
    d=dict(r)
    return (str(d.get("source_system") or "DMS_MBW"),str(d.get("ma_don_nguon") or d.get("order_no") or d.get("ma_don") or ""))

_v112_trace_init()

@app.get("/api/qtgh-v112/ui04/pending-orders")
def qtgh_v112_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        x=qtgh_v082_pending_orders_readonly(ma_nvgh,ngay_giao,ma_lo)
        rows=x.get("rows",[]) if isinstance(x,dict) else []
        c=_v112_sqlite3.connect(_v112_db());c.row_factory=_v112_sqlite3.Row
        traces={(r["source_system"],r["ma_don_nguon"]) for r in c.execute("SELECT source_system,ma_don_nguon FROM qtgh_ui04_draft_trace")}
        c.close()
        for r in rows:
            key=(str(r.get("source_system") or ""),str(r.get("ma_don_nguon") or ""))
            r["qt_state"]="QT nháp" if key in traces else "Bình thường"
        if isinstance(x,dict):x["rows"]=rows
        return x
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v112/ui04/open-draft")
async def qtgh_v112_open_draft(request:Request):
    try:
        x=await request.json();source=str(x.get("source_system") or "").strip() or "DMS_MBW";order=str(x.get("ma_don_nguon") or "").strip()
        d=_v112_create_or_get_draft(source,order)
        if isinstance(d,int):d=_v112_get_draft(d)
        return d
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v112/ui04/draft/{did}/recalc")
async def qtgh_v112_recalc(did:int,request:Request):
    try:
        _v112_update_draft(did,await request.json());d=_v112_get_draft(did);s,o=_v112_src_order(did);_v112_trace(s,o);return d
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v112/ui04/draft/{did}/payment")
async def qtgh_v112_payment(did:int,request:Request):
    try:
        _v112_update_draft(did,await request.json());d=_v112_get_draft(did);s,o=_v112_src_order(did);_v112_trace(s,o);return d
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/api/qtgh-v112/ui04/draft/{did}/full-break")
def qtgh_v112_break(did:int):
    try:
        _v112_full_break(did);d=_v112_get_draft(did);s,o=_v112_src_order(did);_v112_trace(s,o);return d
    except Exception as e:raise HTTPException(400,str(e))



# ===== QTGH V1.0.13 UI04 L-ONLY =====
@app.get("/api/qtgh-v113/ui04/pending-orders")
def qtgh_v113_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        x = qtgh_v082_pending_orders_readonly(ma_nvgh,ngay_giao,ma_lo)
        rows = x.get("rows",[]) if isinstance(x,dict) else []
        out = []

        import sqlite3 as _v113_sqlite3
        from pathlib import Path as _v113_Path
        _db = _v113_Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

        for r in rows:
            loai = str(r.get("loai_don") or "").strip().upper()

            if not loai:
                c=_v113_sqlite3.connect(_db)
                c.row_factory=_v113_sqlite3.Row
                rr=c.execute(
                    "SELECT loai_don FROM qtgh_source_projection WHERE source_system=? AND ma_don_nguon=? LIMIT 1",
                    (str(r.get("source_system") or ""),str(r.get("ma_don_nguon") or ""))
                ).fetchone()
                c.close()
                loai=str(rr["loai_don"] if rr else "").strip().upper()

            if loai=="L":
                r["loai_don"]="L"
                out.append(r)

        if isinstance(x,dict):
            x["rows"]=out
            x["count"]=len(out)
        return x
    except Exception as e:
        print(f"[QTGH V113 UI04 L-ONLY ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.15 UI04 CANONICAL ONLY =====
@app.get("/api/qtgh-v115/ui04/pending-orders")
def qtgh_v115_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        x = qtgh_v082_pending_orders_readonly(ma_nvgh,ngay_giao,ma_lo)
        rows = x.get("rows",[]) if isinstance(x,dict) else []

        # Canonical QTGH source after rebuild: DMS_MBW only.
        # Legacy DMS/MBW rows from old backend path must never appear in UI04.
        out=[]
        seen=set()

        for r in rows:
            source=str(r.get("source_system") or "").strip().upper()
            loai=str(r.get("loai_don") or "").strip().upper()
            order=str(r.get("ma_don_nguon") or "").strip()

            if source!="DMS_MBW":
                continue
            if loai!="L":
                continue
            if not order or order in seen:
                continue

            seen.add(order)

            # Recalculate canonical order amount from current projection.
            import sqlite3 as _v115_sqlite3
            from pathlib import Path as _v115_Path
            _db=_v115_Path(__file__).resolve().parent.parent/"data"/"miniapp.db"

            c=_v115_sqlite3.connect(_db)
            c.row_factory=_v115_sqlite3.Row
            s=c.execute("""
                SELECT
                  COUNT(*) so_sku,
                  SUM(COALESCE(sl_hang_ban_dat,0)*COALESCE(don_gia_co_vat,0)
                      -COALESCE(ck_km_dong_goc,0)) so_phai_thu
                FROM qtgh_source_projection
                WHERE source_system='DMS_MBW'
                  AND UPPER(TRIM(loai_don))='L'
                  AND ma_don_nguon=?
            """,(order,)).fetchone()
            c.close()

            so_phai_thu=round(float(s["so_phai_thu"] or 0)) if s else 0
            so_sku=int(s["so_sku"] or 0) if s else 0

            r["source_system"]="DMS_MBW"
            r["loai_don"]="L"
            r["so_sku"]=so_sku
            r["tien_sau_ck_dong"]=so_phai_thu
            r["so_phai_thu"]=so_phai_thu

            # Default normal payment until draft says otherwise.
            if not r.get("draft_id"):
                r["tien_mat"]=so_phai_thu
                r["tien_ck"]=0
                r["cong_no_kh"]=0
                r["status_qt"]="BINH_THUONG_CHO_QT"

            out.append(r)

        if isinstance(x,dict):
            x["rows"]=out
            x["count"]=len(out)
        return x
    except Exception as e:
        print(f"[QTGH V115 UI04 CANONICAL ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.19 UI04 ALL ORDER TYPES =====
@app.get("/api/qtgh-v119/ui04/pending-orders")
def qtgh_v119_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        x = qtgh_v082_pending_orders_readonly(ma_nvgh,ngay_giao,ma_lo)
        rows = x.get("rows",[]) if isinstance(x,dict) else []

        import sqlite3 as _v119_sqlite3
        from pathlib import Path as _v119_Path
        _db = _v119_Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

        out=[]
        seen=set()

        for r in rows:
            source=str(r.get("source_system") or "").strip().upper()
            order=str(r.get("ma_don_nguon") or "").strip()

            if source!="DMS_MBW":
                continue
            if not order or order in seen:
                continue

            c=_v119_sqlite3.connect(_db)
            c.row_factory=_v119_sqlite3.Row
            s=c.execute(
                """
                SELECT MAX(UPPER(TRIM(loai_don))) loai_don,
                       COUNT(*) so_sku,
                       SUM(COALESCE(sl_hang_ban_dat,0)*COALESCE(don_gia_co_vat,0)
                           -COALESCE(ck_km_dong_goc,0)) so_phai_thu
                FROM qtgh_source_projection
                WHERE source_system='DMS_MBW'
                  AND ma_don_nguon=?
                """,
                (order,)
            ).fetchone()

            trace=None
            try:
                trace=c.execute(
                    """
                    SELECT status
                    FROM qtgh_ui04_draft_trace
                    WHERE ma_don_nguon=?
                    LIMIT 1
                    """,
                    (order,)
                ).fetchone()
            except Exception:
                pass
            c.close()

            if not s or not s["loai_don"]:
                continue

            loai=str(s["loai_don"]).strip().upper()
            if loai not in ("L","B"):
                continue

            seen.add(order)
            due=round(float(s["so_phai_thu"] or 0))

            r["source_system"]="DMS_MBW"
            r["loai_don"]=loai
            r["so_sku"]=int(s["so_sku"] or 0)
            r["tien_sau_ck_dong"]=due
            r["so_phai_thu"]=due
            r["qt_state"]="QT nháp" if trace else "Bình thường"

            if not r.get("draft_id"):
                r["tien_mat"]=due
                r["tien_ck"]=0
                r["cong_no_kh"]=0

            out.append(r)

        if isinstance(x,dict):
            x["rows"]=out
            x["count"]=len(out)
        return x
    except Exception as e:
        print(f"[QTGH V119 UI04 ALL TYPES ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.20 DRAFT-AWARE UI04 =====
@app.get("/api/qtgh-v120/ui04/pending-orders")
def qtgh_v120_pending_orders(ma_nvgh:str,ngay_giao:str=None,ma_lo:str=None):
    try:
        x = qtgh_v119_pending_orders(ma_nvgh,ngay_giao,ma_lo)
        rows = x.get("rows",[]) if isinstance(x,dict) else []

        import sqlite3 as _v120_sqlite3
        from pathlib import Path as _v120_Path
        _db = _v120_Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

        out=[]
        c=_v120_sqlite3.connect(_db)
        c.row_factory=_v120_sqlite3.Row

        for r in rows:
            order=str(r.get("ma_don_nguon") or "").strip()
            source=str(r.get("source_system") or "DMS_MBW").strip()
            draft_id=r.get("draft_id")

            if not draft_id:
                try:
                    cols=[z["name"] for z in c.execute("PRAGMA table_info(qtgh_draft_order)").fetchall()]
                    up={z.upper():z for z in cols}
                    src_col=up.get("SOURCE_SYSTEM")
                    ord_col=up.get("MA_DON_NGUON") or up.get("ORDER_NO") or up.get("MA_DON")
                    rr=None
                    if ord_col and src_col:
                        rr=c.execute(
                            f'SELECT id FROM qtgh_draft_order WHERE "{src_col}"=? AND "{ord_col}"=? ORDER BY id DESC LIMIT 1',
                            (source,order)
                        ).fetchone()
                    elif ord_col:
                        rr=c.execute(
                            f'SELECT id FROM qtgh_draft_order WHERE "{ord_col}"=? ORDER BY id DESC LIMIT 1',
                            (order,)
                        ).fetchone()
                    if rr:
                        draft_id=rr["id"]
                except Exception:
                    draft_id=None

            if draft_id:
                try:
                    d=_v112_get_draft(int(draft_id))
                    if isinstance(d,dict):
                        due=round(float(d.get("so_phai_thu_sau_qt") or 0))
                        cash=round(float(d.get("tien_mat") or 0))
                        bank=round(float(d.get("tien_ck_xac_nhan") or 0))
                        debt=round(float(d.get("cong_no_kh") or max(0,due-cash-bank)))

                        r["draft_id"]=draft_id
                        r["so_phai_thu"]=due
                        r["tien_sau_ck_dong"]=due
                        r["tien_mat"]=cash
                        r["tien_ck"]=bank
                        r["cong_no_kh"]=debt
                        r["qt_state"]="QT nháp"
                        r["status_qt"]="QT_NHAP"
                except Exception as e:
                    print(f"[QTGH V120 DRAFT READ WARN] {order}: {e}")

            out.append(r)

        c.close()
        if isinstance(x,dict):
            x["rows"]=out
            x["count"]=len(out)
        return x
    except Exception as e:
        print(f"[QTGH V120 PENDING ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.31 RECALC CK/KM AFTER DRAFT =====
import sqlite3 as _v131_sqlite3
from pathlib import Path as _v131_Path

def _v131_db():
    return _v131_Path(__file__).resolve().parent.parent / "data" / "miniapp.db"

def _v131_num(v):
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except Exception:
        return 0.0

def _v131_recalc_draft(did:int):
    db=_v131_db()
    c=_v131_sqlite3.connect(db)
    c.row_factory=_v131_sqlite3.Row

    line_cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_draft_line)")}
    order_cols={r["name"] for r in c.execute("PRAGMA table_info(qtgh_draft_order)")}

    draft_fk = "draft_id" if "draft_id" in line_cols else ("draft_order_id" if "draft_order_id" in line_cols else None)
    if not draft_fk:
        c.close()
        raise ValueError("Không xác định được khóa draft trong qtgh_draft_line")

    rows=c.execute(f'SELECT * FROM qtgh_draft_line WHERE "{draft_fk}"=?',(did,)).fetchall()

    total=0.0

    for rr in rows:
        d=dict(rr)

        hb_dat=_v131_num(d.get("sl_hang_ban_dat"))
        hb_tra=_v131_num(d.get("sl_hang_ban_tra"))
        km_dat=_v131_num(d.get("sl_hang_km_dat"))
        km_tra=_v131_num(d.get("sl_hang_km_tra"))
        price=_v131_num(d.get("don_gia_co_vat"))

        hb_thuc=max(0.0,hb_dat-hb_tra)
        km_thuc=max(0.0,km_dat-km_tra)

        ck_after=_v131_num(
            d.get("ck_km_dong_sau")
            if "ck_km_dong_sau" in d
            else d.get("ck_km_dong_goc")
        )

        line_amount=(hb_thuc+km_thuc)*price-ck_after

        sets=[]
        vals=[]

        if "sl_hang_ban_thuc_giao" in line_cols:
            sets.append('"sl_hang_ban_thuc_giao"=?')
            vals.append(hb_thuc)

        if "sl_hang_km_thuc_giao" in line_cols:
            sets.append('"sl_hang_km_thuc_giao"=?')
            vals.append(km_thuc)

        if "thanh_tien_sau" in line_cols:
            sets.append('"thanh_tien_sau"=?')
            vals.append(line_amount)

        if sets:
            vals.append(d["id"])
            c.execute(
                f'UPDATE qtgh_draft_line SET {",".join(sets)} WHERE id=?',
                vals
            )

        total += line_amount

    order=c.execute("SELECT * FROM qtgh_draft_order WHERE id=?",(did,)).fetchone()
    if not order:
        c.close()
        raise ValueError(f"Không tìm thấy draft order #{did}")

    od=dict(order)

    accumulation=_v131_num(od.get("accumulation_after"))
    display=_v131_num(od.get("display_after"))
    other=_v131_num(od.get("other_order_discount_after"))

    due=total-accumulation-display-other

    # Only tiny floating artifacts near zero are normalized.
    if -0.5 < due < 0:
        due=0.0

    cash=_v131_num(od.get("tien_mat"))
    bank=_v131_num(od.get("tien_ck_xac_nhan"))
    mode=str(od.get("payment_mode") or "").upper()

    if mode=="AUTO_CASH":
        cash=due
        bank=0.0
    elif mode=="BANK_100":
        cash=0.0
        bank=due

    debt=max(0.0,due-cash-bank)

    sets=[]
    vals=[]

    if "so_phai_thu_sau_qt" in order_cols:
        sets.append('"so_phai_thu_sau_qt"=?')
        vals.append(due)
    if "tien_mat" in order_cols:
        sets.append('"tien_mat"=?')
        vals.append(cash)
    if "tien_ck_xac_nhan" in order_cols:
        sets.append('"tien_ck_xac_nhan"=?')
        vals.append(bank)
    if "cong_no_kh" in order_cols:
        sets.append('"cong_no_kh"=?')
        vals.append(debt)

    if sets:
        vals.append(did)
        c.execute(
            f'UPDATE qtgh_draft_order SET {",".join(sets)} WHERE id=?',
            vals
        )

    c.commit()
    c.close()

@app.post("/api/qtgh-v131/ui04/draft/{did}/recalc")
async def qtgh_v131_recalc(did:int,request:Request):
    try:
        payload=await request.json()
        _v112_update_draft(did,payload)
        _v131_recalc_draft(did)

        d=_v112_get_draft(did)

        try:
            s,o=_v112_src_order(did)
            _v112_trace(s,o)
        except Exception:
            pass

        return d
    except Exception as e:
        print(f"[QTGH V131 RECALC ERROR] {e}")
        raise HTTPException(400,str(e))



# ===== QTGH V1.0.33 UI05 PRINT RECEIPT =====
@app.get("/api/qtgh-v133/ui05/cash/{rid}/print-data")
def qtgh_v133_ui05_print_data(rid:int):
    try:
        import sqlite3 as _v133_sqlite3
        from pathlib import Path as _v133_Path

        db=_v133_Path(__file__).resolve().parent.parent/"data"/"miniapp.db"
        c=_v133_sqlite3.connect(db)
        c.row_factory=_v133_sqlite3.Row

        r=c.execute("SELECT * FROM qtgh_cash_receipt WHERE id=?",(rid,)).fetchone()
        c.close()

        if not r:
            raise ValueError(f"Không tìm thấy phiếu thu #{rid}")

        d=dict(r)

        def pick(*names, default=""):
            for n in names:
                if n in d and d.get(n) is not None:
                    return d.get(n)
            return default

        return {
            "id": rid,
            "receipt_kind": pick("receipt_kind","source_type"),
            "source_type": pick("source_type","receipt_kind"),
            "ma_nvgh": pick("ma_nvgh","payer_code","employee_code"),
            "expected_amount": pick("expected_amount","amount_due", default=0),
            "actual_amount": pick("actual_amount","amount_received", default=0),
            "variance_amount": pick("variance_amount","shortage_amount", default=0),
            "resolution_code": pick("resolution_code"),
            "resolution_note": pick("resolution_note","note"),
            "received_at": pick("received_at","updated_at","created_at"),
            "status": pick("status"),
        }
    except Exception as e:
        print(f"[QTGH V133 PRINT DATA ERROR] {e}")
        raise HTTPException(400,str(e))



# QTGH_STABLE_CLEAN_V1_1_0
from .qtgh_stable import router as qtgh_stable_router
app.include_router(qtgh_stable_router)

from .qtgh_money_candidate import router as qtgh_money_candidate_router, init as qtgh_money_candidate_init
qtgh_money_candidate_init()
app.include_router(qtgh_money_candidate_router)

# QTGH_BA_V11_PHASE2B
from .qtgh_phase2b_v11 import router as qtgh_phase2b_v11_router
app.include_router(qtgh_phase2b_v11_router)

# QTGH_BA_V11_PHASE1_RESTORED
from .qtgh_print_v11 import router as qtgh_print_v11_router
app.include_router(qtgh_print_v11_router)

# QTGH_BA_V11_PHASE2A_RESTORED
from .qtgh_prep_v11 import router as qtgh_prep_v11_router
app.include_router(qtgh_prep_v11_router)
from .raw_ui02 import router as raw_ui02_router
app.include_router(raw_ui02_router)

# QTGH_BA_V11_PHASE3B_QR_SNAPSHOT
from .qtgh_qr_snapshot_v11 import router as qtgh_qr_snapshot_v11_router
app.include_router(qtgh_qr_snapshot_v11_router)

# QTGH_BA_V11_PHASE4A_FINALIZE
from .qtgh_finalize_v11 import router as qtgh_finalize_v11_router
app.include_router(qtgh_finalize_v11_router)

# QTGH_BA_V11_PHASE4B_HANDOFF
from .qtgh_handoff_v11 import router as qtgh_handoff_v11_router
app.include_router(qtgh_handoff_v11_router)

from .qtgh_reduction_report import router as qtgh_reduction_report_router
app.include_router(qtgh_reduction_report_router)

from .qtgh_bank_report import router as qtgh_bank_report_router
app.include_router(qtgh_bank_report_router)

from .qtgh_misa_export import router as qtgh_misa_export_router
app.include_router(qtgh_misa_export_router)
