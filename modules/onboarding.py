import streamlit as st
from database.db import update_company, mongo_db, USE_MONGO, hash_password
from bson import ObjectId
def render_onboarding(tr, company):
    st.markdown(f"# 👋 Welcome {company['name']} - Complete Your Profile")
    st.info("First login - Complete profile + change password")
    with st.form("onboarding"):
        address = st.text_input("Address", value=company.get("address",""))
        phone = st.text_input("Phone", value=company.get("phone",""))
        email = st.text_input("Email", value=company.get("email",""))
        ice = st.text_input("ICE", value=company.get("ice",""))
        bank = st.text_input("Bank", value=company.get("bank_name",""))
        rib = st.text_input("RIB", value=company.get("bank_rib",""))
        new_pw = st.text_input("New Password", type="password", value="")
        btn = st.form_submit_button("✅ Complete Profile", type="primary", use_container_width=True)
        if btn:
            upd = {"address": address, "phone": phone, "email": email, "ice": ice, "bank_name": bank, "bank_rib": rib, "must_complete_profile": False}
            if new_pw: upd["password_hash"] = hash_password(new_pw)
            try: mongo_db.companies.update_one({"_id": ObjectId(company["id"])}, {"$set": upd})
            except: mongo_db.companies.update_one({"_id": company["id"]}, {"$set": upd})
            st.session_state["must_complete_profile"] = False
            st.success("Profile completed!"); st.rerun()
