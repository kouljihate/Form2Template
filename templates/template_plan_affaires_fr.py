"""Plan d'affaires - version francaise."""

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
LABEL = "Plan d'affaires - Permaculture App"


def generate_pdf_fr(data, pdf_path=None):
    """Build the French business plan and return it as a BytesIO buffer."""
    style = styles(LANG)
    buffer, doc = build("Plan d'affaires")
    story = []

    header(
        story,
        style,
        "Plan d'affaires - Projet de permaculture",
        f"{data.get('company_name') or 'Permaculture App'} - {data.get('project') or ''}".strip(" -"),
        LANG,
    )

    section(story, style, "1. Porteur de projet", LANG)
    story.append(
        info_table(
            [
                ("Nom complet", data.get("name") or "-"),
                ("Projet", data.get("project") or "-"),
                ("Localisation", data.get("location") or "-"),
                ("Surface", f"{float(data.get('surface') or 0):g} ha"),
                ("Methode de culture", data.get("method") or "-"),
            ],
            style,
            LANG,
        )
    )

    section(story, style, "2. Plantation", LANG)
    story.append(
        grid(
            ["Espece", "Arbres", "Rendement (kg/arbre)", "Production (kg)"],
            [
                ("Cerisiers", number(data.get("n_cer")), number(data.get("y_cer")), number(data.get("prod_cer"))),
                ("Nectarines", number(data.get("n_nec")), number(data.get("y_nec")), number(data.get("prod_nec"))),
                ("Pruniers", number(data.get("n_pru")), number(data.get("y_pru")), number(data.get("prod_pru"))),
            ],
            style,
            LANG,
            widths=[55 * mm, 30 * mm, 45 * mm, 44 * mm],
        )
    )
    spacer(story, 6)
    paragraph(story, style, f"Total arbres : {number(data.get('total_trees'))}", LANG)

    section(story, style, "3. Chiffre d'affaires previsionnel", LANG)
    story.append(
        grid(
            ["Annee", "Hypothese de production", "Chiffre d'affaires"],
            [
                ("Annee 1", pct(30), money(data.get("ca_year1"))),
                ("Annee 2", pct(60), money(data.get("ca_year2"))),
                ("Annee 3", pct(100), money(data.get("ca_year3"))),
            ],
            style,
            LANG,
            widths=[38 * mm, 70 * mm, 66 * mm],
        )
    )
    paragraph(
        story,
        style,
        "Hypotheses : cerise 25 MAD/kg, nectarine 20 MAD/kg, pruneau 18 MAD/kg. "
        "Le potentiel de production est atteint progressivement (30 % en annee 1, "
        "60 % en annee 2, 100 % en annee 3), le temps que les arbres entrent en pleine production.",
        LANG,
    )

    section(story, style, "4. Synthese", LANG)
    surface = float(data.get("surface") or 0)
    ca_year3 = int(data.get("ca_year3") or 0)
    story.append(
        info_table(
            [
                ("Nombre total d'arbres", number(data.get("total_trees"))),
                ("Production potentielle", f"{number((data.get('prod_cer') or 0) + (data.get('prod_nec') or 0) + (data.get('prod_pru') or 0))} kg"),
                ("Chiffre d'affaires cible (annee 3)", money(ca_year3)),
                ("Chiffre d'affaires par hectare (annee 3)", money(ca_year3 / surface) if surface else "-"),
            ],
            style,
            LANG,
        )
    )

    spacer(story, 10)
    paragraph(
        story,
        style,
        "Document genere automatiquement. Les prix et rendements sont des hypotheses de "
        "travail a ajuster selon les conditions locales du marche.",
        LANG,
    )

    return render(buffer, doc, story, LABEL, pdf_path)
