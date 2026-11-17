"""ملف البنك - النسخة العربية."""

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
LABEL = "ملف البنك - Permaculture App"


def generate_pdf_ar(data, pdf_path=None):
    """Build the Arabic bank application and return it as a BytesIO buffer."""
    style = styles(LANG)
    buffer, doc = build("ملف طلب التمويل")
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
        "ملف طلب التمويل البنكي",
        f"{data.get('company_name') or 'Permaculture App'} - {data.get('nom_projet') or ''}".strip(" -"),
        LANG,
    )

    section(story, style, "1. طالب التمويل", LANG)
    story.append(
        info_table(
            [
                ("الاسم الكامل", data.get("nom_complet") or "-"),
                ("رقم البطاقة الوطنية", data.get("cin") or "-"),
                ("العنوان", data.get("adresse") or "-"),
                ("الهاتف", data.get("telephone") or "-"),
            ],
            style,
            LANG,
            rtl=True,
        )
    )

    section(story, style, "2. المشروع", LANG)
    story.append(
        info_table(
            [
                ("اسم المشروع", data.get("nom_projet") or "-"),
                ("الموقع", data.get("localisation") or "-"),
                ("المساحة", f"{float(data.get('surface') or 0):g} هكتار"),
                ("نوع المشروع", data.get("type_projet") or "-"),
            ],
            style,
            LANG,
            rtl=True,
        )
    )

    section(story, style, "3. مخطط التمويل", LANG)
    story.append(
        grid(
            ["البند", "المبلغ"],
            [
                ("الاستثمار الإجمالي", money(investissement)),
                ("المساهمة الشخصية", money(apport)),
                ("المبلغ المطلوب", money(montant)),
                ("نسبة التمويل", pct(montant / investissement * 100) if investissement else "-"),
                ("مدة السداد", f"{number(duree)} شهر"),
                ("القسط الشهري التقديري (بدون فوائد)", money(mensualite)),
            ],
            style,
            LANG,
            widths=[95 * mm, 79 * mm],
            rtl=True,
        )
    )

    section(story, style, "4. القدرة على السداد", LANG)
    story.append(
        grid(
            ["المؤشر", "القيمة"],
            [
                ("المدخول السنوي", money(revenu)),
                ("الأعباء السنوية", money(charges)),
                ("النتيجة الصافية السنوية", money(resultat_net)),
                ("القسط السنوي للسداد", money(mensualite * 12)),
                ("نسبة التغطية", f"{couverture:.2f}" if mensualite else "-"),
            ],
            style,
            LANG,
            widths=[95 * mm, 79 * mm],
            rtl=True,
        )
    )

    section(story, style, "5. الضمانات والتوطين البنكي", LANG)
    story.append(
        info_table(
            [
                ("الضمانة المقترحة", data.get("garantie") or "-"),
                ("الحساب البنكي", data.get("compte_bancaire") or "-"),
            ],
            style,
            LANG,
            rtl=True,
        )
    )

    spacer(story, 8)
    paragraph(
        story,
        style,
        "القسط الشهري المذكور تقديري وخطي بدون فوائد أو مصاريف الملف. "
        "تقارن نسبة التغطية النتيجة الصافية السنوية بالقسط السنوي للسداد.",
        LANG,
    )

    return render(buffer, doc, story, LABEL, pdf_path)
