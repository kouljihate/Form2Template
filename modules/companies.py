import streamlit as st
from database.db import update_company, get_logo_for_display
def render_companies(tr, current_company, allow_create=False):
    st.subheader(f"🏢 {tr['company_title']} - {current_company['name']} (Yours Only)")
    if current_company.get("logo_base64"): st.image(current_company["logo_base64"], width=150)
    with st.form("form_company_edit_own"):
        e_address = st.text_input(tr["company_address"], value=current_company.get("address",""))
        e_phone = st.text_input(tr["company_phone"], value=current_company.get("phone",""))
        e_email = st.text_input(tr["company_email"], value=current_company.get("email",""))
        e_ice = st.text_input(tr["company_ice"], value=current_company.get("ice",""))
        e_bank = st.text_input(tr["company_bank"], value=current_company.get("bank_name",""))
        e_rib = st.text_input(tr["company_rib"], value=current_company.get("bank_rib",""))
        e_color = st.color_picker(tr["company_color"], current_company.get("primary_color","#2E7D32"))
        e_footer = st.text_input(tr["company_footer"], value=current_company.get("footer_text",""))
        e_logo = st.file_uploader(tr["company_logo_new"], type=["png","jpg","jpeg"])
        upd = st.form_submit_button(tr["company_save"], use_container_width=True, type="primary")
        if upd:
            new_data = {**current_company, "address": e_address, "phone": e_phone, "email": e_email, "ice": e_ice, "bank_name": e_bank, "bank_rib": e_rib, "primary_color": e_color, "footer_text": e_footer}
            if e_logo:
                import base64
                new_data["logo_base64"] = "data:image/png;base64," + base64.b64encode(e_logo.read()).decode()
            update_company(current_company["id"], new_data)
            st.success(tr["company_saved"]); st.rerun()
    st.caption("To change Name, Username, Template - Contact Admin")
def render_change_password(tr, current_company):
    st.markdown("### 🔑 Change Password")
    with st.form("change_pw"):
        old = st.text_input("Old password", type="password")
        new = st.text_input("New password", type="password")
        btn = st.form_submit_button("Change Password")
        if btn:
            from database.db import verify_password, admin_reset_password
            ok,_ = verify_password(old, current_company.get("password_hash",""))
            if ok:
                admin_reset_password(current_company["id"], new); st.success("Password changed")
            else: st.error("Old password wrong")
