"""خطة الأعمال - النسخة العربية."""

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

LANG = "AR"
LABEL = "خطة الأعمال - Permaculture App"


def generate_pdf_ar(data, pdf_path=None):
    """Build the Arabic business plan and return it as a BytesIO buffer."""
    style = styles(LANG)
    buffer, doc = build("خطة الأعمال")
    story = []

    header(
        story,
        style,
        "خطة الأعمال - مشروع زراعي",
        f"{data.get('company_name') or 'Permaculture App'} - {data.get('project') or ''}".strip(" -"),
        LANG,
    )

    section(story, style, "1. صاحب المشروع", LANG)
    story.append(
        info_table(
            [
                ("الاسم الكامل", data.get("name") or "-"),
                ("المشروع", data.get("project") or "-"),
                ("الموقع", data.get("location") or "-"),
                ("المساحة", f"{float(data.get('surface') or 0):g} هكتار"),
                ("طريقة الزراعة", data.get("method") or "-"),
            ],
            style,
            LANG,
            rtl=True,
        )
    )

    section(story, style, "2. الغرس", LANG)
    story.append(
        grid(
            ["النوع", "عدد الأشجار", "المردود (كغ/شجرة)", "الإنتاج (كغ)"],
            [
                ("الكرز", number(data.get("n_cer")), number(data.get("y_cer")), number(data.get("prod_cer"))),
                ("النكتارين", number(data.get("n_nec")), number(data.get("y_nec")), number(data.get("prod_nec"))),
                ("البرقوق", number(data.get("n_pru")), number(data.get("y_pru")), number(data.get("prod_pru"))),
            ],
            style,
            LANG,
            widths=[55 * mm, 30 * mm, 45 * mm, 44 * mm],
            rtl=True,
        )
    )
    spacer(story, 6)
    paragraph(story, style, f"مجموع الأشجار: {number(data.get('total_trees'))}", LANG)

    section(story, style, "3. رقم الأعمال التقديري", LANG)
    story.append(
        grid(
            ["السنة", "افتراض الإنتاج", "رقم الأعمال"],
            [
                ("السنة 1", pct(30), money(data.get("ca_year1"))),
                ("السنة 2", pct(60), money(data.get("ca_year2"))),
                ("السنة 3", pct(100), money(data.get("ca_year3"))),
            ],
            style,
            LANG,
            widths=[38 * mm, 70 * mm, 66 * mm],
            rtl=True,
        )
    )
    paragraph(
        story,
        style,
        "الافتراضات: الكرز 25 درهم/كغ، النكتارين 20 درهم/كغ، البرقوق 18 درهم/كغ. "
        "يرتفع الإنتاج تدريجياً (30% في السنة الأولى، 60% في السنة الثانية، 100% في السنة الثالثة) "
        "إلى أن تبلغ الأشجار كامل طاقتها الإنتاجية.",
        LANG,
    )

    section(story, style, "4. الخلاصة", LANG)
    surface = float(data.get("surface") or 0)
    ca_year3 = int(data.get("ca_year3") or 0)
    production = (data.get("prod_cer") or 0) + (data.get("prod_nec") or 0) + (data.get("prod_pru") or 0)
    story.append(
        info_table(
            [
                ("مجموع الأشجار", number(data.get("total_trees"))),
                ("الإنتاج المحتمل", f"{number(production)} كغ"),
                ("رقم الأعمال المستهدف (السنة 3)", money(ca_year3)),
                ("رقم الأعمال لكل هكتار (السنة 3)", money(ca_year3 / surface) if surface else "-"),
            ],
            style,
            LANG,
            rtl=True,
        )
    )

    spacer(story, 10)
    paragraph(
        story,
        style,
        "وثيقة مولدة تلقائياً. الأسعار والمردودية افتراضات عمل يجب تعديلها حسب ظروف السوق المحلية.",
        LANG,
    )

    return render(buffer, doc, story, LABEL, pdf_path)
