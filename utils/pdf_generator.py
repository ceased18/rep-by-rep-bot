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

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            backColor=colors.green,
            textColor=colors.white,
            borderPadding=10
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            backColor=colors.lightblue,
            borderPadding=5
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=12,
            bulletColor=colors.red
        )
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.blue,
            spaceAfter=0
        )

        # Content
        content = []
        try:
            # Add title
            content.append(Paragraph(f"Your Personalized Meal Plan", title_style))
            content.append(Spacer(1, 12))

            # Add meal icon at the top
            meal_icon_path = os.path.join('assets', 'meal icon.jpg')
            if os.path.exists(meal_icon_path):
                meal_img = Image(meal_icon_path, width=144, height=72)  # 2x1 inches (72 points per inch)
                content.append(meal_img)
                content.append(Spacer(1, 12))
            else:
                logger.warning(f"Meal icon not found at {meal_icon_path}")

            # Parse the meal plan text into sections
            sections = meal_plan_text.split('\n\n')
            for section in sections:
                if section.strip():
                    if "Total Macronutrients" in section:
                        # Add section heading
                        content.append(Paragraph("Total Macronutrients", heading_style))
                        content.append(Spacer(1, 12))

                        # Parse macronutrients into table data
                        rows = [['Nutrient', 'Amount']]
                        for line in section.split('\n')[1:]:  # Skip the heading
                            if ':' in line:
                                nutrient, amount = line.split(':', 1)
                                rows.append([nutrient.strip(), amount.strip()])

                        # Create table with alternating colors
                        table = Table(rows)
                        table.setStyle(TableStyle([
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 14),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
                        ]))
                        content.append(table)
                        content.append(Spacer(1, 12))
                    elif "Meal" in section:
                        # Add plate icon before meal sections
                        plate_icon_path = os.path.join('assets', 'plate icon.jpg')
                        if os.path.exists(plate_icon_path):
                            plate_img = Image(plate_icon_path, width=36, height=36)  # 0.5x0.5 inches
                            content.append(plate_img)
                            content.append(Spacer(1, 6))

                        # Add section heading
                        heading = section.split('\n')[0]
                        content.append(Paragraph(heading, heading_style))
                        content.append(Spacer(1, 12))

                        # Add bullet points with red bullets
                        for line in section.split('\n')[1:]:
                            if line.strip():
                                content.append(Paragraph(f"• {line.strip()}", body_style))
                    else:
                        content.append(Paragraph(section, body_style))
                    content.append(Spacer(1, 12))

            # Add Tips for Success section
            content.append(Spacer(1, 20))
            content.append(Paragraph("Tips for Success", heading_style))
            content.append(Spacer(1, 12))
            
            tips = [
                "Stay hydrated during non-fasting hours.",
                "Prioritize protein at Suhoor and Iftar.",
                "Adjust portions based on energy levels."
            ]
            for tip in tips:
                content.append(Paragraph(f"• {tip}", body_style))
            
            # Add footer text in blue italic
            content.append(Spacer(1, 20))  # Add extra space before footer
            content.append(Paragraph("Feel free to ask questions about your meal plan!", footer_style))

            # Build PDF
            doc.build(content)
            logger.info("PDF generation completed successfully")
            return pdf_path

        except Exception as e:
            logger.error(f"Error creating PDF content: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        # Clean up temporary file if it exists
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                logger.debug(f"Cleaned up temporary file: {pdf_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
        raise