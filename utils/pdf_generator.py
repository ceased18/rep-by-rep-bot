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

        # Title style - black text, clean and professional
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.black,
            alignment=1,  # Center alignment
            spaceAfter=6
        )

        # Subtitle style - light grey, smaller
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.grey,
            alignment=1,  # Center alignment
            spaceAfter=20
        )

        # Header style - blue background like RIFT & TAPS
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

        # Normal text style
        text_style = ParagraphStyle(
            'CustomText',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=8
        )

        # Footer style - italic text
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.black,
            alignment=1,  # Center alignment
            spaceAfter=0
        )

        # Start building content
        story = []

        # Add title and subtitle
        story.append(Paragraph(f"Meal Plan for {username}", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Personalized Nutrition Plan for Ramadan", subtitle_style))
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

            if "Total Macronutrients" in header:
                # Create table for macronutrients
                table_data = []
                for line in lines[1:]:
                    if ':' in line:
                        nutrient, amount = line.split(':', 1)
                        table_data.append([nutrient.strip(), amount.strip()])

                if table_data:
                    table = Table(table_data, colWidths=[doc.width/2]*2)
                    table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    story.append(table)
            else:
                # Add regular text content
                for line in lines[1:]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), text_style))

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