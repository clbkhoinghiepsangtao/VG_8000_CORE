from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
import datetime, secrets, string, json
from .db import connect
from .security import get_user_by_token, hash_password, audit, has_permission

router=APIRouter()

SCREENS=[
 "QTGH_UI02","QTGH_UI04","QTGH_UI05","QTGH_UI06",
 "QTGH_UI07","QTGH_UI08","QTGH_UI09","QTGH_UI10","QTGH_UI11"
]
LEVELS={"NONE","VIEW","EDIT"}
ADMIN_ROLES={"SUPER_ADMIN","ADMIN"}

DEFAULTS={
 "SUPER_ADMIN":{s:"EDIT" for s in SCREENS},
 "ADMIN":{s:"EDIT" for s in SCREENS},
 "KE_TOAN_TRUONG":{
  "QTGH_UI02":"EDIT","QTGH_UI04":"EDIT","QTGH_UI05":"VIEW","QTGH_UI06":"NONE",
  "QTGH_UI07":"EDIT","QTGH_UI08":"EDIT","QTGH_UI09":"EDIT","QTGH_UI10":"EDIT","QTGH_UI11":"VIEW"
 },
 "KE_TOAN":{
  "QTGH_UI02":"EDIT","QTGH_UI04":"EDIT","QTGH_UI05":"VIEW","QTGH_UI06":"NONE",
  "QTGH_UI07":"EDIT","QTGH_UI08":"EDIT","QTGH_UI09":"EDIT","QTGH_UI10":"EDIT","QTGH_UI11":"VIEW"
 },
 "THU_KHO":{
  "QTGH_UI02":"NONE","QTGH_UI04":"NONE","QTGH_UI05":"NONE","QTGH_UI06":"EDIT",
  "QTGH_UI07":"NONE","QTGH_UI08":"NONE","QTGH_UI09":"NONE","QTGH_UI10":"NONE","QTGH_UI11":"NONE"
 },
 "THU_QUY":{
  "QTGH_UI02":"NONE","QTGH_UI04":"NONE","QTGH_UI05":"EDIT","QTGH_UI06":"NONE",
  "QTGH_UI07":"NONE","QTGH_UI08":"VIEW","QTGH_UI09":"NONE","QTGH_UI10":"NONE","QTGH_UI11":"EDIT"
 },
 "QUAN_LY":{s:"VIEW" for s in SCREENS},
 "VIEWER":{s:"VIEW" for s in SCREENS},
 "HCNS":{s:"NONE" for s in SCREENS},
}

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def ensure_schema():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS user_screen_permission(
          username TEXT NOT NULL,
          screen_code TEXT NOT NULL,
          access_level TEXT NOT NULL CHECK(access_level IN ('NONE','VIEW','EDIT')),
          updated_at TEXT NOT NULL,
          updated_by TEXT,
          PRIMARY KEY(username,screen_code),
          FOREIGN KEY(username) REFERENCES app_user(username)
        )""")
ensure_schema()

def auth_user(authorization):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Chưa đăng nhập")
    u=get_user_by_token(authorization.split(" ",1)[1].strip())
    if not u:
        raise HTTPException(401,"Phiên đăng nhập hết hạn/không hợp lệ")
    return u

def is_admin(u):
    return str(u.get("role") or "").upper() in ADMIN_ROLES

def defaults(role):
    role=str(role or "").upper()
    return dict(DEFAULTS.get(role,{s:"NONE" for s in SCREENS}))

def effective(username,role):
    out=defaults(role)
    if str(role or "").upper()=="SUPER_ADMIN":
        return out
    with connect() as c:
        for r in c.execute(
            "SELECT screen_code,access_level FROM user_screen_permission WHERE username=?",
            (username,)
        ):
            if r["screen_code"] in out:
                out[r["screen_code"]]=r["access_level"]
    return out

def profile(u):
    return {
      "username":u["username"],"full_name":u.get("full_name",""),"role":u["role"],
      "must_change_password":bool(u.get("must_change_password")),
      "is_admin":is_admin(u),
      "screen_permissions":effective(u["username"],u["role"])
    }

def allowed(u,screen,method):
    level=effective(u["username"],u["role"]).get(screen,"NONE")
    return level in ("VIEW","EDIT") if method.upper() in ("GET","HEAD") else level=="EDIT"

def required(path,method):
    p=path.lower()
    # Legacy QTGH routes remain callable even when their old screens are hidden.
    if p.startswith('/api/qtgh-v'):
        import re
        match=re.search(r'/ui(0[2-9]|1[01])(?:/|$)',p)
        if match: return ['QTGH_UI'+match.group(1)]
        if p.startswith('/api/qtgh-v11'): return ['QTGH_UI02']
        if any(x in p for x in ('/draft','/finalize','/banks')): return ['QTGH_UI04']
    if p.startswith('/api/gh-v1/'):
        if '/cashier' in p:return ['QTGH_UI05']
        if '/customer-debt' in p:return ['QTGH_UI08']
        if '/delivery-debt' in p:return ['QTGH_UI09']
        if '/settlement' in p:return ['QTGH_UI04']
        return ['QTGH_UI02']
    if p.startswith("/api/qtgh-v11"): return ["QTGH_UI02"]
    if p.startswith("/api/qtgh-stable/ui04/suggest-nvgh"): return ["QTGH_UI04","QTGH_UI08"]
    if p.startswith("/api/qtgh-stable/ui04"): return ["QTGH_UI04"]
    if p.startswith("/api/qtgh-stable/ui05"): return ["QTGH_UI05"]
    if p.startswith("/api/qtgh-stable/ui06"): return ["QTGH_UI06"]
    if p.startswith("/api/qtgh-stable/ui07/debts") and method.upper()=="GET": return ["QTGH_UI07","QTGH_UI08"]
    if p.startswith("/api/qtgh-stable/ui07"): return ["QTGH_UI07"]
    if p.startswith("/api/qtgh-stable/ui08"): return ["QTGH_UI08"]
    if p.startswith("/api/qtgh-stable/ui09"): return ["QTGH_UI09"]
    if p.startswith("/api/qtgh-stable/ui10"): return ["QTGH_UI10"]
    if p.startswith("/api/qtgh-stable/ui11"): return ["QTGH_UI11"]
    if p=="/api/qtgh-stable/context": return ["QTGH_UI04"]
    if p.startswith("/api/qtgh-stable/banks"): return ["QTGH_UI04","QTGH_UI05","QTGH_UI07","QTGH_UI09"]
    return []

def authorize_request(request):
    path=request.url.path
    method=request.method.upper()
    if not path.startswith('/api/') or path in ('/api/auth/login','/api/health'):
        return None
    authorization=request.headers.get('authorization')
    token=(authorization.split(' ',1)[1].strip() if authorization and authorization.lower().startswith('bearer ') else request.cookies.get('vg_session'))
    u=get_user_by_token(token) if token else None
    if not u:return JSONResponse(status_code=401,content={'detail':'Chưa đăng nhập hoặc phiên đã hết hạn'})
    if u.get('must_change_password') and path not in ('/api/auth/change-password','/api/auth/logout'):
        return JSONResponse(status_code=428,content={'detail':'Phải đổi mật khẩu trước khi sử dụng'})
    if path.startswith("/api/admin/accounts"):
        if not is_admin(u): return JSONResponse(status_code=403,content={"detail":"Chỉ Admin được quản lý tài khoản"})
        return None
    screens=required(path,method)
    if screens and not any(allowed(u,s,method) for s in screens):
        return JSONResponse(status_code=403,content={"detail":"Không có quyền thao tác màn hình này","required_screens":screens})
    if method not in ('GET','HEAD','OPTIONS') and not screens:
        p=path.lower()
        if p.startswith('/api/master-data/') or p.startswith('/api/demo/'):
            permitted=is_admin(u)
        elif p=='/api/adjustments':
            permitted=has_permission(u['role'],'CREATE_ADJUSTMENT')
        elif p.startswith('/api/qtgh-stable/bx-pack-v3/'):
            permitted=has_permission(u['role'],'MANAGE_LOADING')
        elif p.startswith(('/api/qtgh-stable/bx-v2/','/api/qtgh-stable/kq-nvkd/target-','/api/source-import/','/api/xb-','/api/uploads/')):
            permitted=has_permission(u['role'],'UPLOAD_SOURCE')
        elif p.startswith('/api/auth/'):
            permitted=True
        else:
            permitted=is_admin(u)
        if not permitted:return JSONResponse(status_code=403,content={'detail':'Không có quyền thao tác API này'})
    return None

@router.get("/api/access/profile")
def access_profile(authorization:str|None=Header(default=None)):
    return profile(auth_user(authorization))

def require_admin(authorization):
    u=auth_user(authorization)
    if u.get("must_change_password"): raise HTTPException(428,"Phải đổi mật khẩu trước khi sử dụng")
    if not is_admin(u): raise HTTPException(403,"Chỉ Admin được quản lý tài khoản")
    return u

def temp_password():
    chars=string.ascii_letters+string.digits+"@#%"
    while True:
        p="".join(secrets.choice(chars) for _ in range(14))
        if any(x.islower() for x in p) and any(x.isupper() for x in p) and any(x.isdigit() for x in p) and any(x in "@#%" for x in p):
            return p

def save_permissions(username,perm,admin):
    with connect() as c:
        for s in SCREENS:
            v=str((perm or {}).get(s,"NONE")).upper()
            if v not in LEVELS: raise HTTPException(400,f"Quyền {s} không hợp lệ")
            c.execute("""INSERT INTO user_screen_permission(username,screen_code,access_level,updated_at,updated_by)
              VALUES(?,?,?,?,?)
              ON CONFLICT(username,screen_code) DO UPDATE SET access_level=excluded.access_level,
              updated_at=excluded.updated_at,updated_by=excluded.updated_by""",
              (username,s,v,now(),admin))

@router.get("/api/admin/accounts")
def accounts(authorization:str|None=Header(default=None)):
    require_admin(authorization)
    with connect() as c:
        rows=[dict(r) for r in c.execute("SELECT username,full_name,role,is_active,must_change_password,created_at FROM app_user ORDER BY username")]
    for r in rows:r["screen_permissions"]=effective(r["username"],r["role"])
    return {"rows":rows}

@router.post("/api/admin/accounts")
def create_account(payload:dict,authorization:str|None=Header(default=None)):
    a=require_admin(authorization)
    username=str(payload.get("username") or "").strip()
    full_name=str(payload.get("full_name") or "").strip()
    role=str(payload.get("role") or "").strip().upper()
    if not username or not full_name or role not in DEFAULTS: raise HTTPException(400,"Thiếu/không hợp lệ username, họ tên hoặc vai trò")
    if not username.replace("_","").replace(".","").isalnum(): raise HTTPException(400,"Username chỉ gồm chữ, số, dấu _ hoặc .")
    pwd=temp_password()
    with connect() as c:
        if c.execute("SELECT 1 FROM app_user WHERE username=?",(username,)).fetchone(): raise HTTPException(409,"Username đã tồn tại")
        c.execute("INSERT INTO app_user(username,full_name,password_hash,role,is_active,must_change_password) VALUES(?,?,?,?,1,1)",
                  (username,full_name,hash_password(pwd),role))
    save_permissions(username,payload.get("screen_permissions") or defaults(role),a["username"])
    audit(a["username"],"CREATE_USER","APP_USER",username,new_json=json.dumps({"full_name":full_name,"role":role},ensure_ascii=False))
    return {"status":"ok","username":username,"temporary_password":pwd,"must_change_password":True}

@router.put("/api/admin/accounts/{username}/permissions")
def update_permissions(username:str,payload:dict,authorization:str|None=Header(default=None)):
    a=require_admin(authorization)
    with connect() as c:u=c.execute("SELECT role FROM app_user WHERE username=?",(username,)).fetchone()
    if not u:raise HTTPException(404,"Tài khoản không tồn tại")
    p=payload.get("screen_permissions") or {}
    if str(u["role"]).upper()=="SUPER_ADMIN":p=defaults("SUPER_ADMIN")
    save_permissions(username,p,a["username"])
    audit(a["username"],"UPDATE_USER_PERMISSION","APP_USER",username)
    return {"status":"ok","screen_permissions":effective(username,u["role"])}

@router.post("/api/admin/accounts/{username}/reset-password")
def reset_password(username:str,authorization:str|None=Header(default=None)):
    a=require_admin(authorization);pwd=temp_password()
    with connect() as c:
        if not c.execute("SELECT 1 FROM app_user WHERE username=?",(username,)).fetchone(): raise HTTPException(404,"Tài khoản không tồn tại")
        c.execute("UPDATE app_user SET password_hash=?,must_change_password=1 WHERE username=?",(hash_password(pwd),username))
        c.execute("DELETE FROM auth_session WHERE username=?",(username,))
    audit(a["username"],"RESET_PASSWORD","APP_USER",username)
    return {"status":"ok","temporary_password":pwd,"must_change_password":True}

@router.post("/api/admin/accounts/{username}/status")
def status(username:str,payload:dict,authorization:str|None=Header(default=None)):
    a=require_admin(authorization);active=1 if payload.get("is_active") else 0
    if username==a["username"] and not active: raise HTTPException(400,"Không thể tự khóa tài khoản đang dùng")
    with connect() as c:
        if not c.execute("SELECT 1 FROM app_user WHERE username=?",(username,)).fetchone(): raise HTTPException(404,"Tài khoản không tồn tại")
        c.execute("UPDATE app_user SET is_active=? WHERE username=?",(active,username))
        if not active:c.execute("DELETE FROM auth_session WHERE username=?",(username,))
    audit(a["username"],"SET_USER_STATUS","APP_USER",username,new_json=json.dumps({"is_active":active}))
    return {"status":"ok","is_active":bool(active)}
