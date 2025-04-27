# /backend/services/pdf_utils.py
import io
import base64
import logging
from typing import List, Tuple, Optional

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

# Heuristic: Consider PDF image-based if average characters per page is low
# Increased from 100 to 500 based on testing with scanned documents.
TEXT_EXTRACTION_THRESHOLD_PER_PAGE = 500


def analyze_pdf_content(pdf_content: bytes) -> Tuple[str, Optional[str]]:
    """Analyzes PDF content to extract text and determine if it's image-based.

    Args:
        pdf_content: The byte content of the PDF file.

    Returns:
        A tuple containing:
        - pdf_type: 'text' or 'image'.
        - extracted_text: The extracted text if pdf_type is 'text', otherwise None.
    """
    extracted_text = ""
    pdf_type = "image"  # Default to image
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)
        if num_pages == 0:
            logger.warning("PDF has 0 pages.")
            return "image", None  # Treat as image if no pages

        total_chars = 0
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n"  # Add separator
                    total_chars += len(page_text)
            except Exception as page_error:
                logger.warning(f"Error extracting text from a page: {page_error}")
                continue  # Try next page

        avg_chars_per_page = total_chars / num_pages if num_pages > 0 else 0
        logger.info(
            f"PDF Analysis: {num_pages} pages, {total_chars} total chars, "
            f"{avg_chars_per_page:.2f} avg chars/page."
        )

        if avg_chars_per_page >= TEXT_EXTRACTION_THRESHOLD_PER_PAGE:
            pdf_type = "text"
            logger.info("Classified PDF as text-based.")
            return pdf_type, extracted_text.strip()
        else:
            logger.info("Classified PDF as image-based (low text content).")
            return "image", None

    except PdfReadError as e:
        logger.error(f"PyPDF2 error reading PDF: {e}")
        # Could be encrypted, corrupted, or truly image-based
        return "image", None
    except Exception as e:
        logger.error(f"Unexpected error analyzing PDF content: {e}", exc_info=True)
        return "image", None  # Fallback to image if analysis fails


def convert_pdf_to_images(pdf_content: bytes) -> List[str]:
    """Converts PDF pages to a list of base64 encoded PNG images."""
    base64_images = []
    try:
        # Convert PDF bytes to PIL Image objects at 300 DPI
        images = convert_from_bytes(pdf_content, fmt="png", dpi=300)

        for i, image in enumerate(images):
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_images.append(img_str)
            logger.debug(f"Converted page {i + 1} to base64 PNG.")

        if not base64_images:
            logger.warning("pdf2image conversion resulted in 0 images.")

    except Exception as e:
        logger.error(
            f"Error converting PDF to images using pdf2image: {e}", exc_info=True
        )
        # Return empty list on failure, downstream needs to handle this

    return base64_images
