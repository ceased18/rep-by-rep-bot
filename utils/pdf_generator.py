
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
            spaceAfter=8,
            leftIndent=20
        )
        macro_style = ParagraphStyle(
            'CustomMacro',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=12,
            leftIndent=20,
            alignment=0
        )
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Italic'],
            fontSize=12,
            textColor=colors.blue,
            alignment=1
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
        for section in sections:
            if not section.strip():
                continue
                
            # Clean up section text
            section = section.replace('###', '').replace('**', '')
            
            if "Total Daily Macronutrients" in section:
                story.append(Paragraph("Total Daily Macronutrients", header_style))
                story.append(Spacer(1, 12))
                
                # Parse macros into table data
                rows = [['Nutrient', 'Amount']]
                for line in section.split('\n')[1:]:
                    if ':' in line:
                        nutrient, amount = line.split(':', 1)
                        rows.append([nutrient.strip(), amount.strip()])
                
                # Create table
                table = Table(rows, colWidths=[200, 200])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), darker_blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('TOPPADDING', (0, 1), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
            
            elif "MEAL" in section.upper() or "IFTAR" in section.upper() or "SUHOOR" in section.upper():
                story.append(Paragraph("Meals", header_style))
                story.append(Spacer(1, 12))
                
                lines = section.split('\n')
                for line in lines:
                    if line.strip():
                        if ":" in line:
                            meal_name, details = line.split(":", 1)
                            story.append(Paragraph(meal_name.strip().upper(), header_style))
                            story.append(Paragraph(details.strip(), body_style))
                            
                            # Add macros if they exist
                            if "|" in details:
                                macros = details.split("|")[1].strip()
                                story.append(Paragraph(macros, macro_style))
                        else:
                            story.append(Paragraph(line.strip(), body_style))
                story.append(Spacer(1, 12))
            
            elif "Micronutrients" in section:
                story.append(Paragraph("Total Micronutrients", header_style))
                story.append(Spacer(1, 12))
                for line in section.split('\n')[1:]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), body_style))
                story.append(Spacer(1, 12))
            
            elif "Tips" in section:
                story.append(Paragraph("Tips for Success", header_style))
                story.append(Spacer(1, 12))
                for line in section.split('\n')[1:]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), body_style))
                story.append(Spacer(1, 20))

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
