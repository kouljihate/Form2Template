import streamlit as st

from database.db import (
    admin_reset_password,
    create_company_by_admin,
    delete_company,
    get_companies,
    get_logs,
    send_company_welcome_whatsapp,
    update_company,
    USE_MONGO,
)

TEMPLATE_CHOICES = {"both": "template_both", "plan": "template_plan", "banque": "template_banque"}


def _t(tr, key, default=""):
    value = tr.get(key)
    return value if value else (default or key)


def _flash(message):
    st.session_state["admin_flash"] = message


def _show_flash():
    message = st.session_state.pop("admin_flash", None)
    if message:
        st.success(message)


def _template_options(tr):
    return {code: _t(tr, key) for code, key in TEMPLATE_CHOICES.items()}


def _app_url():
    try:
        return st.secrets.get("app", {}).get("url", "")
    except Exception:
        return ""


def render_admin_companies(tr):
    """Admin tab: create, edit, deactivate and delete company accounts."""
    _show_flash()
    st.subheader(f"🏢 {_t(tr, 'admin_tab_companies')}")

    if not USE_MONGO:
        st.warning(_t(tr, "admin_need_mongo"))
        return

    companies = get_companies(include_inactive=True)
    active = [c for c in companies if c.get("is_active")]
    pending = [c for c in companies if c.get("must_complete_profile")]
    col1, col2, col3 = st.columns(3)
    col1.metric(_t(tr, "admin_total"), len(companies))
    col2.metric(_t(tr, "admin_active"), len(active))
    col3.metric(_t(tr, "admin_pending"), len(pending))

    tab_create, tab_manage = st.tabs([_t(tr, "admin_create"), _t(tr, "admin_manage")])
    with tab_create:
        _render_create(tr)
    with tab_manage:
        _render_manage(tr, companies)


def _render_create(tr):
    options = _template_options(tr)
    with st.form("admin_create_company"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(_t(tr, "admin_new_name"))
            username = st.text_input(_t(tr, "admin_new_username"))
            password = st.text_input(_t(tr, "admin_new_password"), type="password", value="admin-admin")
            email = st.text_input(_t(tr, "admin_new_email"))
        with col2:
            city = st.text_input(_t(tr, "admin_new_city"))
            phone = st.text_input(_t(tr, "admin_new_phone"))
            template = st.selectbox(
                _t(tr, "admin_new_template"),
                list(options),
                format_func=lambda code: options[code],
            )
            send_whatsapp = st.checkbox(_t(tr, "admin_send_whatsapp"), value=True)
        submitted = st.form_submit_button(_t(tr, "admin_create_btn"), type="primary", use_container_width=True)

    if not submitted:
        return
    if not name.strip() or not username.strip() or len(password) < 6:
        st.error(_t(tr, "admin_pw_short"))
        return

    company_id, message, whatsapp_sent = create_company_by_admin(
        {
            "name": name.strip(),
            "username": username.strip(),
            "password": password,
            "email": email.strip(),
            "city": city.strip(),
            "phone": phone.strip(),
            "template_choice": template,
            "send_whatsapp": send_whatsapp,
            "app_url": _app_url(),
        }
    )
    if company_id:
        detail = _t(tr, "admin_created") + f" ({username.strip()})"
        if send_whatsapp:
            detail += " - WhatsApp ✅" if whatsapp_sent else " - WhatsApp ❌"
        _flash(detail)
        st.rerun()
    else:
        st.error(message)


def _render_manage(tr, companies):
    if not companies:
        st.info(_t(tr, "admin_no_companies"))
        return

    labels = {f"{c.get('name', '?')} (@{c.get('username', '')})": c for c in companies}
    selected_label = st.selectbox(_t(tr, "admin_select"), list(labels))
    company = labels[selected_label]
    company_id = company["id"]

    status = _t(tr, "admin_active") if company.get("is_active", True) else _t(tr, "admin_inactive")
    col1, col2, col3 = st.columns(3)
    col1.metric(_t(tr, "admin_status"), status)
    col2.metric("Logins", company.get("login_count", 0))
    col3.metric(_t(tr, "admin_new_city"), company.get("city") or "-")

    options = _template_options(tr)
    current_template = company.get("template_choice", "both")
    if current_template not in options:
        current_template = "both"
    with st.form(f"admin_edit_{company_id}"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(_t(tr, "admin_new_name"), value=company.get("name", ""))
            city = st.text_input(_t(tr, "admin_new_city"), value=company.get("city", ""))
            phone = st.text_input(_t(tr, "admin_new_phone"), value=company.get("phone", ""))
        with col2:
            email = st.text_input(_t(tr, "admin_new_email"), value=company.get("email", ""))
            template = st.selectbox(
                _t(tr, "admin_new_template"),
                list(options),
                index=list(options).index(current_template),
                format_func=lambda code: options[code],
            )
            is_active = st.checkbox(_t(tr, "admin_active"), value=company.get("is_active", True))
        submitted = st.form_submit_button(_t(tr, "admin_save"), type="primary", use_container_width=True)

    if submitted:
        update_company(
            company_id,
            {
                "name": name.strip(),
                "city": city.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "template_choice": template,
                "is_active": is_active,
            },
        )
        _flash(_t(tr, "admin_saved"))
        st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        with st.form(f"admin_reset_{company_id}"):
            new_password = st.text_input(_t(tr, "admin_pw_label"), type="password")
            reset = st.form_submit_button(_t(tr, "admin_reset_btn"), use_container_width=True)
        if reset:
            if len(new_password) < 6:
                st.error(_t(tr, "admin_pw_short"))
            else:
                admin_reset_password(company_id, new_password)
                _flash(_t(tr, "admin_reset_btn") + " ✅")
                st.rerun()
    with col2:
        if st.button(_t(tr, "admin_resend"), use_container_width=True):
            sent, detail = send_company_welcome_whatsapp(company, _app_url())
            if sent:
                _flash("WhatsApp ✅")
            else:
                st.error(f"WhatsApp ❌ - {detail}")
        st.caption(_t(tr, "admin_username") + f": @{company.get('username', '')}")

    with st.expander(f"⚠️ {_t(tr, 'admin_delete')}"):
        confirmed = st.checkbox(_t(tr, "admin_delete_confirm"), key=f"admin_confirm_{company_id}")
        if st.button(_t(tr, "admin_delete"), disabled=not confirmed, key=f"admin_delete_{company_id}"):
            if delete_company(company_id):
                _flash(_t(tr, "admin_deleted"))
                st.rerun()
            else:
                st.error(_t(tr, "admin_no_companies"))

    st.divider()
    st.markdown(f"#### 📜 {_t(tr, 'admin_logs')}")
    st.dataframe(get_logs(None, 30), use_container_width=True, hide_index=True)
