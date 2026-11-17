import streamlit as st
from database.db import authenticate, _is_login_locked, _get_failed_count, create_whatsapp_otp, verify_whatsapp_otp, admin_reset_password, mongo_db, USE_MONGO

def render_login(tr):
    st.markdown("# 🌿 Permaculture App")
    tab_login, tab_forgot = st.tabs(["🔐 Login", "🔑 Forgot Password"])
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            btn = st.form_submit_button("Login", use_container_width=True, type="primary")
        if btn:
            if not username or not password: st.error("Enter username + password")
            else:
                locked, mins = _is_login_locked(username)
                if locked: st.error(f"🔒 Locked - Try again in {mins} min")
                else:
                    user, role = authenticate(username, password)
                    if role == "locked": st.error("🔒 Locked")
                    elif user:
                        st.session_state["authenticated"]=True; st.session_state["user"]=user; st.session_state["role"]=role
                        st.session_state["company_id"]=user.get("id") if role=="company" else None
                        st.session_state["must_complete_profile"]=user.get("must_complete_profile", False) if role=="company" else False
                        st.success(f"Welcome {user['name']}!"); st.rerun()
                    else:
                        fails=_get_failed_count(username); st.error(f"❌ Wrong username/password - {max(0,5-fails)} tries left")
    with tab_forgot:
        st.markdown("### Reset via WhatsApp OTP")
        u = st.text_input("Username for reset", key="forgot_user")
        if st.button("📱 Send OTP via WhatsApp"):
            ok, msg, masked = create_whatsapp_otp(u)
            if ok: st.success(msg)
            else: st.error(msg)
        otp = st.text_input("Enter OTP code", key="forgot_otp")
        new_pw = st.text_input("New password", type="password", key="forgot_newpw")
        if st.button("✅ Verify OTP + Reset Password"):
            if verify_whatsapp_otp(u, otp):
                if USE_MONGO:
                    comp = mongo_db.companies.find_one({"username": u.strip().lower()})
                    if comp:
                        admin_reset_password(str(comp["_id"]), new_pw)
                        st.success("Password reset - Login now")
            else: st.error("Invalid / expired OTP")

def render_logout():
    if st.button("🚪 Logout", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()