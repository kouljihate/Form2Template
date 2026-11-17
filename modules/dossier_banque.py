import datetime

import streamlit as st

from database.db import save_banque
from templates.template_dossier_banque_ar import generate_pdf_ar
from templates.template_dossier_banque_fr import generate_pdf_fr


def render_dossier_banque(tr, current_company):
    st.subheader(f"🏦 {tr['tab_banque']}")
    with st.form("form_banque"):
        st.markdown(f"### {tr['banque_personal']}")
        col1, col2 = st.columns(2)
        with col1:
            nom_complet = st.text_input(tr["banque_nom"], placeholder="Ahmed El Idrissi")
            cin = st.text_input(tr["banque_cin"], placeholder="AB123456")
            adresse = st.text_input(tr["banque_adresse"], placeholder="Salé, Maroc")
            telephone = st.text_input(tr["banque_tel"], placeholder="06 12 34 56 78")
        with col2:
            nom_projet = st.text_input(tr["banque_projet"])
            localisation = st.text_input(tr["banque_localisation"])
            surface = st.number_input(tr["banque_surface"], min_value=0.1, value=1.0, step=0.1)
            type_projet = st.selectbox(tr["banque_type"], tr["banque_type_options"])

        st.markdown(f"### {tr['banque_financement']}")
        col3, col4 = st.columns(2)
        with col3:
            investissement_total = st.number_input(tr["banque_invest"], min_value=0, value=200000, step=1000)
            apport_personnel = st.number_input(tr["banque_apport"], min_value=0, value=60000, step=1000)
            montant_demande = st.number_input(tr["banque_montant"], min_value=0, value=140000, step=1000)
            duree_mois = st.number_input(tr["banque_duree"], min_value=12, value=60, step=12)
        with col4:
            revenu_annuel = st.number_input(tr["banque_revenu"], min_value=0, value=180000, step=1000)
            charges_annuel = st.number_input(tr["banque_charges"], min_value=0, value=60000, step=1000)
            garantie = st.selectbox(tr["banque_garantie"], tr["banque_garantie_options"])
            compte_bancaire = st.text_input(tr["banque_compte"], placeholder="Attijariwafa / BMCE / ...")

        output_lang = st.radio(tr["output_lang"], tr["output_options"], horizontal=True)
        submitted = st.form_submit_button(tr["generate"], use_container_width=True)

    if submitted:
        if not nom_complet.strip() or not nom_projet.strip():
            st.error(tr["required_fields"])
            return
        pdf_lang_code = "AR" if "Arabic" in output_lang else "FR"

        data = {
            "nom_complet": nom_complet.strip(),
            "cin": cin.strip(),
            "adresse": adresse.strip(),
            "telephone": telephone.strip(),
            "nom_projet": nom_projet.strip(),
            "localisation": localisation.strip(),
            "surface": surface,
            "type_projet": type_projet,
            "investissement_total": investissement_total,
            "apport_personnel": apport_personnel,
            "montant_demande": montant_demande,
            "duree_mois": duree_mois,
            "revenu_annuel": revenu_annuel,
            "charges_annuel": charges_annuel,
            "garantie": garantie,
            "compte_bancaire": compte_bancaire.strip(),
            "ui_language": st.session_state.get("ui_mode", ""),
            "pdf_lang_code": pdf_lang_code,
            "company_id": current_company["id"],
            "company_name": current_company["name"],
            "form": {
                "nom_complet": nom_complet.strip(),
                "cin": cin.strip(),
                "adresse": adresse.strip(),
                "telephone": telephone.strip(),
                "nom_projet": nom_projet.strip(),
                "localisation": localisation.strip(),
                "surface": surface,
                "type_projet": type_projet,
                "investissement_total": investissement_total,
                "apport_personnel": apport_personnel,
                "montant_demande": montant_demande,
                "duree_mois": duree_mois,
                "revenu_annuel": revenu_annuel,
                "charges_annuel": charges_annuel,
                "garantie": garantie,
                "compte_bancaire": compte_bancaire.strip(),
            },
        }

        pdf_buffer = generate_pdf_ar(data) if pdf_lang_code == "AR" else generate_pdf_fr(data)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in nom_complet if c.isalnum() or c in "_-") or "banque"
        data["pdf_bytes"] = pdf_buffer
        data["pdf_name"] = f"banque_{safe}_{timestamp}_{pdf_lang_code}.pdf"

        submission_id = save_banque(data)
        st.session_state["banque_result"] = {
            "bytes": pdf_buffer.getvalue(),
            "name": data["pdf_name"],
            "id": submission_id,
            "mensualite": montant_demande / duree_mois if duree_mois else 0,
        }

    result = st.session_state.get("banque_result")
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
            key="banque_download",
        )
        st.info(f"{tr['banque_mensualite']}: {result['mensualite']:,.0f} MAD / {tr['banque_mois']}")
