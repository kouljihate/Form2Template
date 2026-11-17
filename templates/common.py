"""Shared ReportLab helpers used by the FR/AR PDF templates."""

import io
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:  # Arabic shaping is optional: text is still drawn when these are absent.
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:  # pragma: no cover - depends on the installed packages
    arabic_reshaper = None
    get_display = None

BRAND = colors.HexColor("#2E7D32")
BRAND_DARK = colors.HexColor("#1B5E20")
BRAND_LIGHT = colors.HexColor("#E8F5E9")
BRAND_ALT = colors.HexColor("#F4FAF4")
MUTED = colors.HexColor("#5F6368")
BORDER = colors.HexColor("#C8E6C9")
INK = colors.HexColor("#1B1B1B")

_REGULAR_CANDIDATES = (
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
)
_BOLD_CANDIDATES = (
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\tahomabd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
)

_font_pair = None


def _first_existing(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def fonts():
    """Register a Unicode TTF once and return the ``(regular, bold)`` names."""
    global _font_pair
    if _font_pair:
        return _font_pair
    regular = _first_existing(_REGULAR_CANDIDATES)
    bold = _first_existing(_BOLD_CANDIDATES)
    _font_pair = ("Helvetica", "Helvetica-Bold")
    if regular:
        try:
            pdfmetrics.registerFont(TTFont("DocFont", regular))
            _font_pair = ("DocFont", "DocFont")
            if bold:
                pdfmetrics.registerFont(TTFont("DocFont-Bold", bold))
                _font_pair = ("DocFont", "DocFont-Bold")
        except Exception:  # unreadable font -> fall back to the built-ins
            _font_pair = ("Helvetica", "Helvetica-Bold")
    return _font_pair


def arabic(text):
    """Reshape and reorder Arabic so ReportLab draws joined, right-to-left text."""
    value = str(text)
    if get_display is None or not value:
        return value
    try:
        return get_display(arabic_reshaper.reshape(value))
    except Exception:  # never fail a document because of a shaping quirk
        return value


def localize(text, lang):
    """Pick the right half of a bilingual "AR / FR" label."""
    value = "" if text is None else str(text)
    if " / " in value:
        left, right = value.split(" / ", 1)
        return left if str(lang).upper() == "AR" else right
    return value


def tx(text, lang):
    """Prepare a value for a Paragraph: localise, escape markup, shape Arabic."""
    value = escape(localize(text, lang))
    return arabic(value) if str(lang).upper() == "AR" else value


def number(value):
    """Format a number with a thin thousands separator, e.g. ``120 000``."""
    try:
        return f"{int(round(float(value))):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def money(value):
    return f"{number(value)} MAD"


def pct(value):
    try:
        return f"{float(value):.1f} %"
    except (TypeError, ValueError):
        return "-"


def styles(lang):
    """Return the paragraph styles for a document written in ``lang``."""
    regular, bold = fonts()
    rtl = str(lang).upper() == "AR"
    align = TA_RIGHT if rtl else TA_LEFT
    return {
        "title": ParagraphStyle(
            "title", fontName=bold, fontSize=19, leading=24,
            textColor=BRAND_DARK, alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=regular, fontSize=9.5, leading=13,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "section", fontName=bold, fontSize=12.5, leading=16,
            textColor=BRAND_DARK, spaceBefore=12, spaceAfter=5, alignment=align,
        ),
        "body": ParagraphStyle(
            "body", fontName=regular, fontSize=10, leading=15,
            textColor=INK, alignment=align,
        ),
        "cell": ParagraphStyle(
            "cell", fontName=regular, fontSize=9.5, leading=13,
            textColor=INK, alignment=align,
        ),
        "head": ParagraphStyle(
            "head", fontName=bold, fontSize=9.5, leading=13,
            textColor=colors.white, alignment=align,
        ),
        "note": ParagraphStyle(
            "note", fontName=regular, fontSize=8.5, leading=12,
            textColor=MUTED, alignment=align, spaceBefore=4,
        ),
    }


def build(title):
    """Create the buffer and the document; return ``(buffer, doc)``."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="Permaculture App",
        subject=title,
    )
    return buffer, doc


def footer(label):
    """Draw a rule, the label and the page number at the bottom of each page."""
    regular, _ = fonts()

    def draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
        canvas.setFont(regular, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 11 * mm, label)
        canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, str(doc.page))
        canvas.restoreState()

    return draw


def header(story, style, title, subtitle, lang):
    story.append(Paragraph(tx(title, lang), style["title"]))
    if subtitle:
        story.append(Paragraph(tx(subtitle, lang), style["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND, spaceAfter=10))


def section(story, style, title, lang):
    story.append(Paragraph(tx(title, lang), style["section"]))


def info_table(rows, style, lang, label_width=45 * mm, value_width=129 * mm, rtl=False):
    """Two-column label/value block."""
    data = [
        [Paragraph(tx(label, lang), style["cell"]), Paragraph(tx(value, lang), style["cell"])]
        for label, value in rows
    ]
    table = Table(data, colWidths=[label_width, value_width], hAlign="RIGHT" if rtl else "LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def grid(columns, rows, style, lang, widths, rtl=False):
    """Table with a coloured header row and zebra striping."""
    data = [[Paragraph(tx(column, lang), style["head"]) for column in columns]]
    for row in rows:
        data.append([Paragraph(tx(cell, lang), style["cell"]) for cell in row])
    table = Table(data, colWidths=list(widths), hAlign="RIGHT" if rtl else "LEFT", repeatRows=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for index in range(2, len(data), 2):
        commands.append(("BACKGROUND", (0, index), (-1, index), BRAND_ALT))
    table.setStyle(TableStyle(commands))
    return table


def paragraph(story, style, text, lang):
    story.append(Paragraph(tx(text, lang), style["body"]))


def spacer(story, height=6):
    story.append(Spacer(1, height))


def render(buffer, doc, story, label, pdf_path=None):
    """Build the PDF, optionally mirror it on disk, and return the buffer."""
    draw_footer = footer(label)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    payload = buffer.getvalue()
    if pdf_path:
        directory = os.path.dirname(pdf_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(pdf_path, "wb") as handle:
            handle.write(payload)
    buffer.seek(0)
    return buffer
