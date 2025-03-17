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
    logger.debug("Parsing meal plan text sections...")

    try:
        # Create temporary file
        pdf_name = f"Meal Plan for {username}.pdf"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{pdf_name}')
        pdf_path = temp_file.name
        temp_file.close()
        logger.debug(f"Created temporary file: {pdf_path}")

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

        # Header style - royal blue background
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

        # Meal totals style - slightly emphasized
        totals_style = ParagraphStyle(
            'MealTotals',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
            alignment=0,  # Left alignment
            textColor=colors.HexColor('#4169E1'),  # Royal Blue
            fontName='Helvetica-Bold'
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
        story.append(Paragraph(f"Meal Plan for {username}", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Based on your personal preferences and goals", subtitle_style))
        story.append(Spacer(1, 20))

        # Process meal plan text
        sections = meal_plan_text.split('\n\n')
        total_daily_calories = 0
        total_daily_protein = 0
        total_daily_carbs = 0
        total_daily_fats = 0
        target_calories = 0
        target_protein = 0
        target_carbs = 0
        target_fats = 0

        # Track if meal header was added
        current_meal_header = None

        for section in sections:
            if not section.strip():
                continue

            # Clean up section text
            section = section.replace('**', '').strip()
            lines = section.split('\n')

            if not lines:
                continue

            # Parse target macros from Total Daily Macronutrients section
            if "Total Daily Macronutrients" in lines[0]:
                story.append(Paragraph("Daily Targets", header_style))
                table_data = []
                for line in lines[1:]:
                    if ':' in line:
                        nutrient, amount = line.split(':', 1)
                        table_data.append([nutrient.strip(), amount.strip()])
                        # Extract target values
                        if 'calories' in nutrient.lower():
                            try:
                                target_calories = float(amount.split()[0])
                            except:
                                pass
                        elif 'protein' in nutrient.lower():
                            try:
                                target_protein = float(amount.split()[0])
                            except:
                                pass
                        elif 'carbs' in nutrient.lower():
                            try:
                                target_carbs = float(amount.split()[0])
                            except:
                                pass
                        elif 'fats' in nutrient.lower():
                            try:
                                target_fats = float(amount.split()[0])
                            except:
                                pass

                if table_data:
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
                story.append(Spacer(1, 20))
                continue

            # Check if this is a meal section header
            meal_keywords = ["Meal", "Breakfast", "Lunch", "Dinner", "Snack", "Pre-workout", "Post-workout", "Suhoor", "Iftar", "Post-Taraweeh"]
            is_meal_header = any(keyword in lines[0] for keyword in meal_keywords)

            if is_meal_header:
                # Add meal header
                current_meal_header = lines[0].strip()
                story.append(Paragraph(current_meal_header, header_style))

                # Process meal items
                meal_protein = 0.0
                meal_carbs = 0.0
                meal_fats = 0.0
                meal_calories = 0.0

                for line in lines[1:]:
                    if line.strip() and not line.startswith("Meal Totals:"):
                        # Format food items with macros
                        content = line.strip('- ').strip()
                        if '(' in content:
                            food_part = content.split('(')[0].strip()
                            macros_part = content[content.find('('):]
                            # Extract macro values for totals
                            try:
                                if 'Protein:' in macros_part:
                                    protein = float(macros_part.split('Protein:')[1].split('g')[0].strip())
                                    meal_protein += protein
                                if 'Carbs:' in macros_part:
                                    carbs = float(macros_part.split('Carbs:')[1].split('g')[0].strip())
                                    meal_carbs += carbs
                                if 'Fats:' in macros_part:
                                    fats = float(macros_part.split('Fats:')[1].split('g')[0].strip())
                                    meal_fats += fats
                                if 'Calories:' in macros_part:
                                    calories = float(macros_part.split('Calories:')[1].split(')')[0].strip())
                                    meal_calories += calories
                            except Exception as e:
                                logger.warning(f"Could not parse macros from line: {content}")
                            story.append(Paragraph(f"• {food_part} {macros_part}", text_style))
                        else:
                            story.append(Paragraph(f"• {content}", text_style))

                # Add meal totals if we have values
                if meal_protein > 0 or meal_carbs > 0 or meal_fats > 0 or meal_calories > 0:
                    story.append(Spacer(1, 8))
                    meal_totals = (f"Meal Totals: Protein: {meal_protein:.1f}g, "
                                   f"Carbs: {meal_carbs:.1f}g, "
                                   f"Fats: {meal_fats:.1f}g, "
                                   f"Calories: {meal_calories:.0f}")
                    story.append(Paragraph(meal_totals, totals_style))
                    story.append(Spacer(1, 12))

                    # Add to daily totals
                    total_daily_protein += meal_protein
                    total_daily_carbs += meal_carbs
                    total_daily_fats += meal_fats
                    total_daily_calories += meal_calories

            elif "Total Micronutrients" in lines[0]:
                # Add Energy Summary section first
                story.append(Paragraph("Energy Summary", header_style))

                # Calculate percentages of targets
                calorie_percent = int((total_daily_calories / target_calories * 100) if target_calories > 0 else 0)
                protein_percent = int((total_daily_protein / target_protein * 100) if target_protein > 0 else 0)
                carbs_percent = int((total_daily_carbs / target_carbs * 100) if target_carbs > 0 else 0)
                fats_percent = int((total_daily_fats / target_fats * 100) if target_fats > 0 else 0)

                # Format energy summary table
                energy_data = [
                    ["Nutrient", "Consumed", "Target", "Percent"],
                    ["Calories", f"{total_daily_calories:.0f} kcal", f"{target_calories:.0f} kcal", f"{calorie_percent}%"],
                    ["Protein", f"{total_daily_protein:.1f}g", f"{target_protein:.1f}g", f"{protein_percent}%"],
                    ["Net Carbs", f"{total_daily_carbs:.1f}g", f"{target_carbs:.1f}g", f"{carbs_percent}%"],
                    ["Fat", f"{total_daily_fats:.1f}g", f"{target_fats:.1f}g", f"{fats_percent}%"]
                ]

                # Create and style the energy summary table
                energy_table = Table(energy_data, colWidths=[doc.width/4]*4)
                energy_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row bold
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4169E1')),  # Header row blue
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text white
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                story.append(energy_table)
                story.append(Spacer(1, 20))

                # Add Highlighted Nutrients section
                story.append(Paragraph("Highlighted Nutrients", header_style))

                # Create dictionary of micronutrients from the text
                micronutrients = {}
                for line in lines[1:]:
                    if ':' in line:
                        nutrient, amount = line.split(':', 1)
                        micronutrients[nutrient.strip()] = amount.strip()

                # Define key nutrients and their units
                key_nutrients = {
                    'Iron': 'mg',
                    'Calcium': 'mg',
                    'Vitamin A': 'IU',
                    'Vitamin C': 'mg',
                    'Vitamin B12': 'mcg',
                    'Folate': 'mcg',
                    'Potassium': 'mg'
                }

                # Create micronutrient table data
                micro_data = [["Nutrient", "Amount"]]
                for nutrient, unit in key_nutrients.items():
                    if nutrient in micronutrients:
                        try:
                            amount = micronutrients[nutrient].split()[0]
                            micro_data.append([f"{nutrient}", f"{amount} {unit}"])
                        except:
                            micro_data.append([f"{nutrient}", "Data not available"])
                    else:
                        micro_data.append([f"{nutrient}", "Data not available"])

                # Create and style the micronutrients table
                micro_table = Table(micro_data, colWidths=[doc.width/2]*2)
                micro_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4169E1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                story.append(micro_table)
            else:
                # Add other sections with regular formatting
                if not any(keyword in lines[0] for keyword in meal_keywords):
                    story.append(Paragraph(lines[0], header_style))
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
        logger.debug("Generated PDF with following sections:")
        logger.debug("- Meal sections with blue headers")
        logger.debug("- Food items with formatted macros")
        logger.debug("- Energy Summary table")
        logger.debug("- Highlighted Nutrients section")
        return pdf_path

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                logger.debug("Cleaned up temporary PDF file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")
        raise