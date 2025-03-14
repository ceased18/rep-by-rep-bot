
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
        subtitle_grey = colors.HexColor('#F0F0F0')  # Light grey for subtitle background

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
            fontSize=16,
            spaceAfter=20,
            backColor=subtitle_grey,
            borderPadding=10,
            alignment=1
        )
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            backColor=darker_blue,
            textColor=colors.white,
            borderPadding=5
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=8
        )
        macro_style = ParagraphStyle(
            'CustomMacro',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=12,
            textColor=colors.HexColor('#666666')
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
        
        # Title
        story.append(Paragraph(f"Meal Plan for {username}", title_style))
        story.append(Spacer(1, 12))
        
        # Subtitle
        story.append(Paragraph("Personalized Nutrition Plan for Ramadan", subtitle_style))
        story.append(Spacer(1, 12))

        # Process meal plan text
        sections = meal_plan_text.split('\n\n')
        
        # Default macros if none provided
        default_macros = [
            ['Protein', '150g'],
            ['Carbs', '200g'],
            ['Fats', '60g'],
            ['Calories', '2000']
        ]

        for section in sections:
            if not section.strip():
                continue
            
            # Clean up section text
            section = section.replace('###', '').replace('**', '')
            
            if "Total Daily Macronutrients" in section:
                story.append(Paragraph("Total Daily Macronutrients", header_style))
                story.append(Spacer(1, 12))
                
                # Parse macros or use defaults
                macro_data = []
                macro_lines = section.split('\n')[1:]
                if len(macro_lines) > 1:
                    for line in macro_lines:
                        if ':' in line:
                            nutrient, amount = line.split(':', 1)
                            macro_data.append([nutrient.strip(), amount.strip()])
                
                if not macro_data:
                    macro_data = default_macros

                # Create table
                table = Table(
                    [['Nutrient', 'Amount']] + macro_data,
                    colWidths=[200, 200]
                )
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), darker_blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('TOPPADDING', (0, 1), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
            
            elif any(meal_type in section.upper() for meal_type in ["MEAL", "IFTAR", "SUHOOR"]):
                # Default meal data if none provided
                default_meals = {
                    "SUHOOR": "Oatmeal (1 cup), Eggs (2 whole), Banana (1 medium)\nProtein: 20g | Carbs: 45g | Fats: 12g | Calories: 380",
                    "IFTAR": "Chicken breast (4 oz), Brown rice (1 cup), Mixed veggies (1 cup)\nProtein: 35g | Carbs: 45g | Fats: 8g | Calories: 420",
                    "POST-TARAWEEH": "Greek yogurt (1 cup), Mixed nuts (1 oz), Honey (1 tbsp)\nProtein: 18g | Carbs: 25g | Fats: 15g | Calories: 320"
                }

                meal_lines = section.split('\n')
                for line in meal_lines:
                    if ':' in line:
                        meal_name = line.split(':')[0].strip().upper()
                        story.append(Paragraph(meal_name, header_style))
                        
                        meal_content = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                        if not meal_content and meal_name in default_meals:
                            meal_content = default_meals[meal_name]
                        
                        # Split content and macros
                        if '|' in meal_content:
                            content, macros = meal_content.split('|', 1)
                            story.append(Paragraph(content.strip(), body_style))
                            story.append(Paragraph(macros.strip(), macro_style))
                        else:
                            story.append(Paragraph(meal_content, body_style))
                        story.append(Spacer(1, 12))

        # Footer
        story.append(Paragraph("Feel free to ask questions about your meal plan!", footer_style))

        # Build PDF
        doc.build(story)
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
