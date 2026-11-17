import streamlit as st, hashlib, hmac, secrets, datetime, random, os, base64
import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import requests

try:
    MONGO_URI = st.secrets["mongodb"]["uri"]
    DB_NAME = st.secrets["mongodb"].get("db_name", "permaculture")
    client = MongoClient(MONGO_URI)
    mongo_db = client[DB_NAME]
    USE_MONGO = True
except:
    mongo_db = None
    USE_MONGO = False

def init_db():
    if USE_MONGO:
        mongo_db.companies.create_index("username", unique=True)
        try: mongo_db.failed_logins.create_index("username")
        except: pass
        try: mongo_db.failed_logins.create_index("created_at", expireAfterSeconds=900)
        except: pass

def hash_password(pw):
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200000)
    return f"pbkdf2_sha256$200000${salt}${dk.hex()}"
def verify_password(pw, stored):
    try:
        _, iters, salt, h = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), h), False
    except: return False, False

# --- Rate Limit ---
def _record_failed_login(username):
    if USE_MONGO: mongo_db.failed_logins.insert_one({"username": username.strip().lower(), "created_at": datetime.datetime.now().isoformat()})
def _clear_failed_logins(username):
    if USE_MONGO: mongo_db.failed_logins.delete_many({"username": username.strip().lower()})
def _is_login_locked(username):
    if not USE_MONGO: return False, 0
    ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
    c = mongo_db.failed_logins.count_documents({"username": username.strip().lower(), "created_at": {"$gte": ago}})
    if c >= 5: return True, 15
    return False, 0
def _get_failed_count(username):
    if not USE_MONGO: return 0
    ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).isoformat()
    return mongo_db.failed_logins.count_documents({"username": username.strip().lower(), "created_at": {"$gte": ago}})

def _get_admin_credentials():
    try:
        a = st.secrets.get("auth", {})
        return a.get("admin_username","admin"), a.get("admin_password",""), a.get("admin_password_hash","")
    except: return "admin","",""

def authenticate(username, password):
    locked,_ = _is_login_locked(username)
    if locked: return None, "locked"
    admin_user, admin_pw, admin_hash = _get_admin_credentials()
    if username.strip().lower() == admin_user.lower():
        valid = False
        if admin_hash: valid,_ = verify_password(password, admin_hash)
        elif admin_pw: valid = hmac.compare_digest(password, admin_pw)
        else: return None, None
        if valid:
            _clear_failed_logins(username)
            return {"username": admin_user, "name": "Administrator", "role": "admin", "id": "admin"}, "admin"
        _record_failed_login(username); return None, None
    if USE_MONGO:
        doc = mongo_db.companies.find_one({"username": username.strip().lower(), "is_active": True})
        if doc:
            valid,_ = verify_password(password, doc.get("password_hash",""))
            if valid:
                _clear_failed_logins(username)
                doc["id"] = str(doc.pop("_id"))
                mongo_db.companies.update_one({"username": username.strip().lower()}, {"$set": {"last_login": datetime.datetime.now().isoformat()}, "$inc": {"login_count": 1}})
                log_action(doc["id"], doc["name"], "LOGIN", "auth", doc["id"], doc["name"], f"Login {username}")
                return doc, "company"
            _record_failed_login(username); return None, None
        _record_failed_login(username); return None, None
    return None, None

# --- Guards ---
def _get_session_company_id():
    try:
        if st.session_state.get("role")=="company": return str(st.session_state.get("company_id",""))
    except: pass
    return None
def _is_admin():
    try: return st.session_state.get("role")=="admin"
    except: return False
def _can_access_company(tid):
    if _is_admin(): return True
    s = _get_session_company_id()
    return s is not None and str(tid)==s

def log_action(company_id, company_name, action, template, target_id, target_name, details=""):
    if USE_MONGO:
        mongo_db.logs.insert_one({"company_id": str(company_id), "company_name": company_name, "action": action, "template": template, "target_id": str(target_id), "target_name": target_name, "details": details, "created_at": datetime.datetime.now().isoformat()})

def get_logs(company_id=None, limit=100):
    if _get_session_company_id() is not None: company_id = _get_session_company_id()
    if USE_MONGO:
        q={}
        if company_id: q["company_id"]=str(company_id)
        docs=list(mongo_db.logs.find(q).sort("_id",-1).limit(limit))
        return pd.DataFrame([{"Date": d.get("created_at",""), "Company": d.get("company_name",""), "Action": d.get("action",""), "Template": d.get("template",""), "Target": d.get("target_name",""), "Details": d.get("details","")} for d in docs])
    return pd.DataFrame()

def get_companies(include_inactive=False):
    if USE_MONGO:
        q={} if include_inactive else {"is_active": True}
        docs=list(mongo_db.companies.find(q).sort("name",1))
        for d in docs: d["id"]=str(d.pop("_id"))
        return docs
    return []
def get_company_by_id(cid):
    if not _can_access_company(cid) and _get_session_company_id() is not None: return None
    if USE_MONGO:
        try: doc=mongo_db.companies.find_one({"_id": ObjectId(cid)})
        except: doc=mongo_db.companies.find_one({"_id": cid})
        if doc: doc["id"]=str(doc.pop("_id")); return doc
    return None
def update_company(cid, data):
    if not _can_access_company(cid): raise PermissionError("Cannot edit another company")
    if USE_MONGO:
        upd={k:v for k,v in data.items() if k not in ["id","_id","logo_file"]}
        try: mongo_db.companies.update_one({"_id": ObjectId(cid)}, {"$set": upd})
        except: mongo_db.companies.update_one({"_id": cid}, {"$set": upd})
        return True
    return False
def admin_reset_password(cid, new_pw):
    if USE_MONGO:
        try: mongo_db.companies.update_one({"_id": ObjectId(cid)}, {"$set": {"password_hash": hash_password(new_pw)}})
        except: mongo_db.companies.update_one({"_id": cid}, {"$set": {"password_hash": hash_password(new_pw)}})
        return True
    return False

def create_company_by_admin(data):
    if USE_MONGO:
        if mongo_db.companies.find_one({"username": data["username"].strip().lower()}):
            return None, "Username exists", False
        doc={"name": data["name"], "username": data["username"].strip().lower(), "email": data.get("email",""), "city": data.get("city",""), "phone": data.get("phone",""), "password_hash": hash_password(data.get("password","admin-admin")), "template_choice": data.get("template_choice","both"), "is_active": True, "must_complete_profile": True, "login_count": 0, "created_at": datetime.datetime.now().isoformat(), "address": "", "ice": "", "rc": "", "bank_name": "", "bank_rib": "", "primary_color": "#2E7D32", "footer_text": "", "logo_base64": ""}
        r=mongo_db.companies.insert_one(doc)
        log_action(str(r.inserted_id), data["name"], "ADMIN_CREATE_COMPANY", "companies", str(r.inserted_id), data["name"], "Admin created")
        wa=False
        if data.get("send_whatsapp"):
            wa,_=send_company_welcome_whatsapp({**doc, "id": str(r.inserted_id)}, data.get("app_url",""))
        return str(r.inserted_id), "Created", wa
    return None, "Mongo required", False

# --- WhatsApp ---
def send_whatsapp_message(phone, msg):
    clean=phone.replace(" ","").replace("-","").replace("+","")
    if clean.startswith("06") or clean.startswith("07") or clean.startswith("05"): clean="212"+clean[1:]
    try:
        pid=st.secrets["whatsapp"]["phone_number_id"]; tok=st.secrets["whatsapp"]["access_token"]; ver=st.secrets["whatsapp"].get("api_version","v21.0")
        r=requests.post(f"https://graph.facebook.com/{ver}/{pid}/messages", json={"messaging_product":"whatsapp","to":clean,"type":"text","text":{"body":msg}}, headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}, timeout=15)
        return r.status_code in [200,201], r.text[:300]
    except Exception as e: return False, str(e)
def send_whatsapp_template(phone, template_name, params):
    clean=phone.replace(" ","").replace("-","").replace("+","")
    if clean.startswith("06") or clean.startswith("07") or clean.startswith("05"): clean="212"+clean[1:]
    try:
        pid=st.secrets["whatsapp"]["phone_number_id"]; tok=st.secrets["whatsapp"]["access_token"]; ver=st.secrets["whatsapp"].get("api_version","v21.0")
        payload={"messaging_product":"whatsapp","to":clean,"type":"template","template":{"name":template_name,"language":{"code":"en_US"},"components":[{"type":"body","parameters":[{"type":"text","text":str(p)} for p in params]}]}}
        r=requests.post(f"https://graph.facebook.com/{ver}/{pid}/messages", json=payload, headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}, timeout=15)
        return r.status_code in [200,201], r.text[:300]
    except Exception as e: return False, str(e)
def send_company_welcome_whatsapp(company, app_url=""):
    phone=company.get("phone","")
    if not phone: return False, "No phone"
    try: use_templates=st.secrets.get("whatsapp",{}).get("use_templates",False)
    except: use_templates=False
    if use_templates: return send_whatsapp_template(phone, "welcome_company", [company["name"], company.get("username"), "admin-admin", app_url])
    return send_whatsapp_message(phone, f"🌿 Welcome {company['name']} - Username: {company.get('username')} - Password: admin-admin - Login: {app_url}")

# --- OTP - NO LEAK ---
def create_whatsapp_otp(username):
    if not USE_MONGO: return False, "Mongo required", ""
    comp=mongo_db.companies.find_one({"username": username.strip().lower()})
    if not comp: return False, "If this username exists, OTP sent to its WhatsApp", ""
    phone=comp.get("phone","")
    if not phone: return False, "No phone - Contact Admin", ""
    ten=(datetime.datetime.now()-datetime.timedelta(minutes=10)).isoformat()
    if mongo_db.otp_codes.count_documents({"username": username.strip().lower(), "created_at": {"$gte": ten}})>=3:
        return False, "Too many OTP - Wait 10 min", ""
    otp=f"{random.randint(100000,999999)}"
    mongo_db.otp_codes.insert_one({"company_id": str(comp["_id"]), "username": username.strip().lower(), "phone": phone, "otp_hash": hashlib.sha256(otp.encode()).hexdigest(), "expires_at": (datetime.datetime.now()+datetime.timedelta(minutes=5)).isoformat(), "used": False, "attempts": 0, "created_at": datetime.datetime.now().isoformat()})
    try:
        if st.secrets.get("whatsapp",{}).get("use_templates",False): success, debug=send_whatsapp_template(phone, "otp_reset", [otp])
        else: success, debug=send_whatsapp_message(phone, f"🌿 Permaculture App\n\nYour reset code is: *{otp}*\nValid 5 min.")
    except Exception as e: success, debug=False, str(e)
    log_action(str(comp["_id"]), comp["name"], "WHATSAPP_OTP_SENT", "auth", str(comp["_id"]), comp["name"], f"OTP sent Success={success}")
    masked=f"{phone[:2]}******{phone[-2:]}" if len(phone)>=6 else "****"
    if success: return True, f"OTP sent to {masked}", masked
    return False, f"WhatsApp failed ({debug}) - Contact Admin", masked
def verify_whatsapp_otp(username, otp_input):
    if not USE_MONGO: return False
    rec=mongo_db.otp_codes.find_one({"username": username.strip().lower(), "used": False}, sort=[("created_at",-1)])
    if not rec: return False
    if datetime.datetime.now().isoformat() > rec["expires_at"]: return False
    if rec.get("attempts",0)>=3: return False
    ok=hmac.compare_digest(hashlib.sha256(otp_input.strip().encode()).hexdigest(), rec["otp_hash"])
    if ok:
        mongo_db.otp_codes.update_one({"_id": rec["_id"]}, {"$set": {"used": True}})
        return True
    mongo_db.otp_codes.update_one({"_id": rec["_id"]}, {"$inc": {"attempts": 1}})
    return False

# --- PDF Base64 ---
def _pdf_to_base64(src):
    if not src: return ""
    if isinstance(src, (bytes, bytearray)): return base64.b64encode(bytes(src)).decode("utf-8")
    if hasattr(src, "getvalue"): return base64.b64encode(src.getvalue()).decode("utf-8")
    if isinstance(src, str) and os.path.exists(src):
        with open(src, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")
    return ""
def save_plan(data):
    pdf_b64=_pdf_to_base64(data.get("pdf_bytes") or data.get("pdf_path",""))
    doc={"company_id": str(data["company_id"]), "company_name": data["company_name"], "type":"plan", "name": data.get("name"), "project": data.get("project"), "location": data.get("location"), "surface": data.get("surface"), "total_trees": data.get("total_trees"), "ca_year3": data.get("ca_year3"), "form": data.get("form",{}), "pdf_path": "", "pdf_base64": pdf_b64, "pdf_name": data.get("pdf_name") or "Plan.pdf", "pdf_size_kb": len(pdf_b64)//1024 if pdf_b64 else 0, "created_at": datetime.datetime.now().isoformat()}
    if USE_MONGO:
        if len(pdf_b64)>10000000: doc["pdf_base64"]=""; doc["pdf_too_large"]=True
        r=mongo_db.submissions_plan.insert_one(doc)
        log_action(data["company_id"], data["company_name"], "SUBMIT_PLAN", "plan", str(r.inserted_id), data.get("project",""), f"Plan {doc['pdf_size_kb']}KB")
        return str(r.inserted_id)
    return None
def save_banque(data):
    pdf_b64=_pdf_to_base64(data.get("pdf_bytes") or data.get("pdf_path",""))
    doc={"company_id": str(data["company_id"]), "company_name": data["company_name"], "type":"banque", "nom_complet": data.get("nom_complet"), "nom_projet": data.get("nom_projet"), "montant_demande": data.get("montant_demande"), "duree_mois": data.get("duree_mois"), "form": data.get("form",{}), "pdf_path": "", "pdf_base64": pdf_b64, "pdf_name": data.get("pdf_name") or "Banque.pdf", "pdf_size_kb": len(pdf_b64)//1024 if pdf_b64 else 0, "created_at": datetime.datetime.now().isoformat()}
    if USE_MONGO:
        if len(pdf_b64)>10000000: doc["pdf_base64"]=""; doc["pdf_too_large"]=True
        r=mongo_db.submissions_banque.insert_one(doc)
        log_action(data["company_id"], data["company_name"], "SUBMIT_BANQUE", "banque", str(r.inserted_id), data.get("nom_projet",""), f"Banque {doc['pdf_size_kb']}KB")
        return str(r.inserted_id)
    return None
def get_pdf_bytes(collection_name, sid):
    if not USE_MONGO: return None, None
    coll=mongo_db[collection_name]
    try: doc=coll.find_one({"_id": ObjectId(sid)})
    except: doc=coll.find_one({"_id": sid})
    if not doc: return None, None
    b64=doc.get("pdf_base64","")
    if b64: return base64.b64decode(b64), doc.get("pdf_name","document.pdf")
    return None, None
def get_submissions(limit=100, company_id=None):
    if _get_session_company_id() is not None: company_id=_get_session_company_id()
    if USE_MONGO:
        q={}
        if company_id: q["company_id"]=str(company_id)
        docs=list(mongo_db.submissions_plan.find(q).sort("_id",-1).limit(limit))
        return pd.DataFrame([{"Date": d.get("created_at",""), "Company": d.get("company_name",""), "Project": d.get("project"), "Location": d.get("location"), "Surface": d.get("surface")} for d in docs])
    return pd.DataFrame()
def get_submissions_banque(limit=100, company_id=None):
    if _get_session_company_id() is not None: company_id=_get_session_company_id()
    if USE_MONGO:
        q={}
        if company_id: q["company_id"]=str(company_id)
        docs=list(mongo_db.submissions_banque.find(q).sort("_id",-1).limit(limit))
        return pd.DataFrame([{"Date": d.get("created_at",""), "Company": d.get("company_name",""), "Projet": d.get("nom_projet"), "Montant": d.get("montant_demande")} for d in docs])
    return pd.DataFrame()
def get_logo_for_display(company):
    return company.get("logo_base64","")

def delete_company(cid):
    """Remove a company account (admin only); its submissions are kept for audit."""
    if not _is_admin(): raise PermissionError("Admin only")
    if USE_MONGO:
        try: q={"_id": ObjectId(cid)}
        except: q={"_id": cid}
        doc=mongo_db.companies.find_one(q)
        if not doc: return False
        mongo_db.companies.delete_one(q)
        log_action("admin", "Administrator", "ADMIN_DELETE_COMPANY", "companies", cid, doc.get("name",""), "Admin deleted company")
        return True
    return False
