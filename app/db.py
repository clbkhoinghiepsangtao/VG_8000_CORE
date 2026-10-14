import sqlite3, json, os
from pathlib import Path
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "vinh_giang.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS import_batch(
          batch_id TEXT PRIMARY KEY, template_key TEXT NOT NULL, template_version TEXT,
          filename TEXT NOT NULL, file_hash TEXT NOT NULL, status TEXT NOT NULL,
          total_rows INTEGER DEFAULT 0, valid_rows INTEGER DEFAULT 0, error_rows INTEGER DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, committed_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_import_batch_hash ON import_batch(file_hash, template_key);
        CREATE TABLE IF NOT EXISTS import_row(
          id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT NOT NULL, sheet_name TEXT NOT NULL,
          row_no INTEGER NOT NULL, payload_json TEXT NOT NULL, is_valid INTEGER NOT NULL,
          errors_json TEXT NOT NULL, FOREIGN KEY(batch_id) REFERENCES import_batch(batch_id)
        );
        CREATE TABLE IF NOT EXISTS source_row(
          id INTEGER PRIMARY KEY AUTOINCREMENT, template_key TEXT NOT NULL, batch_id TEXT NOT NULL,
          sheet_name TEXT NOT NULL, row_no INTEGER NOT NULL, payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(batch_id, sheet_name, row_no)
        );
        CREATE TABLE IF NOT EXISTS dm_product(
          ma_sku TEXT PRIMARY KEY, ten_sku TEXT, su_thung REAL NOT NULL, trong_luong_su REAL NOT NULL,
          vat_rate REAL NOT NULL DEFAULT 0.08, bu TEXT, nhan TEXT, trang_thai TEXT DEFAULT 'ACTIVE'
        );
        CREATE TABLE IF NOT EXISTS dm_personnel_code(
          ma_nghiep_vu TEXT PRIMARY KEY, ma_nv TEXT NOT NULL, loai_ma TEXT, trang_thai TEXT DEFAULT 'ACTIVE'
        );
        CREATE TABLE IF NOT EXISTS dm_customer_map(
          ma_kh_nguon TEXT PRIMARY KEY, ma_kh_chuan TEXT NOT NULL, source_system TEXT
        );

        CREATE TABLE IF NOT EXISTS app_user(username TEXT PRIMARY KEY,full_name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL,is_active INTEGER NOT NULL DEFAULT 1,must_change_password INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS role_permission(role TEXT NOT NULL,permission TEXT NOT NULL,PRIMARY KEY(role,permission));
        CREATE TABLE IF NOT EXISTS auth_session(token TEXT PRIMARY KEY,username TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,expires_at TEXT NOT NULL,FOREIGN KEY(username) REFERENCES app_user(username));
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL,action TEXT NOT NULL,entity_type TEXT,entity_id TEXT,reason TEXT,old_json TEXT,new_json TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS adjustment_doc(adjustment_id TEXT PRIMARY KEY,original_doc_type TEXT NOT NULL,original_doc_id TEXT NOT NULL,direction TEXT NOT NULL CHECK(direction IN ('INCREASE','DECREASE')),amount REAL DEFAULT 0,quantity REAL DEFAULT 0,reason TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'DRAFT',created_by TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,posted_at TEXT);
        CREATE TABLE IF NOT EXISTS lock_event(id INTEGER PRIMARY KEY AUTOINCREMENT,doc_type TEXT NOT NULL,doc_id TEXT NOT NULL,action TEXT NOT NULL CHECK(action IN ('LOCK','UNLOCK')),reason TEXT NOT NULL,username TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS result_snapshot(
          metric_key TEXT PRIMARY KEY, metric_value REAL NOT NULL, unit TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        con.executemany("INSERT OR IGNORE INTO dm_product(ma_sku,ten_sku,su_thung,trong_luong_su,vat_rate,bu,nhan) VALUES(?,?,?,?,?,?,?)", [
          ('SKU001','Sản phẩm demo 1',6,3.0,0.08,'HC','101'),
          ('SKU002','Sản phẩm demo 2',12,1.0,0.08,'PC','103'),
          ('SKU003','Sản phẩm demo 3',24,0.5,0.08,'BE','111'),
        ])
        con.executemany("INSERT OR IGNORE INTO dm_personnel_code(ma_nghiep_vu,ma_nv,loai_ma) VALUES(?,?,?)", [
          ('4185','VG206','MAY_BAN_HANG'),('4256','VG206','MAY_BAN_HANG'),('AD001','VG001','ADMIN'),
          ('GH018','VG318','GIAO_HANG'),('LX018','VG418','LAI_XE')
        ])
        con.executemany("INSERT OR IGNORE INTO dm_customer_map(ma_kh_nguon,ma_kh_chuan,source_system) VALUES(?,?,?)", [
          ('TEST-SOURCE-KH-001','TEST-KH-001','DMS'),('TEST-SOURCE-KH-002','TEST-KH-001','MBW'),('TEST-SOURCE-KH-003','TEST-KH-002','MISA')
        ])
        from .security import hash_password
        default_pwd=os.environ.get("VG_INITIAL_ADMIN_PASSWORD",'')
        con.execute("INSERT OR IGNORE INTO app_user(username,full_name,password_hash,role,must_change_password) VALUES(?,?,?,?,1)",("admin","Quản trị cao nhất",hash_password(default_pwd),"SUPER_ADMIN"))
        perms={"KE_TOAN":["UPLOAD_SOURCE","VIEW_REPORT","MANAGE_PRICE","CREATE_ADJUSTMENT","EXPORT_EXCEL"],"THU_QUY":["VIEW_GH","COLLECT_CASH","VIEW_DEBT"],"THU_KHO":["VIEW_GH","CONFIRM_RETURN","MANAGE_LOADING"],"QUAN_LY":["VIEW_REPORT","VIEW_DASHBOARD","EXPORT_EXCEL"],"VIEWER":["VIEW_REPORT","VIEW_DASHBOARD"]}
        for role,ps in perms.items(): con.executemany("INSERT OR IGNORE INTO role_permission(role,permission) VALUES(?,?)",[(role,p) for p in ps])

