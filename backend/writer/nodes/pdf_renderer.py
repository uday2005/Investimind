import base64
import hashlib
import io
import logging
import re
from datetime import date
from html import escape

from backend.state import InvestMindState


logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[N(\d+)\]")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:60] or "investment-report"


def report_filename(report) -> str:
    report_hash = hashlib.sha256(
        report.model_dump_json().encode("utf-8")
    ).hexdigest()[:10]
    return f"{slugify(report.title)}-{report_hash}.pdf"


def paragraph_markup(content: str) -> str:
    escaped_content = escape(content).replace("\n", "<br/>")
    return CITATION_PATTERN.sub(
        lambda match: (
            f'<link href="#source-N{match.group(1)}" color="#087f8c">'
            f"[N{match.group(1)}]</link>"
        ),
        escaped_content,
    )


def cited_note_ids(report) -> list[int]:
    note_ids = set(report.executive_summary.cited_note_ids)

    for section in report.sections:
        note_ids.update(section.analysis.cited_note_ids)

    return sorted(note_ids)


def render_investment_report_pdf_bytes(
    report,
    research_notes,
) -> tuple[str, bytes]:
    """Render the investment report to PDF bytes in memory.

    Returns (filename, pdf_bytes). Nothing is written to disk -- the bytes are
    handed straight back so only the user's browser saves a copy.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )

    filename = report_filename(report)
    buffer = io.BytesIO()
    notes_by_id = {
        note_id: note
        for note_id, note in enumerate(research_notes, start=1)
    }

    navy = colors.HexColor("#17324D")
    teal = colors.HexColor("#087F8C")
    charcoal = colors.HexColor("#24323D")
    muted = colors.HexColor("#667783")
    light_rule = colors.HexColor("#D9E2E7")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=navy,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    metadata_style = ParagraphStyle(
        "ReportMetadata",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=muted,
        spaceAfter=5,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=navy,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.5,
        textColor=charcoal,
        spaceAfter=8,
        allowWidows=0,
        allowOrphans=0,
    )
    limitation_style = ParagraphStyle(
        "Limitation",
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-7,
        textColor=colors.HexColor("#6B3B2A"),
    )
    source_style = ParagraphStyle(
        "Source",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=charcoal,
        spaceAfter=7,
        splitLongWords=True,
    )
    source_label_style = ParagraphStyle(
        "SourceLabel",
        parent=source_style,
        fontName="Helvetica-Bold",
        textColor=teal,
        spaceAfter=2,
    )
    empty_style = ParagraphStyle(
        "Empty",
        parent=body_style,
        textColor=muted,
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title=report.title,
        author="InvestMind",
        subject="Evidence-grounded investment research report",
    )
    story = [
        Spacer(1, 8 * mm),
        Paragraph("INVESTMIND RESEARCH", metadata_style),
        Paragraph(escape(report.title), title_style),
        HRFlowable(width="100%", thickness=1.2, color=teal, spaceAfter=10),
        Paragraph(
            f"Generated {date.today().isoformat()} | Evidence-grounded analysis",
            metadata_style,
        ),
        Spacer(1, 5 * mm),
        Paragraph("Executive Summary", heading_style),
        Paragraph(
            paragraph_markup(report.executive_summary.content),
            body_style,
        ),
    ]

    for section in report.sections:
        story.extend(
            [
                Paragraph(escape(section.heading), heading_style),
                Paragraph(paragraph_markup(section.analysis.content), body_style),
            ]
        )

    story.append(Paragraph("Evidence Limitations", heading_style))
    if report.evidence_limitations:
        for limitation in report.evidence_limitations:
            story.append(
                Paragraph(f"- {escape(limitation)}", limitation_style)
            )
    else:
        story.append(
            Paragraph(
                "No additional evidence limitations were reported.",
                empty_style,
            )
        )

    story.extend([PageBreak(), Paragraph("Sources", heading_style)])

    source_count = 0
    for note_id in cited_note_ids(report):
        note = notes_by_id.get(note_id)
        if note is None:
            continue
        source_count += 1
        safe_url = escape(note.source_url, quote=True)
        story.append(
            Paragraph(
                f'<a name="source-N{note_id}"/><b>[N{note_id}]</b>',
                source_label_style,
            )
        )
        story.append(Paragraph(escape(note.content), source_style))
        story.append(
            Paragraph(
                f'Source: <link href="{safe_url}" color="#087f8c">'
                f"{escape(note.source_url)}</link><br/>"
                f"Search query: {escape(note.query)}",
                source_style,
            )
        )

    if source_count == 0:
        story.append(Paragraph("No cited sources were available.", empty_style))

    def draw_page(canvas, document):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(light_rule)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, height - 14 * mm, width - 20 * mm, height - 14 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(20 * mm, height - 11 * mm, "InvestMind Research")
        canvas.drawRightString(
            width - 20 * mm,
            height - 11 * mm,
            f"Page {document.page}",
        )
        canvas.line(20 * mm, 13 * mm, width - 20 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(
            width / 2,
            9 * mm,
            "Evidence-grounded research. Not investment advice.",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return filename, buffer.getvalue()


def pdf_renderer_node(state: InvestMindState):
    try:
        filename, pdf_bytes = render_investment_report_pdf_bytes(
            state["investment_report"],
            state["research_notes"],
        )
    except Exception as exc:
        logger.exception("Failed to render investment report PDF")
        return {
            "pdf_base64": None,
            "pdf_filename": None,
            "pdf_error": str(exc),
        }

    return {
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        "pdf_filename": filename,
        "pdf_error": None,
    }