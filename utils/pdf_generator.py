from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def generate_meal_plan_pdf(meal_plan_text, username):
    """Generate a professional PDF meal plan document"""
    logger.info(f"Starting meal plan PDF generation for {username}")

    try:
        # Create temporary file
        pdf_name = f"Meal Plan for {username}.pdf"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{pdf_name}')
        pdf_path = temp_file.name
        temp_file.close()

        # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Get sample stylesheet and define custom styles
        styles = getSampleStyleSheet()

        # Title style - black text, professional look
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.black,
            alignment=1,  # Center alignment
            spaceAfter=6
        )

        # Subtitle style - light grey
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1,  # Center alignment
            spaceAfter=20
        )

        # Header style - royal blue background like in RIFT & TAPS
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.white,
            backColor=colors.HexColor('#4169E1'),  # Royal Blue
            borderPadding=6,
            alignment=0,
            spaceAfter=12
        )

        # Body text style
        text_style = ParagraphStyle(
            'CustomText',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=8,
            alignment=0  # Left alignment
        )

        # Footer style - italic
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.black,
            alignment=1  # Center alignment
        )

        # Start building content
        story = []

        # Title and subtitle
        story.append(Paragraph(f"RIFT & TAPS Ramadan Meal Plan", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Personalized plan for {username}", subtitle_style))
        story.append(Spacer(1, 20))

        # Process meal plan text
        sections = meal_plan_text.split('\n\n')

        for section in sections:
            if not section.strip():
                continue

            # Clean up section text
            section = section.replace('**', '').strip()
            lines = section.split('\n')

            if not lines:
                continue

            # Add section header
            header = lines[0].strip()
            story.append(Paragraph(header, header_style))
            story.append(Spacer(1, 8))

            if "Total Macronutrients" in header:
                # Create table for macronutrients
                table_data = []
                for line in lines[1:]:
                    if ':' in line:
                        nutrient, amount = line.split(':', 1)
                        table_data.append([nutrient.strip(), amount.strip()])

                if table_data:
                    # Create table with equal column widths
                    table = Table(table_data, colWidths=[doc.width/2.5]*2)
                    table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('TOPPADDING', (0, 0), (-1, -1), 12),
                        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    story.append(table)
            else:
                # Add meal content with macros on the same line
                for line in lines[1:]:
                    if line.strip():
                        # For meal items, combine food and macros in a clean format
                        if '|' in line:
                            food, macros = line.split('|', 1)
                            content = f"{food.strip()} ({macros.strip()})"
                        else:
                            content = line.strip()
                        story.append(Paragraph(content, text_style))

            story.append(Spacer(1, 12))

        # Add footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Feel free to ask questions about your meal plan!", footer_style))

        # Generate PDF
        doc.build(story)
        logger.info(f"PDF generation completed successfully for {username}")
        return pdf_path

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
        raise