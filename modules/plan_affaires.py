import datetime

import streamlit as st

from database.db import save_plan
from templates.template_plan_affaires_ar import generate_pdf_ar
from templates.template_plan_affaires_fr import generate_pdf_fr

# Reference prices in MAD/kg used by the revenue model.
PRICE_CER, PRICE_NEC, PRICE_PRU = 25, 20, 18
YEAR1_RATIO, YEAR2_RATIO = 0.3, 0.6


def render_plan_affaires(tr, current_company):
    st.subheader(f"📋 {tr['tab_plan']}")
    with st.form("form_plan"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(tr["name"], placeholder="Ahmed El Idrissi")
            project = st.text_input(tr["project"])
            location = st.text_input(tr["location"], placeholder="Salé, Maroc")
            surface = st.number_input(tr["surface"], min_value=0.1, value=1.0, step=0.1)
            method = st.selectbox(tr["method"], tr["method_options"])
        with col2:
            st.markdown(f"**{tr['trees_title']}**")
            n_cer = st.number_input(tr["cer"], min_value=0, value=50)
            n_nec = st.number_input(tr["nec"], min_value=0, value=30)
            n_pru = st.number_input(tr["pru"], min_value=0, value=20)
            st.markdown(f"**{tr['yield_title']}**")
            y_cer = st.number_input(tr["y_cer"], min_value=0.0, value=20.0)
            y_nec = st.number_input(tr["y_nec"], min_value=0.0, value=15.0)
            y_pru = st.number_input(tr["y_pru"], min_value=0.0, value=18.0)
        output_lang = st.radio(tr["output_lang"], tr["output_options"], horizontal=True)
        submitted = st.form_submit_button(tr["generate"], use_container_width=True)

    if submitted:
        if not name.strip():
            st.error(tr["required_fields"])
            return
        total_trees = n_cer + n_nec + n_pru
        prod_cer, prod_nec, prod_pru = n_cer * y_cer, n_nec * y_nec, n_pru * y_pru
        ca_year3 = int(prod_cer * PRICE_CER + prod_nec * PRICE_NEC + prod_pru * PRICE_PRU)
        ca_year1 = int(ca_year3 * YEAR1_RATIO)
        ca_year2 = int(ca_year3 * YEAR2_RATIO)
        pdf_lang_code = "AR" if "Arabic" in output_lang else "FR"

        data = {
            "name": name.strip(),
            "project": project.strip(),
            "location": location.strip(),
            "surface": surface,
            "method": method,
            "n_cer": n_cer,
            "n_nec": n_nec,
            "n_pru": n_pru,
            "y_cer": y_cer,
            "y_nec": y_nec,
            "y_pru": y_pru,
            "total_trees": total_trees,
            "prod_cer": prod_cer,
            "prod_nec": prod_nec,
            "prod_pru": prod_pru,
            "ca_year1": ca_year1,
            "ca_year2": ca_year2,
            "ca_year3": ca_year3,
            "ui_language": st.session_state.get("ui_mode", ""),
            "pdf_lang_code": pdf_lang_code,
            "company_id": current_company["id"],
            "company_name": current_company["name"],
            "form": {
                "name": name.strip(),
                "project": project.strip(),
                "location": location.strip(),
                "surface": surface,
                "method": method,
                "trees": {"cer": n_cer, "nec": n_nec, "pru": n_pru},
                "yields": {"cer": y_cer, "nec": y_nec, "pru": y_pru},
            },
        }

        pdf_buffer = generate_pdf_ar(data) if pdf_lang_code == "AR" else generate_pdf_fr(data)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in name if c.isalnum() or c in "_-") or "plan"
        data["pdf_bytes"] = pdf_buffer
        data["pdf_name"] = f"plan_{safe}_{timestamp}_{pdf_lang_code}.pdf"

        submission_id = save_plan(data)
        st.session_state["plan_result"] = {
            "bytes": pdf_buffer.getvalue(),
            "name": data["pdf_name"],
            "id": submission_id,
        }

    result = st.session_state.get("plan_result")
    if result:
        message = tr["success"]
        if result["id"]:
            message += f" | {tr['saved_id']}: #{result['id']}"
        st.success(message)
        st.download_button(
            tr["download"],
            result["bytes"],
            file_name=result["name"],
            mime="application/pdf",
            key="plan_download",
        )
