# backend/src/services/ingestion/rtf_processor.py
import argparse
import logging
from pathlib import Path
import sys

from striprtf.striprtf import rtf_to_text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_rtf_directory(input_dir: Path, output_dir: Path):
    """
    Processes RTF files in an input directory, converting them to plain text
    and saving the text to the output directory.

    Args:
        input_dir: Path to the directory containing RTF files.
        output_dir: Path to the directory where extracted text files (.txt) will be saved.
    """
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory set to: {output_dir}")

    processed_count = 0
    skipped_count = 0
    error_count = 0

    # Use a case-insensitive glob pattern to find both .rtf and .RTF files
    rtf_files = list(input_dir.glob('*.[rR][tT][fF]'))
    logger.info(f"Found {len(rtf_files)} RTF files (case-insensitive) in {input_dir}.")

    for rtf_file in rtf_files:
        if not rtf_file.is_file(): # Should not happen with glob but good practice
            continue

        output_txt_path = output_dir / f"{rtf_file.stem}.txt"
        logger.info(f"Processing RTF file: {rtf_file.name}...")

        try:
            # Read the RTF file content
            # Try common encodings if default fails
            rtf_content = None
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings_to_try:
                try:
                    with open(rtf_file, 'r', encoding=encoding) as f:
                        rtf_content = f.read()
                    logger.debug(f"Successfully read {rtf_file.name} with encoding {encoding}")
                    break # Exit loop if successful
                except UnicodeDecodeError:
                    logger.debug(f"Failed to decode {rtf_file.name} with {encoding}")
                    continue
                except Exception as read_err:
                     logger.error(f"Error reading {rtf_file.name} even before decoding: {read_err}")
                     raise # Re-raise unexpected reading errors

            if rtf_content is None:
                logger.error(f"Could not decode {rtf_file.name} with any attempted encoding. Skipping.")
                error_count += 1
                continue

            if not rtf_content:
                logger.warning(f"Skipping empty RTF file: {rtf_file.name}")
                skipped_count += 1
                continue

            # Convert RTF to plain text
            plain_text = rtf_to_text(rtf_content, errors="ignore") # Ignore encoding errors within RTF structure

            if plain_text:
                with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(plain_text.strip())
                logger.info(f"Converted {rtf_file.name} to {output_txt_path.name}")
                processed_count += 1
            else:
                logger.warning(f"Conversion resulted in empty text for {rtf_file.name}. Skipping output.")
                skipped_count += 1

        except Exception as e:
            logger.error(f"Error processing RTF file {rtf_file.name}: {e}", exc_info=True)
            error_count += 1

    logger.info(f"Finished processing Rich Text directory.")
    logger.info(f"  Successfully converted: {processed_count} RTF files")
    logger.info(f"  Skipped (empty or conversion yielded no text): {skipped_count}")
    logger.info(f"  Errors: {error_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process RTF files in a directory, converting them to plain text.")
    parser.add_argument("input_dir", help="Path to the input directory containing RTF files.")
    parser.add_argument("output_dir", help="Path to the output directory for extracted text files (.txt).")

    args = parser.parse_args()

    input_path = Path(args.input_dir).resolve()
    output_path = Path(args.output_dir).resolve()

    process_rtf_directory(input_path, output_path)
