from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def generate_meal_plan_pdf(meal_plan_text):
    """Generate a PDF file containing the meal plan"""
    logger.info("Starting meal plan PDF generation")

    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
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
            spaceAfter=30
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            leading=14,
            spaceAfter=12
        )

        # Content
        content = []
        try:
            # Add title
            content.append(Paragraph("Your Personalized Meal Plan", title_style))
            content.append(Spacer(1, 12))

            # Try to add images if they exist
            try:
                food_image_path = os.path.join('assets', 'meal icon.jpg')
                plate_icon_path = os.path.join('assets', 'plate icon.jpg')

                if os.path.exists(food_image_path):
                    food_img = Image(food_image_path, width=400, height=200)
                    content.append(food_img)
                    content.append(Spacer(1, 12))
                else:
                    logger.warning(f"Food image not found at {food_image_path}")

                if os.path.exists(plate_icon_path):
                    plate_img = Image(plate_icon_path, width=50, height=50)
                    content.append(plate_img)
                    content.append(Spacer(1, 12))
                else:
                    logger.warning(f"Plate icon not found at {plate_icon_path}")

            except Exception as img_error:
                logger.warning(f"Error adding images to PDF: {str(img_error)}")
                # Continue without images

            # Split the meal plan text into paragraphs
            paragraphs = meal_plan_text.split('\n')
            for para in paragraphs:
                if para.strip():
                    content.append(Paragraph(para, body_style))
                    content.append(Spacer(1, 12))

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