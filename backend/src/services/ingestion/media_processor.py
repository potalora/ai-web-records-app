# backend/src/services/ingestion/media_processor.py
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ..pdf_utils import analyze_pdf_content

def process_media_directory(input_dir: Path, output_dir: Path):
    """
    Processes PDF files in an input directory, extracting text from text-based PDFs
    and saving it to the output directory. Logs image-based PDFs and TIFs for later processing.

    Args:
        input_dir: Path to the directory containing media files (PDF, TIF, etc.).
        output_dir: Path to the directory where extracted text files (.txt) will be saved.
    """
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory set to: {output_dir}")

    processed_text_count = 0
    image_pdf_count = 0
    tif_count = 0
    other_files_count = 0
    error_count = 0

    media_files = list(input_dir.iterdir())
    logger.info(f"Found {len(media_files)} items in {input_dir}.")

    for media_file in media_files:
        if not media_file.is_file():
            logger.debug(f"Skipping directory: {media_file.name}")
            continue

        file_extension = media_file.suffix.lower()
        output_txt_path = output_dir / f"{media_file.stem}.txt"

        if file_extension == '.pdf':
            logger.info(f"Processing PDF file: {media_file.name}...")
            try:
                with open(media_file, 'rb') as f:
                    pdf_content = f.read()

                if not pdf_content:
                    logger.warning(f"Skipping empty PDF file: {media_file.name}")
                    error_count += 1
                    continue

                pdf_type, extracted_text = analyze_pdf_content(pdf_content)

                if pdf_type == 'text' and extracted_text:
                    with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(extracted_text)
                    logger.info(f"Extracted text from {media_file.name} to {output_txt_path.name}")
                    processed_text_count += 1
                elif pdf_type == 'image':
                    logger.info(f"PDF {media_file.name} classified as image-based. Needs OCR/Image processing.")
                    image_pdf_count += 1
                else: # Handle cases where text extraction might fail or return empty
                    logger.warning(f"Could not extract sufficient text from {media_file.name} (classified as {pdf_type}). Might need image processing.")
                    error_count += 1 # Count as error/unprocessed for now

            except Exception as e:
                logger.error(f"Error processing PDF {media_file.name}: {e}", exc_info=True)
                error_count += 1

        elif file_extension == '.tif' or file_extension == '.tiff':
            logger.info(f"TIF file found: {media_file.name}. Needs OCR processing.")
            tif_count += 1
            # Placeholder for TIF processing logic (e.g., using Pillow + pytesseract)

        else:
            # Handle other file types (like _INDEX.HTML) - just log and skip
            logger.debug(f"Skipping non-PDF/TIF file: {media_file.name}")
            other_files_count += 1

    logger.info(f"Finished processing Media directory.")
    logger.info(f"  Successfully extracted text from: {processed_text_count} PDFs")
    logger.info(f"  Image-based PDFs (need OCR/Vision): {image_pdf_count}")
    logger.info(f"  TIF files (need OCR): {tif_count}")
    logger.info(f"  Other skipped files: {other_files_count}")
    logger.info(f"  Errors/Skipped PDFs: {error_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process media files (PDFs) in a directory, extracting text.")
    parser.add_argument("input_dir", help="Path to the input directory containing media files.")
    parser.add_argument("output_dir", help="Path to the output directory for extracted text files (.txt).")

    args = parser.parse_args()

    input_path = Path(args.input_dir).resolve()
    output_path = Path(args.output_dir).resolve()

    process_media_directory(input_path, output_path)
