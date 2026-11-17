from pathlib import Path

import streamlit as st

from database.db import get_company_by_id, get_logs, init_db
from i18n import AVAILABLE_UI_MODES, get_translations
from modules.admin import render_admin_companies
from modules.auth import render_login, render_logout
from modules.companies import render_change_password, render_companies
from modules.dashboard import render_admin_dashboard
from modules.dossier_banque import render_dossier_banque
from modules.onboarding import render_onboarding
from modules.plan_affaires import render_plan_affaires

st.set_page_config(page_title="Permaculture App", page_icon="🌿", layout="wide")
init_db()

if st.session_state.get("ui_mode") not in AVAILABLE_UI_MODES:
    st.session_state["ui_mode"] = AVAILABLE_UI_MODES[0]
with st.sidebar:
    st.session_state["ui_mode"] = st.selectbox(
        "🌐 Langue / Language",
        AVAILABLE_UI_MODES,
        index=AVAILABLE_UI_MODES.index(st.session_state["ui_mode"]),
    )
tr = get_translations(st.session_state["ui_mode"])
try:
    APP_VERSION = (Path(__file__).parent / "VERSION").read_text(encoding="utf-8").strip()
except OSError:
    APP_VERSION = ""
with st.sidebar:
    st.caption(f"{tr['version']} {APP_VERSION}")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    render_login(tr)
    st.stop()

role = st.session_state["role"]
user = st.session_state["user"]

if role == "company" and st.session_state.get("must_complete_profile"):
    company = get_company_by_id(st.session_state["company_id"])
    if not company:
        st.error("Company not found - Contact Admin")
        render_logout()
        st.stop()
    render_onboarding(tr, company)
    st.stop()

if role == "admin":
    st.markdown(f"# 🛡️ {tr['admin_title']}")
    tab_companies, tab_dashboard = st.tabs(
        [f"🏢 {tr['admin_tab_companies']}", f"📊 {tr['admin_tab_dashboard']}"]
    )
    with tab_companies:
        render_admin_companies(tr)
    with tab_dashboard:
        render_admin_dashboard(tr)
    with st.sidebar:
        st.markdown(f"👤 **{user['name']}** - Admin")
        render_logout()
    st.stop()

if role == "company":
    current_company = get_company_by_id(st.session_state["company_id"])
    if not current_company:
        st.error("Company not found")
        render_logout()
        st.stop()
    if not current_company.get("is_active", True):
        st.error("🚫 Account deactivated - Contact Admin")
        render_logout()
        st.stop()

    st.session_state["template_choice"] = current_company.get("template_choice", "both")
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        if current_company.get("logo_base64"):
            st.image(current_company["logo_base64"], width=120)
    with col_info:
        st.markdown(f"# {current_company['name']}")
        st.markdown(
            f"📍 {current_company.get('address', '')} - {current_company.get('city', '')}"
            f" | 📞 {current_company.get('phone', '')} | ✉️ {current_company.get('email', '')}"
        )
        st.markdown(
            f"ICE: {current_company.get('ice', '')} | RC: {current_company.get('rc', '')}"
            f" | 🏦 {current_company.get('bank_name', '')} - RIB: {current_company.get('bank_rib', '')}"
        )
    st.divider()

    choice = current_company.get("template_choice", "both")
    if choice not in ["plan", "banque", "both"]:
        choice = "both"

    handlers = []
    if choice in ["both", "plan"]:
        handlers.append((f"📋 {tr['tab_plan']}", "plan"))
    if choice in ["both", "banque"]:
        handlers.append((f"🏦 {tr['tab_banque']}", "banque"))
    handlers.append((f"🏢 {tr['company_tab']}", "my_company"))
    handlers.append((f"📜 {tr['logs_tab']}", "my_logs"))

    tabs = st.tabs([label for label, _ in handlers])
    for tab_obj, (_, handler) in zip(tabs, handlers):
        with tab_obj:
            if handler == "plan":
                render_plan_affaires(tr, current_company)
            elif handler == "banque":
                render_dossier_banque(tr, current_company)
            elif handler == "my_company":
                render_companies(tr, current_company, allow_create=False)
                render_change_password(tr, current_company)
            elif handler == "my_logs":
                st.subheader(f"{tr['logs_title']} - {current_company['name']}")
                st.dataframe(get_logs(current_company["id"], 100), use_container_width=True)

    with st.sidebar:
        st.markdown(f"👤 **{current_company['name']}** - @{current_company.get('username', '')}")
        st.info(f"Template: **{choice}**")
        render_logout()
    st.stop()
