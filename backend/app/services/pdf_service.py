import io
from datetime import date
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.invoices import Invoice
from app.core.money import sub_money, ZERO

def generate_invoice_pdf(invoice: Invoice) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#334155')
    )

    text_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )

    bold_text_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []

    # Header section
    header_data = [
        [
            Paragraph("<b>BRIGHTLOOP SOFTWARE</b><br/><font size=8 color='#64748b'>Subscription Billing System<br/>billing@brightloop.local</font>", text_style),
            Paragraph(f"<b>INVOICE</b><br/><font size=12 color='#2563eb'><b>{invoice.number}</b></font><br/><font size=8 color='#64748b'>Status: <b>{invoice.status.value.upper()}</b></font>", ParagraphStyle('RAlign', parent=text_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=15))

    # Bill To & Meta info
    addr = invoice.customer_snapshot.billing_address
    addr_line = f"{addr.line1}, {addr.city}, {addr.state} {addr.zip}".strip(", ")
    if addr.country:
        addr_line += f", {addr.country}"

    bill_to_text = f"<b>{invoice.customer_snapshot.name}</b>"
    if addr_line:
        bill_to_text += f"<br/>{addr_line}"
    if invoice.customer_snapshot.tax_id:
        bill_to_text += f"<br/>Tax ID: {invoice.customer_snapshot.tax_id}"

    info_data = [
        [
            Paragraph("<b>BILLED TO:</b>", heading_style),
            Paragraph("<b>INVOICE DETAILS:</b>", heading_style)
        ],
        [
            Paragraph(bill_to_text, text_style),
            Paragraph(
                f"<b>Issue Date:</b> {invoice.issue_date}<br/>"
                f"<b>Due Date:</b> {invoice.due_date}<br/>"
                f"<b>Billing Period:</b> {invoice.period_start} to {invoice.period_end}",
                text_style
            )
        ]
    ]
    info_table = Table(info_data, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Itemized Table
    line_headers = ["Item Description", "Qty", "Unit Price", "Discount", "Tax", "Line Total"]
    table_data = [[Paragraph(f"<b>{h}</b>", bold_text_style) for h in line_headers]]

    for line in invoice.lines:
        desc = line.product_name
        if line.variant_label:
            desc += f"<br/><font size=8 color='#64748b'>{line.variant_label}</font>"
        
        tax_str = "$0.00"
        if line.tax_breakdown:
            tot_tax = sum((tb.amount for tb in line.tax_breakdown), ZERO)
            tax_str = f"${tot_tax:.2f}"

        disc_str = f"${line.discount_amount:.2f}" if line.discount_amount > ZERO else "-"

        table_data.append([
            Paragraph(desc, text_style),
            Paragraph(str(line.quantity), ParagraphStyle('Center', parent=text_style, alignment=1)),
            Paragraph(f"${line.unit_price:.2f}", ParagraphStyle('Right', parent=text_style, alignment=2)),
            Paragraph(disc_str, ParagraphStyle('Right', parent=text_style, alignment=2)),
            Paragraph(tax_str, ParagraphStyle('Right', parent=text_style, alignment=2)),
            Paragraph(f"${line.line_total:.2f}", ParagraphStyle('Right', parent=bold_text_style, alignment=2)),
        ])

    lines_table = Table(table_data, colWidths=[2.6 * inch, 0.6 * inch, 1.0 * inch, 0.9 * inch, 0.9 * inch, 1.0 * inch])
    lines_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
    ]))
    elements.append(lines_table)
    elements.append(Spacer(1, 15))

    # Summary Totals Table
    balance_due = sub_money(invoice.total, invoice.amount_paid)
    summary_data = [
        [Paragraph("Subtotal:", bold_text_style), Paragraph(f"${invoice.subtotal:.2f}", ParagraphStyle('R', parent=text_style, alignment=2))],
        [Paragraph("Discounts:", text_style), Paragraph(f"-${invoice.discount_total:.2f}", ParagraphStyle('R', parent=text_style, alignment=2))],
        [Paragraph("Taxes:", text_style), Paragraph(f"+${invoice.tax_total:.2f}", ParagraphStyle('R', parent=text_style, alignment=2))],
        [Paragraph("<b>Total Amount:</b>", bold_text_style), Paragraph(f"<b>${invoice.total:.2f}</b>", ParagraphStyle('R', parent=bold_text_style, alignment=2))],
        [Paragraph("Amount Paid:", text_style), Paragraph(f"${invoice.amount_paid:.2f}", ParagraphStyle('R', parent=text_style, alignment=2))],
        [Paragraph("<b>Balance Due:</b>", bold_text_style), Paragraph(f"<b>${balance_due:.2f}</b>", ParagraphStyle('R', parent=bold_text_style, alignment=2))]
    ]
    summary_table = Table(summary_data, colWidths=[1.8 * inch, 1.4 * inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 2), (-1, 2), 0.5, colors.HexColor('#cbd5e1')),
        ('LINEBELOW', (0, 3), (-1, 3), 1, colors.HexColor('#94a3b8')),
    ]))

    # Wrap summary table in right-aligned container
    totals_container = Table(
        [[Paragraph("", text_style), summary_table]],
        colWidths=[3.8 * inch, 3.2 * inch]
    )
    totals_container.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(totals_container)

    # Footer note
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=10))
    elements.append(Paragraph("<font size=8 color='#94a3b8'>Thank you for your business. For billing inquiries, contact billing@brightloop.local. Generated electronically by Brightloop Subscription Management System.</font>", ParagraphStyle('CenterM', parent=text_style, alignment=1)))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
