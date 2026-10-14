import hmac, hashlib, secrets
from .db import connect
ITERATIONS=210000

def hash_password(password:str,salt:bytes|None=None)->str:
    salt=salt or secrets.token_bytes(16)
    dk=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"

def verify_password(password:str,encoded:str)->bool:
    try:
        _,it,salt_hex,hash_hex=encoded.split("$")
        dk=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),int(it))
        return hmac.compare_digest(dk.hex(),hash_hex)
    except Exception:return False

def create_session(username:str)->str:
    token=secrets.token_urlsafe(32)
    with connect() as con:
        con.execute("INSERT INTO auth_session(token,username,created_at,expires_at) VALUES(?,?,CURRENT_TIMESTAMP,datetime('now','+12 hours'))",(token,username))
    return token

def get_user_by_token(token:str):
    with connect() as con:
        row=con.execute("""SELECT u.username,u.full_name,u.role,u.is_active,u.must_change_password FROM auth_session s JOIN app_user u ON u.username=s.username WHERE s.token=? AND s.expires_at>CURRENT_TIMESTAMP AND u.is_active=1""",(token,)).fetchone()
        return dict(row) if row else None

def has_permission(role:str,permission:str)->bool:
    if role in ('SUPER_ADMIN','ADMIN'): return True
    # Kế toán trưởng kế thừa quyền thao tác của kế toán; quyền duyệt riêng vẫn
    # được kiểm tra trực tiếp theo vai trò tại từng nghiệp vụ phê duyệt.
    roles=(role,'KE_TOAN') if role=='KE_TOAN_TRUONG' else (role,)
    with connect() as con:
        return con.execute(
            "SELECT 1 FROM role_permission WHERE role IN ("+",".join("?" for _ in roles)+") AND permission=? LIMIT 1",
            (*roles,permission)
        ).fetchone() is not None

def audit(username,action,entity_type=None,entity_id=None,reason=None,old_json=None,new_json=None):
    with connect() as con:con.execute("INSERT INTO audit_log(username,action,entity_type,entity_id,reason,old_json,new_json) VALUES(?,?,?,?,?,?,?)",(username,action,entity_type,entity_id,reason,old_json,new_json))
