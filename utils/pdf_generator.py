from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def generate_meal_plan_pdf(meal_plan_text, username):
    """Generate a PDF file containing the meal plan"""
    logger.info("Starting meal plan PDF generation")

    try:
        # Create temporary file with custom name
        pdf_name = f"Meal Plan for {username}.pdf"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{pdf_name}')
        pdf_path = temp_file.name
        temp_file.close()
        logger.debug(f"Created temporary file: {pdf_path}")

        # Create the PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Define colors
        darker_blue = colors.HexColor('#1E4D8C')  # Darker blue for headers
        subtitle_grey = colors.HexColor('#F0F0F0')  # Light grey for subtitle

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.black,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            backColor=subtitle_grey,
            borderPadding=10,
            alignment=1
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            backColor=darker_blue,
            textColor=colors.white,
            borderPadding=5
        )
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            leftIndent=20,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=8,
            leftIndent=40
        )
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.blue,
            spaceAfter=0,
            alignment=1
        )

        # Content
        content = []

        # Title and Subtitle
        content.append(Paragraph(f"Meal Plan for {username}", title_style))
        content.append(Spacer(1, 12))
        content.append(Paragraph("Personalized Nutrition Plan for Ramadan", subtitle_style))
        content.append(Spacer(1, 12))

        # Food image
        food_image_path = os.path.join('assets', 'food_image.jpg')
        if os.path.exists(food_image_path):
            food_img = Image(food_image_path, width=144, height=72)  # 2x1 inches
            content.append(food_img)
            content.append(Spacer(1, 12))

        # Parse the meal plan text into sections
        sections = meal_plan_text.split('\n\n')
        for section in sections:
            if section.strip():
                if "Total Macronutrients" in section:
                    content.append(Paragraph("Total Daily Macronutrients", heading_style))
                    content.append(Spacer(1, 12))

                    # Parse macronutrients into table data
                    rows = [['Nutrient', 'Amount']]
                    for line in section.split('\n')[1:]:
                        if ':' in line:
                            nutrient, amount = line.split(':', 1)
                            rows.append([nutrient.strip(), amount.strip()])

                    table = Table(rows)
                    table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), darker_blue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12)
                    ]))
                    content.append(table)
                    content.append(Spacer(1, 12))

                elif "Meal" in section:
                    if "Meals" not in locals():
                        content.append(Paragraph("Meals", heading_style))
                        content.append(Spacer(1, 12))
                        meals = True

                    # Add plate icon
                    plate_icon_path = os.path.join('assets', 'plate_icon.jpg')
                    if os.path.exists(plate_icon_path):
                        plate_img = Image(plate_icon_path, width=36, height=36)  # 0.5x0.5 inches
                        content.append(plate_img)
                        content.append(Spacer(1, 6))

                    # Add meal subheading
                    meal_name = section.split('\n')[0].upper()
                    content.append(Paragraph(meal_name, subheading_style))

                    # Add meal details
                    for line in section.split('\n')[1:]:
                        if line.strip():
                            content.append(Paragraph(line.strip(), body_style))
                    content.append(Spacer(1, 12))

                elif "Micronutrients" in section:
                    content.append(Paragraph("Total Micronutrients", heading_style))
                    content.append(Spacer(1, 12))
                    for line in section.split('\n')[1:]:
                        if line.strip():
                            content.append(Paragraph(line.strip(), body_style))
                    content.append(Spacer(1, 12))

        # Tips for Success section
        content.append(Paragraph("Tips for Success", heading_style))
        content.append(Spacer(1, 12))
        tips = [
            "Stay hydrated during non-fasting hours.",
            "Prioritize protein at Suhoor and Iftar.",
            "Adjust portions based on energy levels."
        ]
        for tip in tips:
            content.append(Paragraph(tip, body_style))

        # Footer
        content.append(Spacer(1, 20))
        content.append(Paragraph("Feel free to ask questions about your meal plan!", footer_style))

        # Build PDF
        doc.build(content)
        logger.info("PDF generation completed successfully")
        return pdf_path

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                logger.debug(f"Cleaned up temporary file: {pdf_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
        raise