"""Dossier banque - version francaise."""

from reportlab.lib.units import mm

from .common import (
    build,
    grid,
    header,
    info_table,
    money,
    number,
    paragraph,
    pct,
    render,
    section,
    spacer,
    styles,
)

LANG = "FR"
LABEL = "Dossier bancaire - Permaculture App"


def generate_pdf_fr(data, pdf_path=None):
    """Build the French bank application and return it as a BytesIO buffer."""
    style = styles(LANG)
    buffer, doc = build("Dossier de financement")
    story = []

    investissement = float(data.get("investissement_total") or 0)
    apport = float(data.get("apport_personnel") or 0)
    montant = float(data.get("montant_demande") or 0)
    duree = float(data.get("duree_mois") or 0)
    revenu = float(data.get("revenu_annuel") or 0)
    charges = float(data.get("charges_annuel") or 0)
    mensualite = montant / duree if duree else 0
    resultat_net = revenu - charges
    couverture = resultat_net / (mensualite * 12) if mensualite else 0

    header(
        story,
        style,
        "Dossier de demande de financement",
        f"{data.get('company_name') or 'Permaculture App'} - {data.get('nom_projet') or ''}".strip(" -"),
        LANG,
    )

    section(story, style, "1. Demandeur", LANG)
    story.append(
        info_table(
            [
                ("Nom complet", data.get("nom_complet") or "-"),
                ("CIN", data.get("cin") or "-"),
                ("Adresse", data.get("adresse") or "-"),
                ("Telephone", data.get("telephone") or "-"),
            ],
            style,
            LANG,
        )
    )

    section(story, style, "2. Projet", LANG)
    story.append(
        info_table(
            [
                ("Intitule du projet", data.get("nom_projet") or "-"),
                ("Localisation", data.get("localisation") or "-"),
                ("Surface", f"{float(data.get('surface') or 0):g} ha"),
                ("Type de projet", data.get("type_projet") or "-"),
            ],
            style,
            LANG,
        )
    )

    section(story, style, "3. Plan de financement", LANG)
    story.append(
        grid(
            ["Poste", "Montant"],
            [
                ("Investissement total", money(investissement)),
                ("Apport personnel", money(apport)),
                ("Montant demande", money(montant)),
                ("Part financee", pct(montant / investissement * 100) if investissement else "-"),
                ("Duree de remboursement", f"{number(duree)} mois"),
                ("Mensualite estimee (hors interets)", money(mensualite)),
            ],
            style,
            LANG,
            widths=[95 * mm, 79 * mm],
        )
    )

    section(story, style, "4. Capacite de remboursement", LANG)
    story.append(
        grid(
            ["Indicateur", "Valeur"],
            [
                ("Revenu annuel", money(revenu)),
                ("Charges annuelles", money(charges)),
                ("Resultat net annuel", money(resultat_net)),
                ("Annuité de remboursement", money(mensualite * 12)),
                ("Ratio de couverture", f"{couverture:.2f}" if mensualite else "-"),
            ],
            style,
            LANG,
            widths=[95 * mm, 79 * mm],
        )
    )

    section(story, style, "5. Garanties et domiciliation", LANG)
    story.append(
        info_table(
            [
                ("Garantie proposee", data.get("garantie") or "-"),
                ("Compte bancaire", data.get("compte_bancaire") or "-"),
            ],
            style,
            LANG,
        )
    )

    spacer(story, 8)
    paragraph(
        story,
        style,
        "La mensualite indiquee est une estimation lineaire hors interets et frais de dossier. "
        "Le ratio de couverture compare le resultat net annuel a l'annuite de remboursement.",
        LANG,
    )

    return render(buffer, doc, story, LABEL, pdf_path)
