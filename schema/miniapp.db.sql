CREATE UNIQUE INDEX idx_cash_receipt_no ON qtgh_cash_receipt(receipt_no) WHERE receipt_no IS NOT NULL;

CREATE INDEX ix_gh_settlement_order ON gh_settlement(order_no);

CREATE INDEX ix_kq_nvkd_target_stable_month
      ON kq_nvkd_target_stable(thang,ma_nv);

CREATE INDEX ix_qtgh_adjustment_stable_status
      ON qtgh_adjustment_stable(status,source_doc_type,source_doc_id);

CREATE INDEX ix_qtgh_delivery_audit_obj
      ON qtgh_delivery_audit(object_type,object_id,occurred_at);

CREATE INDEX ix_qtgh_money_adjust_source_candidate
      ON qtgh_money_adjust_candidate(source_type,source_id,status);

CREATE INDEX ix_qtgh_prep_line_order
      ON qtgh_prep_line(loai_don,ma_don_nguon);

CREATE INDEX ix_qtgh_prep_line_planned_lot
      ON qtgh_prep_line(planned_delivery_date,planned_lot_code,planned_delivery_staff_code);

CREATE INDEX ix_qtgh_wh_quantity_adjustment_line
      ON qtgh_wh_quantity_adjustment(line_id,status);

CREATE INDEX ix_qtgh_wh_return_request_status
      ON qtgh_wh_return_request(status,ma_nvgh);

CREATE UNIQUE INDEX ux_qtgh_bank_ma_tknh ON qtgh_receiving_bank_account(ma_tknh) WHERE ma_tknh IS NOT NULL AND TRIM(ma_tknh)<>'';

CREATE UNIQUE INDEX ux_qtgh_canonical_dms_mbw_row
    ON qtgh_source_projection(source_batch_id,source_row_no)
    WHERE source_system='DMS_MBW'
    ;

CREATE UNIQUE INDEX ux_qtgh_handoff_source_batch
                 ON qtgh_handoff(source_batch_id)
                 WHERE source_batch_id IS NOT NULL;

CREATE UNIQUE INDEX ux_qtgh_source_projection_source_row
ON qtgh_source_projection(source_system,source_batch_id,source_row_no)
;

CREATE TABLE bx_misa_v2_batch(
      batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_type TEXT NOT NULL,
      file_name TEXT,
      status TEXT NOT NULL,
      total_rows INTEGER DEFAULT 0,
      valid_rows INTEGER DEFAULT 0,
      error_rows INTEGER DEFAULT 0,
      created_at TEXT,
      committed_at TEXT,
      superseded_by_batch_id INTEGER
    );

CREATE TABLE bx_misa_v2_row(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id INTEGER NOT NULL,
      row_no INTEGER,
      ngay_chung_tu TEXT,
      so_chung_tu TEXT,
      ma_sku TEXT,
      ten_sku TEXT,
      dvt TEXT,
      so_luong REAL DEFAULT 0,
      trong_luong_dv REAL DEFAULT 0,
      khoi_luong_kg REAL DEFAULT 0,
      ma_kh TEXT,
      ten_kh TEXT,
      payload_json TEXT,
      error_text TEXT
    );

CREATE TABLE bx_pack_alloc_v3(
      pack_id INTEGER NOT NULL,
      participant_key TEXT NOT NULL,
      participant_type TEXT NOT NULL,
      ma_nv TEXT,
      loai_boc TEXT NOT NULL,
      kg REAL NOT NULL DEFAULT 0,
      don_gia REAL NOT NULL DEFAULT 0,
      thanh_tien REAL NOT NULL DEFAULT 0,
      PRIMARY KEY(pack_id,participant_key,loai_boc)
    );

CREATE TABLE bx_pack_member_v3(
      pack_id INTEGER NOT NULL,
      ma_nv TEXT NOT NULL,
      PRIMARY KEY(pack_id,ma_nv)
    );

CREATE TABLE bx_pack_trip_v3(
      pack_id INTEGER NOT NULL,
      source_type TEXT NOT NULL,
      so_chung_tu TEXT NOT NULL,
      ngay_chung_tu TEXT,
      loai_boc TEXT NOT NULL,
      kg REAL NOT NULL DEFAULT 0,
      PRIMARY KEY(pack_id,source_type,so_chung_tu)
    );

CREATE TABLE bx_pack_v3(
      pack_id INTEGER PRIMARY KEY AUTOINCREMENT,
      pack_code TEXT UNIQUE NOT NULL,
      pack_date TEXT NOT NULL,
      mode TEXT NOT NULL DEFAULT 'INTERNAL',
      status TEXT NOT NULL DEFAULT 'DRAFT',
      price_in_chan REAL NOT NULL DEFAULT 20000,
      price_in_le REAL NOT NULL DEFAULT 40000,
      price_out REAL NOT NULL DEFAULT 20000,
      price_change_reason TEXT,
      external_name TEXT,
      created_at TEXT,
      created_by TEXT,
      confirmed_at TEXT,
      confirmed_by TEXT
    );

CREATE TABLE bx_trip_class_v3(
      source_type TEXT NOT NULL,
      so_chung_tu TEXT NOT NULL,
      ngay_chung_tu TEXT,
      loai_boc TEXT NOT NULL,
      confirmed_at TEXT,
      confirmed_by TEXT,
      PRIMARY KEY(source_type,so_chung_tu)
    );

CREATE TABLE gh_cashier_receipt(
      receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
      ref_type TEXT NOT NULL,
      ref_id INTEGER NOT NULL,
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'PENDING',
      received_at TEXT,
      received_by TEXT
    );

CREATE TABLE gh_customer_debt(
      debt_id INTEGER PRIMARY KEY AUTOINCREMENT,
      settlement_id INTEGER NOT NULL,
      order_no TEXT,
      customer_code TEXT,
      original_amount REAL NOT NULL,
      paid_amount REAL NOT NULL DEFAULT 0,
      balance REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'OPEN',
      created_at TEXT
    );

CREATE TABLE gh_customer_debt_payment(
      payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
      debt_id INTEGER NOT NULL,
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      overpay_amount REAL NOT NULL DEFAULT 0,
      overpay_reason TEXT,
      created_at TEXT,
      created_by TEXT
    );

CREATE TABLE gh_delivery_debt(
      debt_id INTEGER PRIMARY KEY AUTOINCREMENT,
      settlement_id INTEGER NOT NULL,
      order_no TEXT,
      delivery_code TEXT,
      original_amount REAL NOT NULL,
      paid_amount REAL NOT NULL DEFAULT 0,
      balance REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'OPEN',
      created_at TEXT
    );

CREATE TABLE gh_delivery_debt_payment(
      payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
      debt_id INTEGER NOT NULL,
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      created_at TEXT,
      created_by TEXT
    );

CREATE TABLE gh_order_status(
        order_no TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'CHUA_QUYET_TOAN',
        updated_at TEXT,
        updated_by TEXT,
        note TEXT
    );

CREATE TABLE gh_settlement(
      settlement_id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_no TEXT NOT NULL,
      order_date TEXT,
      customer_code TEXT,
      sales_code TEXT,
      delivery_code TEXT,
      driver_code TEXT,
      vehicle TEXT,
      delivery_lot TEXT,
      status TEXT NOT NULL DEFAULT 'DRAFT',
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      customer_debt_amount REAL NOT NULL DEFAULT 0,
      amount_due REAL NOT NULL DEFAULT 0,
      delivery_debt_amount REAL NOT NULL DEFAULT 0,
      overpay_amount REAL NOT NULL DEFAULT 0,
      overpay_reason TEXT,
      created_at TEXT,
      created_by TEXT,
      committed_at TEXT,
      committed_by TEXT,
      adjustment_of INTEGER,
      adjustment_reason TEXT
    );

CREATE TABLE gh_settlement_line(
      line_id INTEGER PRIMARY KEY AUTOINCREMENT,
      settlement_id INTEGER NOT NULL,
      sku TEXT NOT NULL,
      sku_name TEXT,
      ordered_qty REAL NOT NULL DEFAULT 0,
      return_qty REAL NOT NULL DEFAULT 0,
      actual_qty REAL NOT NULL DEFAULT 0,
      unit_price_prevat REAL NOT NULL DEFAULT 0,
      vat_rate REAL NOT NULL DEFAULT 0,
      discount_amount REAL NOT NULL DEFAULT 0,
      gss_actual REAL NOT NULL DEFAULT 0,
      sales_actual REAL NOT NULL DEFAULT 0,
      FOREIGN KEY(settlement_id) REFERENCES gh_settlement(settlement_id)
    );

CREATE TABLE kq_nvkd_target_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      thang TEXT NOT NULL,
      ma_nv TEXT NOT NULL,
      ten_nv TEXT,
      ct_hc REAL NOT NULL DEFAULT 0,
      ct_pc REAL NOT NULL DEFAULT 0,
      ct_be REAL NOT NULL DEFAULT 0,
      ct_f REAL NOT NULL DEFAULT 0,
      ct_dstl REAL NOT NULL DEFAULT 0,
      ct_dstt REAL NOT NULL DEFAULT 0,
      ct_eco REAL NOT NULL DEFAULT 0,
      source_filename TEXT,
      imported_at TEXT NOT NULL,
      UNIQUE(thang,ma_nv)
    );

CREATE TABLE master_data_generic (category TEXT NOT NULL, business_key TEXT NOT NULL, payload_json TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(category,business_key));

CREATE TABLE qtgh_adjustment(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_doc_type TEXT NOT NULL,
      source_doc_id INTEGER NOT NULL,
      adjustment_type TEXT NOT NULL,
      delta_amount INTEGER NOT NULL DEFAULT 0,
      reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_by TEXT,
      approved_by TEXT,
      created_at TEXT,
      approved_at TEXT
    );

CREATE TABLE qtgh_adjustment_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_no TEXT UNIQUE NOT NULL,
      source_doc_type TEXT NOT NULL,
      source_doc_id INTEGER NOT NULL,
      source_ref TEXT,
      ma_nvgh TEXT,
      adjustment_type TEXT NOT NULL,
      delta_amount REAL NOT NULL DEFAULT 0,
      reason TEXT NOT NULL,
      note TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      before_value REAL,
      after_value REAL,
      effect_target TEXT,
      effect_applied INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      submitted_at TEXT,
      approved_at TEXT,
      approved_by TEXT
    );

CREATE TABLE qtgh_bank_reconciliation(
 draft_order_id INTEGER PRIMARY KEY, status TEXT NOT NULL,
 statement_date TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
 updated_by TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL,
 source_fingerprint TEXT NOT NULL);

CREATE TABLE qtgh_bank_reconciliation_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, draft_order_id INTEGER NOT NULL,
 old_json TEXT NOT NULL, new_json TEXT NOT NULL,
 updated_by TEXT NOT NULL, updated_at TEXT NOT NULL);

CREATE TABLE qtgh_cash_count_line_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      count_id INTEGER NOT NULL,
      denomination INTEGER NOT NULL,
      note_count INTEGER NOT NULL DEFAULT 0,
      amount REAL NOT NULL DEFAULT 0,
      UNIQUE(count_id,denomination),
      FOREIGN KEY(count_id) REFERENCES qtgh_cash_count_stable(id)
    );

CREATE TABLE qtgh_cash_count_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      count_date TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL DEFAULT 'DRAFT',
      received_total REAL NOT NULL DEFAULT 0,
      counted_total REAL NOT NULL DEFAULT 0,
      variance REAL NOT NULL DEFAULT 0,
      amount_words TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      locked_at TEXT
    , loose_amount REAL NOT NULL DEFAULT 0);

CREATE TABLE qtgh_cash_inventory(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      inventory_date TEXT NOT NULL,
      opening_balance INTEGER NOT NULL DEFAULT 0,
      receipt_total INTEGER NOT NULL DEFAULT 0,
      system_closing INTEGER NOT NULL DEFAULT 0,
      actual_count INTEGER,
      variance INTEGER,
      status TEXT NOT NULL DEFAULT 'NHAP',
      counted_by TEXT,
      locked_at TEXT,
      UNIQUE(inventory_date)
    );

CREATE TABLE qtgh_cash_receipt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_type TEXT NOT NULL,
      source_id INTEGER NOT NULL,
      ma_nvgh TEXT,
      expected_amount INTEGER NOT NULL DEFAULT 0,
      actual_amount INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'CHO_THU',
      created_at TEXT,
      locked_at TEXT,
      locked_by TEXT
    , session_key TEXT, receipt_kind TEXT, variance_amount INTEGER, resolution_code TEXT, resolution_note TEXT, received_at TEXT, received_by TEXT, receipt_no TEXT);

CREATE TABLE qtgh_customer_collect_alloc_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      collect_id INTEGER NOT NULL,
      debt_id INTEGER NOT NULL,
      ma_don_nguon TEXT,
      allocated_amount REAL NOT NULL DEFAULT 0,
      FOREIGN KEY(collect_id) REFERENCES qtgh_customer_collect_stable(id)
    );

CREATE TABLE qtgh_customer_collect_batch_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ma_nvgh TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'OPEN',
      cash_total REAL NOT NULL DEFAULT 0,
      bank_total REAL NOT NULL DEFAULT 0,
      cash_receipt_id INTEGER,
      created_at TEXT NOT NULL,
      closed_at TEXT
    );

CREATE TABLE qtgh_customer_collect_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id INTEGER NOT NULL,
      ma_kh_key TEXT NOT NULL,
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      bank_account TEXT,
      bank_txn_id TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(batch_id) REFERENCES qtgh_customer_collect_batch_stable(id)
    );

CREATE TABLE qtgh_customer_debt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      ma_kh_chuan TEXT,
      ma_don_nguon TEXT NOT NULL,
      ma_nvgh TEXT,
      original_amount INTEGER NOT NULL,
      collected_amount INTEGER NOT NULL DEFAULT 0,
      balance INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CON_NO',
      created_at TEXT
    );

CREATE TABLE qtgh_customer_debt_collection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_debt_id INTEGER NOT NULL,
      cash_amount INTEGER NOT NULL DEFAULT 0,
      bank_amount INTEGER NOT NULL DEFAULT 0,
      overpay_amount INTEGER NOT NULL DEFAULT 0,
      overpay_reason TEXT,
      created_at TEXT
    );

CREATE TABLE qtgh_debt_collect_allocation(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_collect_id INTEGER NOT NULL,
      customer_debt_id INTEGER NOT NULL,
      ma_don_nguon TEXT,
      allocated_amount INTEGER NOT NULL DEFAULT 0,
      allocation_order INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(customer_collect_id) REFERENCES qtgh_debt_collect_customer(id)
    );

CREATE TABLE qtgh_debt_collect_batch(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ma_nvgh TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'OPEN',
      cash_total INTEGER NOT NULL DEFAULT 0,
      bank_total INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      cash_receipt_id INTEGER,
      created_at TEXT,
      finalized_at TEXT
    );

CREATE TABLE qtgh_debt_collect_customer(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id INTEGER NOT NULL,
      customer_code TEXT NOT NULL,
      ma_kh_dms TEXT,
      ma_kh_mbw TEXT,
      cash_amount INTEGER NOT NULL DEFAULT 0,
      bank_amount INTEGER NOT NULL DEFAULT 0,
      bank_account TEXT,
      bank_txn_id TEXT,
      total_amount INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'DRAFT',
      created_at TEXT,
      FOREIGN KEY(batch_id) REFERENCES qtgh_debt_collect_batch(id)
    );

CREATE TABLE qtgh_delivery_audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL,
      object_type TEXT NOT NULL,
      object_id TEXT NOT NULL,
      username TEXT,
      occurred_at TEXT NOT NULL,
      before_json TEXT,
      after_json TEXT,
      reason TEXT,
      source_note TEXT
    );

CREATE TABLE qtgh_delivery_finalization(
      finalization_id TEXT PRIMARY KEY,
      print_lot_id TEXT NOT NULL UNIQUE,
      actual_delivery_date TEXT NOT NULL,
      actual_delivery_staff_code TEXT,
      actual_driver_code TEXT,
      actual_vehicle_code TEXT,
      actual_lot_code TEXT NOT NULL,
      reason TEXT,
      warehouse_source_note TEXT,
      finalized_by TEXT NOT NULL,
      finalized_at TEXT NOT NULL,
      finalize_status TEXT NOT NULL DEFAULT 'FINALIZED',
      version INTEGER NOT NULL,
      handoff_id TEXT,
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id)
    );

CREATE TABLE qtgh_draft_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sl_hang_ban_dat TEXT NOT NULL,
      sl_hang_ban_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_ban_thuc_giao TEXT NOT NULL DEFAULT '0',
      sl_hang_km_dat TEXT NOT NULL DEFAULT '0',
      sl_hang_km_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_km_thuc_giao TEXT NOT NULL DEFAULT '0',
      don_gia_co_vat INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_goc INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_sau INTEGER NOT NULL DEFAULT 0,
      thanh_tien_sau INTEGER NOT NULL DEFAULT 0
    );

CREATE TABLE qtgh_draft_order(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_system TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'NHAP',
      vo_type TEXT NOT NULL DEFAULT 'GIAO_DU',
      accumulation_after INTEGER NOT NULL DEFAULT 0,
      display_after INTEGER NOT NULL DEFAULT 0,
      other_order_discount_after INTEGER NOT NULL DEFAULT 0,
      so_phai_thu_goc INTEGER NOT NULL DEFAULT 0,
      so_phai_thu_sau_qt INTEGER NOT NULL DEFAULT 0,
      tien_mat INTEGER NOT NULL DEFAULT 0,
      tien_ck_xac_nhan INTEGER NOT NULL DEFAULT 0,
      so_du_co_su_dung INTEGER NOT NULL DEFAULT 0,
      can_tru INTEGER NOT NULL DEFAULT 0,
      cong_no_kh INTEGER NOT NULL DEFAULT 0,
      bank_txn_id TEXT,
      bank_account TEXT,
      created_at TEXT,
      updated_at TEXT,
      locked_at TEXT,
      locked_by TEXT,
      UNIQUE(source_system,ma_don_nguon)
    );

CREATE TABLE qtgh_employee_collect_stable(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_debt_id INTEGER NOT NULL,
      ma_nvgh TEXT NOT NULL,
      ten_nv TEXT,
      cash_amount REAL NOT NULL DEFAULT 0,
      bank_amount REAL NOT NULL DEFAULT 0,
      bank_account TEXT,
      bank_txn_id TEXT,
      cash_receipt_id INTEGER,
      status TEXT NOT NULL DEFAULT 'OPEN',
      created_at TEXT NOT NULL
    );

CREATE TABLE qtgh_employee_debt(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cash_receipt_id INTEGER NOT NULL,
      ma_nvgh TEXT,
      original_amount INTEGER NOT NULL,
      collected_amount INTEGER NOT NULL DEFAULT 0,
      balance INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CON_NO',
      created_at TEXT
    );

CREATE TABLE qtgh_employee_debt_collection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_debt_id INTEGER NOT NULL,
      planned_amount INTEGER NOT NULL,
      cash_receipt_id INTEGER,
      created_at TEXT
    );

CREATE TABLE qtgh_handoff(
      handoff_id TEXT PRIMARY KEY,
      print_lot_id TEXT NOT NULL UNIQUE,
      finalization_id TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL,
      order_count INTEGER NOT NULL DEFAULT 0,
      line_count INTEGER NOT NULL DEFAULT 0,
      performed_by TEXT,
      performed_at TEXT,
      error_text TEXT, source_batch_id INTEGER, projection_checksum TEXT,
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id),
      FOREIGN KEY(finalization_id) REFERENCES qtgh_delivery_finalization(finalization_id)
    );

CREATE TABLE qtgh_money_adjust_candidate(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_no TEXT UNIQUE,
      source_type TEXT NOT NULL CHECK(source_type IN ('ORDER','SESSION')),
      source_id INTEGER NOT NULL,
      source_ref TEXT NOT NULL,
      case_ref TEXT,
      delta_amount INTEGER NOT NULL CHECK(delta_amount<>0),
      before_amount INTEGER NOT NULL,
      after_amount INTEGER NOT NULL CHECK(after_amount>=0),
      reason TEXT NOT NULL,
      note TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_at TEXT NOT NULL,
      submitted_at TEXT,
      approved_at TEXT,
      approved_by TEXT
    );

CREATE TABLE qtgh_money_effect_candidate(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_id INTEGER NOT NULL,
      party TEXT NOT NULL CHECK(party IN ('KH','NVGH')),
      effect_type TEXT NOT NULL CHECK(effect_type IN ('DEBT_ADD','DEBT_REDUCE','CREDIT')),
      debt_id INTEGER,
      amount INTEGER NOT NULL CHECK(amount>0),
      FOREIGN KEY(adjustment_id) REFERENCES qtgh_money_adjust_candidate(id)
    );

CREATE TABLE qtgh_payment_qr_snapshot(
      qr_snapshot_id TEXT PRIMARY KEY,
      print_batch_id TEXT NOT NULL,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      bank_id INTEGER NOT NULL,
      bank_name TEXT NOT NULL,
      account_no TEXT NOT NULL,
      account_name TEXT,
      amount INTEGER NOT NULL,
      transfer_content TEXT NOT NULL,
      payload_text TEXT NOT NULL,
      payload_checksum TEXT NOT NULL,
      created_at TEXT NOT NULL, qr_image_path TEXT, qr_image_checksum TEXT, quicklink_url TEXT,
      FOREIGN KEY(print_batch_id) REFERENCES qtgh_print_batch(print_batch_id),
      UNIQUE(print_batch_id,loai_don,ma_don_nguon)
    );

CREATE TABLE qtgh_prep_batch(
      prep_batch_id TEXT PRIMARY KEY,
      source_file_name TEXT NOT NULL,
      source_checksum TEXT NOT NULL,
      uploaded_by TEXT,
      uploaded_at TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'DA_NAP_HOP_LE',
      total_orders INTEGER NOT NULL DEFAULT 0,
      total_lines INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      validation_json TEXT,
      UNIQUE(source_checksum)
    );

CREATE TABLE qtgh_prep_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      prep_batch_id TEXT NOT NULL,
      source_row_no INTEGER,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      order_date TEXT NOT NULL,
      planned_delivery_date TEXT NOT NULL,
      planned_delivery_staff_code TEXT,
      planned_driver_code TEXT,
      planned_vehicle_code TEXT,
      planned_lot_code TEXT,
      delivery_sequence INTEGER,
      receiving_bank_id INTEGER,
      ma_nvtt TEXT,
      ma_kh_chuan TEXT,
      ma_kh_mbw TEXT,
      ma_kh_dms TEXT,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sale_qty_su TEXT NOT NULL DEFAULT '0',
      promo_qty_su TEXT NOT NULL DEFAULT '0',
      unit_price_vat INTEGER NOT NULL DEFAULT 0,
      line_discount INTEGER NOT NULL DEFAULT 0,
      order_reward_accum INTEGER NOT NULL DEFAULT 0,
      order_reward_display INTEGER NOT NULL DEFAULT 0,
      amount_due_order INTEGER NOT NULL DEFAULT 0,
      raw_payload_json TEXT,
      created_at TEXT NOT NULL, order_reward_other INTEGER NOT NULL DEFAULT 0, don_app TEXT,
      FOREIGN KEY(prep_batch_id) REFERENCES qtgh_prep_batch(prep_batch_id),
      UNIQUE(prep_batch_id,source_row_no,ma_sku)
    );

CREATE TABLE qtgh_print_batch(
      print_batch_id TEXT PRIMARY KEY,
      print_lot_id TEXT NOT NULL,
      print_version INTEGER NOT NULL,
      pdf_path TEXT,
      pdf_checksum TEXT,
      snapshot_json TEXT NOT NULL,
      created_by TEXT,
      created_at TEXT NOT NULL, snapshot_checksum TEXT, status TEXT DEFAULT 'SNAPSHOT_LOCKED',
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id),
      UNIQUE(print_lot_id,print_version)
    );

CREATE TABLE qtgh_print_lot(
      print_lot_id TEXT PRIMARY KEY,
      prep_batch_id TEXT NOT NULL,
      planned_delivery_date TEXT NOT NULL,
      planned_delivery_staff_code TEXT,
      planned_driver_code TEXT,
      planned_vehicle_code TEXT,
      planned_lot_code TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'DA_NAP_HOP_LE',
      order_count INTEGER NOT NULL DEFAULT 0,
      customer_count INTEGER NOT NULL DEFAULT 0,
      total_amount INTEGER NOT NULL DEFAULT 0,
      created_by TEXT,
      created_at TEXT NOT NULL,
      version INTEGER NOT NULL DEFAULT 1,
      FOREIGN KEY(prep_batch_id) REFERENCES qtgh_prep_batch(prep_batch_id)
    );

CREATE TABLE qtgh_print_lot_order(
      print_lot_id TEXT NOT NULL,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      PRIMARY KEY(print_lot_id,loai_don,ma_don_nguon),
      FOREIGN KEY(print_lot_id) REFERENCES qtgh_print_lot(print_lot_id)
    );

CREATE TABLE qtgh_receiving_bank_account(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      bank_name TEXT NOT NULL,
      account_no TEXT NOT NULL,
      account_name TEXT,
      status TEXT NOT NULL DEFAULT 'ACTIVE', ma_tknh TEXT, bank_bin TEXT, qr_service_code TEXT DEFAULT 'QRIBFTTA',
      UNIQUE(bank_name,account_no)
    );

CREATE TABLE qtgh_return_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      return_note_id INTEGER NOT NULL,
      ma_sku TEXT NOT NULL,
      sl_hang_ban_tra TEXT NOT NULL DEFAULT '0',
      sl_hang_km_tra TEXT NOT NULL DEFAULT '0',
      kho_nhan_hang_ban TEXT NOT NULL DEFAULT '0',
      kho_nhan_hang_km TEXT NOT NULL DEFAULT '0'
    );

CREATE TABLE qtgh_return_note(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      draft_order_id INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'CHO_KHO',
      created_at TEXT,
      locked_at TEXT
    );

CREATE TABLE qtgh_session(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ma_phien_qt TEXT UNIQUE NOT NULL,
      ngay_giao TEXT,
      ma_nvgh TEXT,
      ma_lo TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_at TEXT,
      locked_at TEXT,
      locked_by TEXT
    );

CREATE TABLE qtgh_session_order(
      session_id INTEGER NOT NULL,
      draft_order_id INTEGER NOT NULL,
      PRIMARY KEY(session_id,draft_order_id)
    );

CREATE TABLE qtgh_source_projection(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_system TEXT NOT NULL,
      source_batch_id INTEGER,
      source_row_no INTEGER,
      loai_don TEXT NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      ngay_don TEXT,
      ngay_giao TEXT,
      ma_lo TEXT,
      ma_nvgh TEXT,
      ma_lai_xe TEXT,
      ma_phuong_tien TEXT,
      ma_nvtt TEXT,
      ma_kh_chuan TEXT,
      ma_kh_mbw TEXT,
      ma_kh_dms TEXT,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sl_hang_ban_dat TEXT NOT NULL DEFAULT '0',
      sl_hang_km_dat TEXT NOT NULL DEFAULT '0',
      don_gia_co_vat INTEGER NOT NULL DEFAULT 0,
      ck_km_dong_goc INTEGER NOT NULL DEFAULT 0,
      thuong_tich_luy_goc INTEGER NOT NULL DEFAULT 0,
      thuong_trung_bay_goc INTEGER NOT NULL DEFAULT 0,
      source_hash TEXT, ten_kh TEXT, ten_nvtt TEXT,
      UNIQUE(source_system,source_batch_id,source_row_no)
    );

CREATE TABLE qtgh_ui04_draft_trace(
      source_system TEXT NOT NULL, ma_don_nguon TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'QT_NHAP', saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(source_system,ma_don_nguon));

CREATE TABLE qtgh_wh_quantity_adjustment(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      adjustment_no TEXT UNIQUE NOT NULL,
      request_id INTEGER NOT NULL,
      line_id INTEGER NOT NULL,
      delta_qty REAL NOT NULL,
      before_qty REAL NOT NULL,
      after_qty REAL NOT NULL,
      reason TEXT NOT NULL,
      note TEXT,
      status TEXT NOT NULL DEFAULT 'NHAP',
      created_at TEXT NOT NULL,
      submitted_at TEXT,
      approved_at TEXT,
      approved_by TEXT,
      FOREIGN KEY(request_id) REFERENCES qtgh_wh_return_request(id),
      FOREIGN KEY(line_id) REFERENCES qtgh_wh_return_request_line(id)
    );

CREATE TABLE qtgh_wh_return_request(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      request_no TEXT UNIQUE,
      ma_nvgh TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'CHO_NHAN',
      created_at TEXT NOT NULL,
      received_at TEXT,
      note TEXT
    );

CREATE TABLE qtgh_wh_return_request_line(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      request_id INTEGER NOT NULL,
      ma_sku TEXT NOT NULL,
      ten_sku TEXT,
      sl_hb_phai_tra REAL NOT NULL DEFAULT 0,
      sl_km_phai_tra REAL NOT NULL DEFAULT 0,
      sl_phai_tra REAL NOT NULL DEFAULT 0,
      sl_thuc_nhan REAL NOT NULL DEFAULT 0,
      FOREIGN KEY(request_id) REFERENCES qtgh_wh_return_request(id)
    );

CREATE TABLE qtgh_wh_return_request_order(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      request_id INTEGER NOT NULL,
      draft_order_id INTEGER NOT NULL,
      ma_don_nguon TEXT NOT NULL,
      UNIQUE(draft_order_id),
      FOREIGN KEY(request_id) REFERENCES qtgh_wh_return_request(id)
    );

CREATE TABLE receipt_daily_sequence(day TEXT PRIMARY KEY, last_seq INTEGER NOT NULL CHECK(last_seq>0));

CREATE TABLE receipt_number_registry(
      receipt_id INTEGER PRIMARY KEY, receipt_no TEXT NOT NULL UNIQUE,
      day TEXT NOT NULL, seq INTEGER NOT NULL, assigned_at TEXT NOT NULL,
      UNIQUE(day,seq));

CREATE TABLE src_batch(
        batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        uploaded_by TEXT,
        uploaded_at TEXT NOT NULL,
        total_rows INTEGER NOT NULL DEFAULT 0,
        valid_rows INTEGER NOT NULL DEFAULT 0,
        error_rows INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        UNIQUE(source_type,file_hash)
    );

CREATE TABLE src_row(
        row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER NOT NULL,
        sheet_name TEXT,
        row_no INTEGER,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL,
        error_text TEXT,
        FOREIGN KEY(batch_id) REFERENCES src_batch(batch_id)
    );

CREATE TABLE user_permission_matrix (username TEXT PRIMARY KEY,gh TEXT NOT NULL DEFAULT 'NONE',xb TEXT NOT NULL DEFAULT 'NONE',kq TEXT NOT NULL DEFAULT 'NONE',bx TEXT NOT NULL DEFAULT 'NONE',dm TEXT NOT NULL DEFAULT 'NONE',export_excel INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL);

CREATE TABLE xb_dms_mbw_batch(
      batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_name TEXT,file_hash TEXT UNIQUE,uploaded_by TEXT,uploaded_at TEXT,
      total_rows INTEGER DEFAULT 0,valid_rows INTEGER DEFAULT 0,error_rows INTEGER DEFAULT 0,status TEXT
    , replaces_batch_id INTEGER, superseded_by_batch_id INTEGER, superseded_at TEXT);

CREATE TABLE xb_dms_mbw_row(
      row_id INTEGER PRIMARY KEY AUTOINCREMENT,batch_id INTEGER,row_no INTEGER,
      payload_json TEXT,status TEXT,error_text TEXT
    );

CREATE TABLE xb_misa_bu_batch(
      batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_name TEXT,
      file_hash TEXT UNIQUE,
      uploaded_by TEXT,
      uploaded_at TEXT,
      total_rows INTEGER DEFAULT 0,
      valid_rows INTEGER DEFAULT 0,
      error_rows INTEGER DEFAULT 0,
      status TEXT
    , replaces_batch_id INTEGER, superseded_by_batch_id INTEGER, superseded_at TEXT);

CREATE TABLE xb_misa_bu_row(
      row_id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id INTEGER,
      sheet_name TEXT,
      row_no INTEGER,
      payload_json TEXT,
      status TEXT,
      error_text TEXT
    );

CREATE TABLE xb_src_batch_v2(batch_id INTEGER PRIMARY KEY AUTOINCREMENT,source_type TEXT,file_name TEXT,file_hash TEXT,uploaded_by TEXT,uploaded_at TEXT,total_rows INTEGER DEFAULT 0,valid_rows INTEGER DEFAULT 0,error_rows INTEGER DEFAULT 0,status TEXT, replaces_batch_id INTEGER, superseded_by_batch_id INTEGER, superseded_at TEXT,UNIQUE(source_type,file_hash));

CREATE TABLE xb_src_row_v2(row_id INTEGER PRIMARY KEY AUTOINCREMENT,batch_id INTEGER,sheet_name TEXT,row_no INTEGER,payload_json TEXT,status TEXT,error_text TEXT);

CREATE TRIGGER receipt_number_assign AFTER INSERT ON qtgh_cash_receipt
    BEGIN
      INSERT INTO receipt_daily_sequence(day,last_seq) VALUES(date('now','+7 hours'),1)
        ON CONFLICT(day) DO UPDATE SET last_seq=last_seq+1;
      INSERT INTO receipt_number_registry(receipt_id,receipt_no,day,seq,assigned_at)
        SELECT NEW.id, substr(day,3,2)||'_'||substr(day,6,2)||'_'||substr(day,9,2)||'_'||printf('%03d',last_seq), day,last_seq,datetime('now')
        FROM receipt_daily_sequence WHERE day=date('now','+7 hours');
      UPDATE qtgh_cash_receipt SET receipt_no=(SELECT receipt_no FROM receipt_number_registry WHERE receipt_id=NEW.id) WHERE id=NEW.id;
    END;

CREATE TRIGGER receipt_number_immutable BEFORE UPDATE OF receipt_no ON qtgh_cash_receipt
      WHEN OLD.receipt_no IS NOT NULL AND NEW.receipt_no IS NOT OLD.receipt_no
      BEGIN SELECT RAISE(ABORT,'Receipt number is immutable'); END;

CREATE TRIGGER receipt_registry_no_delete BEFORE DELETE ON receipt_number_registry
          BEGIN SELECT RAISE(ABORT,'Receipt number registry is permanent'); END;

CREATE TRIGGER receipt_registry_no_update BEFORE UPDATE ON receipt_number_registry
          BEGIN SELECT RAISE(ABORT,'Receipt number registry is permanent'); END;

CREATE TRIGGER trg_qtgh_block_legacy_projection
    BEFORE INSERT ON qtgh_source_projection
    WHEN NEW.source_system IN ('DMS','MBW')
      AND EXISTS (
        SELECT 1 FROM xb_dms_mbw_batch b
        WHERE b.batch_id = NEW.source_batch_id
      )
    BEGIN
      SELECT RAISE(IGNORE);
    END;