import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def tsv_to_markdown_table(header: List[str], rows: List[Dict[str, Any]]) -> str:
    """Converts a list of dictionaries (rows) and a header into a Markdown table."""
    if not header:
        return "_Header row is missing or empty._\n"
    if not rows:
        return "_No data rows found._\n"

    # Ensure header doesn't contain empty strings which break markdown tables
    sanitized_header = [h if h else "EMPTY_HEADER" for h in header]

    md_string = "| " + " | ".join(sanitized_header) + " |\n"
    md_string += "|-" + "-|".join(['-' * len(col) for col in sanitized_header]) + "-|\n"
    for row_dict in rows:
        # Ensure all values are strings and handle None or empty values gracefully
        row_values = [str(row_dict.get(h, '')).replace('|', '\\|').replace('\n', ' ').replace('\r', '') for h in header]
        md_string += "| " + " | ".join(row_values) + " |\n"
    return md_string

def parse_ehi_tsv_to_markdown(tsv_file_path: Path) -> str:
    """
    Parses a single Epic EHI TSV file and converts its content to Markdown format.

    Args:
        tsv_file_path: The absolute path to the TSV file.

    Returns:
        A string containing the Markdown representation of the TSV data.

    Raises:
        FileNotFoundError: If the tsv_file_path does not exist.
        Exception: For errors during CSV parsing or other issues.
    """
    if not tsv_file_path.is_file():
        raise FileNotFoundError(f"File not found: {tsv_file_path}")

    table_name = tsv_file_path.stem
    markdown_output = f"# {table_name.replace('_', ' ').title()} Data\n\n"

    try:
        rows: List[Dict[str, Any]] = []
        header: List[str] = []
        # Attempt common encodings if utf-8 fails
        encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        file_parsed = False
        last_exception = None

        for encoding in encodings_to_try:
            try:
                with open(tsv_file_path, mode='r', newline='', encoding=encoding) as tsvfile:
                    # Use csv.DictReader to handle rows as dictionaries
                    # Increase field size limit for potentially large fields in notes etc.
                    # csv.field_size_limit(2147483647) # Max possible limit - use with caution
                    csv.field_size_limit(500 * 1024 * 1024) # 500MB limit - adjust if needed

                    reader = csv.DictReader(tsvfile, delimiter='\t')
                    header = reader.fieldnames if reader.fieldnames else []
                    rows = list(reader) # Read all rows into memory
                file_parsed = True
                logging.info(f"Successfully parsed {tsv_file_path.name} with encoding {encoding}.")
                break # Exit loop if parsing is successful
            except UnicodeDecodeError as e:
                last_exception = e
                logging.warning(f"Encoding {encoding} failed for {tsv_file_path.name}: {e}. Trying next encoding.")
                continue # Try the next encoding
            except csv.Error as e:
                 # Check if the error is due to field size limit
                if "field larger than field limit" in str(e):
                    logging.error(f"CSV field size limit exceeded for {tsv_file_path.name} with encoding {encoding}. Consider increasing csv.field_size_limit(). Skipping file.")
                    return markdown_output + f"_Error: CSV field size limit exceeded. Could not parse file._\n" # Return partial output with error
                else:
                    last_exception = e
                    logging.error(f"CSV Error parsing {tsv_file_path.name} with encoding {encoding}: {e}")
                    # Don't break here, maybe another encoding works or it's just a warning
            except Exception as e:
                last_exception = e
                logging.error(f"Unexpected error reading {tsv_file_path.name} with encoding {encoding}: {e}")
                # Depending on the error, might want to try next encoding or raise


        if not file_parsed:
             # If all encodings failed, raise the last exception encountered
             if last_exception:
                 raise Exception(f"Failed to parse {tsv_file_path.name} with all tried encodings. Last error: {last_exception}") from last_exception
             else:
                 raise Exception(f"Failed to parse {tsv_file_path.name}. Unknown error.")


        markdown_output += tsv_to_markdown_table(header, rows)
        return markdown_output

    except Exception as e:
        # Catch other potential errors
        logging.error(f"An unexpected error occurred while processing {tsv_file_path}: {e}", exc_info=True)
        # Return partial markdown with error message
        return markdown_output + f"\n_Error processing this file: {e}_"


def process_ehi_directory(input_dir: Path, output_dir: Path):
    """
    Processes all TSV files in an input directory and saves them as Markdown
    in the output directory.

    Args:
        input_dir: Path to the directory containing EHI TSV files.
        output_dir: Path to the directory where Markdown files will be saved.
    """
    if not input_dir.is_dir():
        logging.error(f"Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory set to: {output_dir}")

    tsv_files = list(input_dir.glob('*.tsv'))
    logging.info(f"Found {len(tsv_files)} TSV files in {input_dir}.")

    processed_count = 0
    error_count = 0

    for tsv_file in tsv_files:
        logging.info(f"Processing file: {tsv_file.name}...")
        output_md_path = output_dir / f"{tsv_file.stem}.md"
        try:
            markdown_content = parse_ehi_tsv_to_markdown(tsv_file)
            with open(output_md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(markdown_content)
            logging.info(f"Successfully converted {tsv_file.name} to {output_md_path.name}")
            processed_count += 1
        except FileNotFoundError as e:
            logging.error(f"Skipping - File not found: {tsv_file} - {e}")
            error_count += 1
        except Exception as e:
            logging.error(f"Failed to convert {tsv_file.name}: {e}", exc_info=False) # Set exc_info=True for full traceback
            error_count += 1
            # Optionally write error status to the output file
            try:
                 with open(output_md_path, 'w', encoding='utf-8') as md_file:
                     md_file.write(f"# {tsv_file.stem.replace('_', ' ').title()} Data\n\n")
                     md_file.write(f"_Failed to process this file. Error: {e}_")
            except Exception as write_err:
                 logging.error(f"Could not write error status to {output_md_path.name}: {write_err}")


    logging.info(f"Finished processing. Successfully converted: {processed_count}, Errors: {error_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert all Epic EHI TSV files in a directory to Markdown.")
    parser.add_argument("input_dir", help="Path to the input directory containing TSV files.")
    parser.add_argument("output_dir", help="Path to the output directory for Markdown files.")

    args = parser.parse_args()

    input_path = Path(args.input_dir).resolve()
    output_path = Path(args.output_dir).resolve()

    process_ehi_directory(input_path, output_path)
