from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile
import os
import logging
import re

logger = logging.getLogger(__name__)

def generate_meal_plan_pdf(meal_plan_text, username):
    """Generate a PDF file containing the meal plan"""
    logger.info(f"Starting meal plan PDF generation for {username}")

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
        royal_blue = colors.HexColor('#4169E1')  # Royal blue for headers
        light_grey = colors.HexColor('#F5F5F5')  # Light grey for background

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=6,
            textColor=colors.white,
            backColor=colors.green,
            borderPadding=10,
            alignment=1
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=colors.grey,
            alignment=1
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            backColor=royal_blue,
            textColor=colors.white,
            borderPadding=6,
            alignment=0
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=8,
            bulletColor=colors.red
        )

        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.blue,
            alignment=1,
            fontName='Helvetica-Oblique'
        )

        # Content
        story = []

        # Title and subtitle
        story.append(Paragraph(f"Meal Plan for {username}", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Your Personalized Ramadan Nutrition Plan", subtitle_style))

        # Add meal icon at the top
        try:
            meal_icon_path = os.path.join('assets', 'meal icon.jpg')
            if os.path.exists(meal_icon_path):
                meal_img = Image(meal_icon_path, width=144, height=72)  # 2x1 inches
                story.append(meal_img)
                story.append(Spacer(1, 12))
                logger.debug("Successfully added meal icon")
            else:
                logger.warning(f"Meal icon not found at {meal_icon_path}")
        except Exception as e:
            logger.warning(f"Error adding meal icon: {str(e)}")

        # Process meal plan text
        sections = meal_plan_text.split('\n\n')
        logger.debug(f"Found {len(sections)} sections in meal plan text")

        for section in sections:
            if not section.strip():
                continue

            try:
                # Clean up section text
                section = section.replace('**', '').strip()

                if "Total Macronutrients" in section:
                    story.append(Paragraph("Total Macronutrients", header_style))
                    story.append(Spacer(1, 12))

                    # Parse macros into table data
                    macro_data = [['Nutrient', 'Amount']]  # Header row
                    macro_lines = section.split('\n')[1:]  # Skip the header

                    if macro_lines:
                        for line in macro_lines:
                            if ':' in line:
                                nutrient, amount = line.split(':', 1)
                                macro_data.append([nutrient.strip(), amount.strip()])
                    else:
                        # Fallback data if parsing fails
                        macro_data.extend([
                            ['Protein', '150g'],
                            ['Carbs', '200g'],
                            ['Fats', '60g']
                        ])

                    logger.debug(f"Creating macronutrients table with {len(macro_data)} rows")
                    macro_table = Table(macro_data)
                    macro_table.setStyle(TableStyle([
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
                    story.append(macro_table)
                    story.append(Spacer(1, 20))

                elif "Meal" in section:
                    story.append(Paragraph("Meals", header_style))
                    story.append(Spacer(1, 12))

                    # Add plate icon before meals
                    try:
                        plate_icon_path = os.path.join('assets', 'plate icon.jpg')
                        if os.path.exists(plate_icon_path):
                            plate_img = Image(plate_icon_path, width=36, height=36)  # 0.5x0.5 inches
                            story.append(plate_img)
                            story.append(Spacer(1, 6))
                            logger.debug("Successfully added plate icon")
                    except Exception as e:
                        logger.warning(f"Error adding plate icon: {str(e)}")

                    # Add meal items with red bullets
                    for line in section.split('\n')[1:]:
                        if line.strip():
                            story.append(Paragraph(f"• {line.strip()}", body_style))

                else:
                    # Other sections (like micronutrients)
                    story.append(Paragraph(section.split('\n')[0], header_style))
                    story.append(Spacer(1, 12))
                    for line in section.split('\n')[1:]:
                        if line.strip():
                            story.append(Paragraph(f"• {line.strip()}", body_style))
                    story.append(Spacer(1, 12))

            except Exception as section_error:
                logger.error(f"Error processing section: {str(section_error)}")
                continue  # Skip problematic section but continue processing

        # Add footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Feel free to ask questions about your meal plan!", footer_style))

        # Build PDF
        doc.build(story)
        logger.info(f"PDF generation completed successfully for {username}")
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