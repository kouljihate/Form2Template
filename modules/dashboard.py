import streamlit as st, pandas as pd
from database.db import mongo_db, get_companies, get_logs, USE_MONGO
def render_admin_dashboard(tr):
    st.subheader("📊 Dashboard - All Companies")
    companies = get_companies(include_inactive=True)
    total = len(companies); active = len([c for c in companies if c.get("is_active")]); pending = len([c for c in companies if c.get("must_complete_profile")])
    total_plan = mongo_db.submissions_plan.count_documents({}) if USE_MONGO else 0
    total_banque = mongo_db.submissions_banque.count_documents({}) if USE_MONGO else 0
    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("🏢 Total Companies", total, f"{active} active")
    with col2: st.metric("⏳ Pending", pending)
    with col3: st.metric("📄 Total PDFs", total_plan+total_banque, f"Plan {total_plan} | Banque {total_banque}")
    with col4: st.metric("🔐 Total Logins", sum([c.get("login_count",0) for c in companies]))
    st.divider()
    st.markdown("#### 📋 Companies Overview")
    rows=[]
    for c in companies:
        plan_n = mongo_db.submissions_plan.count_documents({"company_id": c["id"]}) if USE_MONGO else 0
        banque_n = mongo_db.submissions_banque.count_documents({"company_id": c["id"]}) if USE_MONGO else 0
        rows.append({"Company": c.get("name",""), "Username": c.get("username",""), "City": c.get("city",""), "Template": c.get("template_choice","both"), "Status": "🚫 Inactive" if not c.get("is_active") else ("⏳ Pending" if c.get("must_complete_profile") else "✅ Active"), "Plan PDFs": plan_n, "Banque PDFs": banque_n, "Logins": c.get("login_count",0), "Last Login": str(c.get("last_login","Never"))[:16]})
    df = pd.DataFrame(rows); st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("📥 Export CSV", df.to_csv(index=False).encode("utf-8"), "companies.csv", "text/csv")
    st.divider()
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("#### 🕒 Recent Activity"); st.dataframe(get_logs(None, 20), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### 📄 Recent PDFs")
        recent=[]
        for p in list(mongo_db.submissions_plan.find().sort("_id",-1).limit(5)) if USE_MONGO else []: recent.append({"Type":"📋 Plan","Company":p.get("company_name",""),"Project":p.get("project",""),"Date":str(p.get("created_at",""))[:16]})
        for b in list(mongo_db.submissions_banque.find().sort("_id",-1).limit(5)) if USE_MONGO else []: recent.append({"Type":"🏦 Banque","Company":b.get("company_name",""),"Project":b.get("nom_projet",""),"Date":str(b.get("created_at",""))[:16]})
        st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)