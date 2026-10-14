
from app.db import init_db, connect
from app.security import hash_password
import os

USERS = [
    ("admin","Quản trị cao nhất","SUPER_ADMIN"),
    ("ketoan01","Kế toán 01","KE_TOAN"),
    ("thuquy01","Thủ quỹ 01","THU_QUY"),
    ("thukho01","Thủ kho 01","THU_KHO"),
    ("quanly01","Quản lý 01","QUAN_LY"),
    ("viewer01","User chỉ xem","VIEWER"),
]

def main():
    init_db()
    default_pwd = os.environ.get("VG_PILOT_DEFAULT_PASSWORD",'')
    with connect() as con:
        for username, full_name, role in USERS:
            con.execute("""
                INSERT OR IGNORE INTO app_user(username,full_name,password_hash,role,is_active,must_change_password)
                VALUES(?,?,?,?,1,1)
            """,(username,full_name,hash_password(default_pwd),role))
    print("Seeded pilot users:")
    for u in USERS:
        print(" -",u[0],u[2])
    print("Default pilot password:", default_pwd)
    print("IMPORTANT: force password change before production.")
if __name__=="__main__":
    main()
