-- Mini App Vinh Giang V1.0 - DEV01 core schema skeleton
-- PostgreSQL 15+
CREATE TABLE md_product (
  product_id BIGSERIAL PRIMARY KEY,
  ma_sku VARCHAR(50) NOT NULL UNIQUE,
  ten_sku TEXT NOT NULL,
  ma_nhan VARCHAR(30), bu VARCHAR(30), dvt_co_so VARCHAR(20) DEFAULT 'SU',
  so_su_thung NUMERIC(18,3), trong_luong_su NUMERIC(18,3), trong_luong_thung NUMERIC(18,3),
  vat_rate NUMERIC(9,6), trang_thai VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), created_by BIGINT,
  updated_at TIMESTAMPTZ, updated_by BIGINT
);

CREATE TABLE md_price_history (
  price_id BIGSERIAL PRIMARY KEY,
  ma_sku VARCHAR(50) NOT NULL REFERENCES md_product(ma_sku),
  tu_ngay DATE NOT NULL, den_ngay DATE,
  don_gia_chua_vat NUMERIC(18,2) NOT NULL,
  vat_rate NUMERIC(9,6) NOT NULL,
  don_gia_co_vat NUMERIC(18,2) NOT NULL,
  nguon_gia VARCHAR(30), trang_thai VARCHAR(20) DEFAULT 'ACTIVE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), created_by BIGINT,
  CHECK (den_ngay IS NULL OR den_ngay >= tu_ngay)
);
CREATE INDEX ix_price_sku_effective ON md_price_history(ma_sku, tu_ngay DESC);

CREATE TABLE md_employee (
  employee_id BIGSERIAL PRIMARY KEY,
  ma_nv VARCHAR(20) NOT NULL UNIQUE,
  ten_nv TEXT NOT NULL,
  nhom_nv VARCHAR(30), ma_vung VARCHAR(30), bo_phan VARCHAR(100), mang VARCHAR(30),
  trang_thai VARCHAR(20) DEFAULT 'ACTIVE', created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE md_employee_code (
  employee_code_id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES md_employee(employee_id),
  loai_ma VARCHAR(30) NOT NULL, ma_nghiep_vu VARCHAR(50) NOT NULL,
  he_thong VARCHAR(30), tu_ngay DATE NOT NULL, den_ngay DATE, trang_thai VARCHAR(20) DEFAULT 'ACTIVE'
);
CREATE INDEX ix_empcode_lookup ON md_employee_code(loai_ma, ma_nghiep_vu, tu_ngay, den_ngay);

CREATE TABLE md_customer (
  customer_id BIGSERIAL PRIMARY KEY,
  ma_kh_chuan VARCHAR(30) NOT NULL UNIQUE,
  ten_kh TEXT, sdt_chinh VARCHAR(10), ma_dia_ban VARCHAR(30), trang_thai VARCHAR(30) DEFAULT 'NORMAL'
);
CREATE TABLE md_customer_source_code (
  customer_source_id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES md_customer(customer_id),
  source_system VARCHAR(20) NOT NULL, source_code VARCHAR(50) NOT NULL,
  UNIQUE(source_system, source_code)
);

CREATE TABLE src_batch (
  batch_id BIGSERIAL PRIMARY KEY, source_system VARCHAR(20) NOT NULL,
  file_name TEXT NOT NULL, file_hash VARCHAR(128) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'UPLOADED',
  total_rows INT DEFAULT 0, valid_rows INT DEFAULT 0, error_rows INT DEFAULT 0,
  uploaded_by BIGINT, uploaded_at TIMESTAMPTZ DEFAULT now(), committed_at TIMESTAMPTZ,
  UNIQUE(source_system, file_hash)
);
CREATE TABLE src_row_error (
  error_id BIGSERIAL PRIMARY KEY, batch_id BIGINT NOT NULL REFERENCES src_batch(batch_id),
  row_no INT NOT NULL, error_code VARCHAR(50) NOT NULL, severity VARCHAR(10) NOT NULL,
  message TEXT, raw_payload JSONB
);

CREATE TABLE gh_order (
  gh_order_id BIGSERIAL PRIMARY KEY,
  source_order_no VARCHAR(80) NOT NULL, order_date DATE NOT NULL,
  ma_nv_kd VARCHAR(20), ma_nv_gh VARCHAR(20), ma_lai_xe VARCHAR(20), phuong_tien VARCHAR(50), lo_giao VARCHAR(30),
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', finalized_at TIMESTAMPTZ, finalized_by BIGINT
);
CREATE INDEX ix_gh_order_date ON gh_order(order_date);
CREATE TABLE gh_order_line (
  gh_line_id BIGSERIAL PRIMARY KEY, gh_order_id BIGINT NOT NULL REFERENCES gh_order(gh_order_id),
  ma_sku VARCHAR(50) NOT NULL REFERENCES md_product(ma_sku),
  sl_hang_ban_dat NUMERIC(18,3) NOT NULL DEFAULT 0,
  sl_hang_ban_tra NUMERIC(18,3) NOT NULL DEFAULT 0,
  sl_hang_ban_thuc_giao NUMERIC(18,3) NOT NULL DEFAULT 0,
  ck_bang_tien NUMERIC(18,2) NOT NULL DEFAULT 0,
  don_gia_chua_vat_ap_dung NUMERIC(18,2) NOT NULL,
  vat_rate_ap_dung NUMERIC(9,6) NOT NULL,
  don_gia_co_vat_ap_dung NUMERIC(18,2) NOT NULL,
  gss_thuc_te NUMERIC(18,2) NOT NULL DEFAULT 0,
  doanh_so_thuc_giao NUMERIC(18,2) NOT NULL DEFAULT 0,
  UNIQUE(gh_order_id, ma_sku)
);

CREATE TABLE adjustment_document (
  adjustment_id BIGSERIAL PRIMARY KEY,
  adjustment_no VARCHAR(50) NOT NULL UNIQUE,
  module_code VARCHAR(20) NOT NULL,
  original_document_type VARCHAR(30) NOT NULL,
  original_document_id BIGINT NOT NULL,
  reason TEXT NOT NULL,
  delta_payload JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'FINAL',
  created_by BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
  audit_id BIGSERIAL PRIMARY KEY,
  event_id UUID NOT NULL UNIQUE,
  event_type VARCHAR(50) NOT NULL, module_code VARCHAR(20), entity_type VARCHAR(40), entity_id VARCHAR(80),
  actor_user_id BIGINT, reason TEXT, before_data JSONB, after_data JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE bx_daily_sheet (
  bx_sheet_id BIGSERIAL PRIMARY KEY, sheet_no VARCHAR(50) NOT NULL UNIQUE,
  work_date DATE NOT NULL, direction VARCHAR(10) NOT NULL CHECK(direction IN ('IN','OUT')),
  work_type VARCHAR(15) NOT NULL CHECK(work_type IN ('INTERNAL','OUTSOURCE')),
  total_kg NUMERIC(18,3) NOT NULL, unit_price NUMERIC(18,2) NOT NULL, total_amount NUMERIC(18,2) NOT NULL,
  price_override_reason TEXT, vendor_name TEXT, status VARCHAR(20) DEFAULT 'DRAFT',
  finalized_at TIMESTAMPTZ, finalized_by BIGINT
);
CREATE TABLE bx_allocation (
  allocation_id BIGSERIAL PRIMARY KEY, bx_sheet_id BIGINT NOT NULL REFERENCES bx_daily_sheet(bx_sheet_id),
  ma_nv VARCHAR(20) NOT NULL, allocated_kg NUMERIC(18,3) NOT NULL, allocated_amount NUMERIC(18,2) NOT NULL,
  UNIQUE(bx_sheet_id, ma_nv)
);

-- Application layer must enforce:
-- 1) non-overlapping md_price_history periods per ma_sku;
-- 2) immutable FINAL documents; corrections through adjustment_document;
-- 3) only single designated SUPER_ADMIN may unlock, with reason + audit event;
-- 4) formulas and rounding rules from the approved technical package.
