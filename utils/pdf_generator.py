
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
        royal_blue = colors.HexColor('#4169E1')  # Royal blue for headers
        light_grey = colors.HexColor('#F5F5F5')  # Light grey for background

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=6,
            textColor=colors.black,
            alignment=0,
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=colors.grey,
            alignment=0
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

        # Default meals if none provided
        default_meals = {
            "Suhoor - 45 min before Fajr": {
                "items": "Oatmeal with Whey Protein and Almonds (1 cup oatmeal, 1 scoop whey protein, 1/4 cup almonds)",
                "macros": "Protein: 40g | Carbs: 60g | Fats: 15g | Calories: 540"
            },
            "Iftar - At Maghrib": {
                "items": "Grilled Chicken with Quinoa and Steamed Broccoli (6 oz chicken, 1 cup quinoa, 1 cup broccoli)",
                "macros": "Protein: 50g | Carbs: 45g | Fats: 10g | Calories: 500"
            },
            "Post-Taraweeh": {
                "items": "Greek Yogurt with Mixed Berries and Honey (1 cup Greek yogurt, 1/2 cup mixed berries, 1 tbsp honey)",
                "macros": "Protein: 20g | Carbs: 40g | Fats: 5g | Calories: 300"
            }
        }

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
                # Create a single line of text for macros instead of a table
                macro_text = " | ".join([f"{nutrient}: {amount}" for nutrient, amount in macro_data])
                story.append(Paragraph(macro_text, macro_style))
                story.append(Spacer(1, 12))
                story.append(table)
                story.append(Spacer(1, 20))

                # Add Meals header
                story.append(Paragraph("Meals", header_style))
                story.append(Spacer(1, 12))

                # Process meal sections or use defaults
                found_meals = False
                for section_part in sections:
                    if any(meal_type in section_part.upper() for meal_type in ["SUHOOR", "IFTAR", "POST-TARAWEEH"]):
                        found_meals = True
                        meal_lines = section_part.split('\n')
                        meal_name = meal_lines[0].strip().replace('###', '').replace('**', '')
                        
                        story.append(Paragraph(meal_name, header_style))
                        
                        if len(meal_lines) > 1:
                            items = meal_lines[1].strip()
                            macros = meal_lines[2].strip() if len(meal_lines) > 2 else ""
                            
                            story.append(Paragraph(items, body_style))
                            if macros:
                                story.append(Paragraph(macros, macro_style))
                        story.append(Spacer(1, 12))

                # If no meals found in the text, use defaults
                if not found_meals:
                    for meal_name, meal_data in default_meals.items():
                        story.append(Paragraph(meal_name, header_style))
                        story.append(Paragraph(meal_data["items"], body_style))
                        story.append(Paragraph(meal_data["macros"], macro_style))
                        story.append(Spacer(1, 12))

        # Add some space before footer
        story.append(Spacer(1, 30))
        
        # Footer with italic style
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
