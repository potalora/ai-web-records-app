# backend/src/services/ingestion_orchestrator.py

import logging
from pathlib import Path

# TODO: Update imports once file structure is confirmed
from .ingestion.epic_ehi_parser import process_ehi_directory
from .ingestion.media_processor import process_media_directory
from .ingestion.rtf_processor import process_rtf_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def orchestrate_ingestion(root_input_dir: Path, root_output_dir: Path):
    """Orchestrates the ingestion process for various EHR data types."""

    logging.info(f"Starting ingestion orchestration for: {root_input_dir}")
    logging.info(f"Output will be saved to: {root_output_dir}")

    # Define specific subdirectories based on typical structure
    ehi_tables_input_dir = root_input_dir / "EHITables"
    media_input_dir = root_input_dir / "Media"
    rich_text_input_dir = root_input_dir / "Rich Text"

    # Define output subdirectories
    ehi_tables_output_dir = root_output_dir / "EHITables_Markdown"
    media_output_dir = root_output_dir / "Media_Text"
    rich_text_output_dir = root_output_dir / "RichText_Text"

    # Create output directories if they don't exist
    ehi_tables_output_dir.mkdir(parents=True, exist_ok=True)
    media_output_dir.mkdir(parents=True, exist_ok=True)
    rich_text_output_dir.mkdir(parents=True, exist_ok=True)

    # --- Process EHI Tables (TSV to Markdown) ---
    if ehi_tables_input_dir.is_dir():
        logging.info(f"Processing EHI Tables from: {ehi_tables_input_dir}")
        try:
            process_ehi_directory(ehi_tables_input_dir, ehi_tables_output_dir)
            logging.info(f"Finished processing EHI Tables. Output in: {ehi_tables_output_dir}")
        except Exception as e:
            logging.error(f"Error processing EHI Tables: {e}", exc_info=True)
    else:
        logging.warning(f"EHI Tables directory not found: {ehi_tables_input_dir}")

    # --- Process Media Files (PDF/TIF) ---
    if media_input_dir.is_dir():
        logging.info(f"Processing Media files from: {media_input_dir}")
        try:
            # Note: process_media_directory handles its own output subdirs ('pdf_text', 'tif_analysis')
            process_media_directory(media_input_dir, media_output_dir) 
            logging.info(f"Finished processing Media files. Output in: {media_output_dir}")
        except Exception as e:
            logging.error(f"Error processing Media files: {e}", exc_info=True)
    else:
        logging.warning(f"Media directory not found: {media_input_dir}")

    # --- Process Rich Text Files (RTF) ---
    if rich_text_input_dir.is_dir():
        logging.info(f"Processing Rich Text files from: {rich_text_input_dir}")
        try:
            process_rtf_directory(rich_text_input_dir, rich_text_output_dir)
            logging.info(f"Finished processing Rich Text files. Output in: {rich_text_output_dir}")
        except Exception as e:
            logging.error(f"Error processing Rich Text files: {e}", exc_info=True)
    else:
        logging.warning(f"Rich Text directory not found: {rich_text_input_dir}")

    logging.info("Ingestion orchestration finished.")


if __name__ == "__main__":
    # Example usage: Replace with your actual paths
    # Ensure the paths point to the parent directory containing 'EHITables', 'Media', 'Rich Text'
    # e.g., /Users/potalora/Downloads/Requested Record/
    default_input_root = Path("/Users/potalora/Downloads/Requested Record/") 
    # Output will be organized within this directory
    default_output_root = Path("/Users/potalora/ai_workspace/ai_web_records_app/processed_data/") 

    import argparse
    parser = argparse.ArgumentParser(description="Orchestrate EHR data ingestion.")
    parser.add_argument("--input_dir", type=Path, default=default_input_root,
                        help="Root directory containing EHR subfolders (EHITables, Media, Rich Text).")
    parser.add_argument("--output_dir", type=Path, default=default_output_root,
                        help="Root directory where processed data will be saved.")

    args = parser.parse_args()

    orchestrate_ingestion(args.input_dir, args.output_dir)
