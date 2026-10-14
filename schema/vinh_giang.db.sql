CREATE UNIQUE INDEX ux_import_batch_hash ON import_batch(file_hash, template_key);

CREATE TABLE adjustment_doc(adjustment_id TEXT PRIMARY KEY,original_doc_type TEXT NOT NULL,original_doc_id TEXT NOT NULL,direction TEXT NOT NULL CHECK(direction IN ('INCREASE','DECREASE')),amount REAL DEFAULT 0,quantity REAL DEFAULT 0,reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'DRAFT',created_by TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,posted_at TEXT);

CREATE TABLE app_user(username TEXT PRIMARY KEY,full_name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL,is_active INTEGER NOT NULL DEFAULT 1,must_change_password INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL,action TEXT NOT NULL,entity_type TEXT,entity_id TEXT,reason TEXT,old_json TEXT,new_json TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE auth_session(token TEXT PRIMARY KEY,username TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,expires_at TEXT NOT NULL,FOREIGN KEY(username) REFERENCES app_user(username));

CREATE TABLE dm_customer_map(
          ma_kh_nguon TEXT PRIMARY KEY, ma_kh_chuan TEXT NOT NULL, source_system TEXT
        );

CREATE TABLE dm_personnel_code(
          ma_nghiep_vu TEXT PRIMARY KEY, ma_nv TEXT NOT NULL, loai_ma TEXT, trang_thai TEXT DEFAULT 'ACTIVE'
        );

CREATE TABLE dm_product(
          ma_sku TEXT PRIMARY KEY, ten_sku TEXT, su_thung REAL NOT NULL, trong_luong_su REAL NOT NULL,
          vat_rate REAL NOT NULL DEFAULT 0.08, bu TEXT, nhan TEXT, trang_thai TEXT DEFAULT 'ACTIVE'
        );

CREATE TABLE import_batch(
          batch_id TEXT PRIMARY KEY, template_key TEXT NOT NULL, template_version TEXT,
          filename TEXT NOT NULL, file_hash TEXT NOT NULL, status TEXT NOT NULL,
          total_rows INTEGER DEFAULT 0, valid_rows INTEGER DEFAULT 0, error_rows INTEGER DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, committed_at TEXT
        );

CREATE TABLE import_row(
          id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT NOT NULL, sheet_name TEXT NOT NULL,
          row_no INTEGER NOT NULL, payload_json TEXT NOT NULL, is_valid INTEGER NOT NULL,
          errors_json TEXT NOT NULL, FOREIGN KEY(batch_id) REFERENCES import_batch(batch_id)
        );

CREATE TABLE lock_event(id INTEGER PRIMARY KEY AUTOINCREMENT,doc_type TEXT NOT NULL,doc_id TEXT NOT NULL,action TEXT NOT NULL CHECK(action IN ('LOCK','UNLOCK')),reason TEXT NOT NULL,username TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE result_snapshot(
          metric_key TEXT PRIMARY KEY, metric_value REAL NOT NULL, unit TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE role_permission(role TEXT NOT NULL,permission TEXT NOT NULL,PRIMARY KEY(role,permission));

CREATE TABLE source_row(
          id INTEGER PRIMARY KEY AUTOINCREMENT, template_key TEXT NOT NULL, batch_id TEXT NOT NULL,
          sheet_name TEXT NOT NULL, row_no INTEGER NOT NULL, payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(batch_id, sheet_name, row_no)
        );

CREATE TABLE user_screen_permission(
          username TEXT NOT NULL,
          screen_code TEXT NOT NULL,
          access_level TEXT NOT NULL CHECK(access_level IN ('NONE','VIEW','EDIT')),
          updated_at TEXT NOT NULL,
          updated_by TEXT,
          PRIMARY KEY(username,screen_code),
          FOREIGN KEY(username) REFERENCES app_user(username)
        );