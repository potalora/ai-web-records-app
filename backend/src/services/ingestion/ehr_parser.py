# backend/utils/ehr_parser.py
import argparse
import csv
import logging
import sys
import json 
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Optional
import concurrent.futures # Added import
import functools # Added import

# Configure logging
# Set level to INFO for less verbose output during normal runs
# Change to DEBUG if needed for detailed tracing
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define logger at the global scope
logger = logging.getLogger(__name__)

def detect_encoding(file_path: Path, encodings_to_try: List[str]) -> Optional[str]:
    """Attempts to detect the encoding of a file by trying a list of common encodings."""
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()  # Try reading the file content
            # Use debug level for successful detection unless debugging
            logger.debug(f"Successfully detected encoding '{enc}' for {file_path.name}")
            return enc
        except UnicodeDecodeError:
            logger.debug(f"Encoding '{enc}' failed for {file_path.name}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error while trying encoding '{enc}' for {file_path.name}: {e}")
            continue
    return None

def read_tsv_content(file_path: Path, encoding: str) -> str:
    """Reads the content of a TSV file with the specified encoding."""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path.name} with encoding {encoding}: {e}")
        raise # Re-raise exception to be handled in the main loop

def tsv_to_markdown(tsv_content: str, filename: str, schema_data: Optional[Dict[str, Any]] = None) -> str:
    """Converts TSV content string to a Markdown formatted table string.

    Args:
        tsv_content: The string content of the TSV file.
        filename: The original filename (used for table name extraction).
        schema_data: Optional dictionary containing schema info for the table.

    Returns:
        A string containing the Markdown representation, or empty string if file skipped.
    """
    lines = tsv_content.strip().split('\n')
    if not lines:
        logger.warning(f"Skipping empty file: {filename}")
        return ""

    # Use StringIO to handle the string content as a file-like object for csv.reader
    f = StringIO(tsv_content)
    reader = csv.reader(f, delimiter='\t', quotechar='"')
    try:
        header = next(reader)
        # Convert reader iterator to list to check if data rows exist
        data_rows = list(reader)
        if not data_rows:
             logger.warning(f"File {filename} has header but no data rows. Skipping content generation.")
             return f"# {filename}\n\n_(Header only, no data rows found in TSV)_" # Indicate header-only

    except StopIteration:
         logger.warning(f"File {filename} seems to be empty (no header found). Skipping.")
         return "" # Handle files with no header
    except Exception as e:
        logger.error(f"Error parsing CSV data in {filename}: {e}", exc_info=True)
        # Return an error message within the Markdown structure
        return f"# {filename}\n\nError parsing TSV content: {e}"


    table_name = Path(filename).stem
    # --- Debug schema lookup ---
    logger.debug(f"--- DEBUG [tsv_to_markdown]: Processing filename: {filename}, Extracted table_name: {table_name}")
    if schema_data:
        logger.debug(f"--- DEBUG [tsv_to_markdown]: Schema data is available (Keys: {len(schema_data)}). Attempting lookup for '{table_name}'...")
        schema_info = schema_data.get(table_name)
        if schema_info:
            logger.debug(f"--- DEBUG [tsv_to_markdown]: Schema info FOUND for '{table_name}'. Description: {schema_info.get('description', 'N/A')[:50]}...")
        else:
            logger.debug(f"--- DEBUG [tsv_to_markdown]: Schema info NOT FOUND for key '{table_name}'.")
            # Add a check for case variations or common prefixes/suffixes if needed
            # Example: check_variations(table_name, schema_data.keys())
    else:
        logger.debug("--- DEBUG [tsv_to_markdown]: Schema data is None.")
        schema_info = None
    # --- End Debug ---

    markdown_output = f"# {filename} (`{table_name}`)\n\n" # Add table name in backticks

    # Add Schema Info if available
    if schema_info:
        description = schema_info.get('description', 'N/A')
        # Ensure description is treated as a single paragraph in Markdown
        markdown_output += f"## Table Description\n\n{' '.join(description.split())}\n\n"
        pk = schema_info.get('primary_key')
        if pk:
            markdown_output += f"**Primary Key(s):** `{', '.join(pk)}`\n\n"

    # --- Generate Markdown Table ---
    markdown_output += "## Data\n\n" # Add a subheading for the data table
    # Create Markdown table header
    markdown_output += "| " + " | ".join(header) + " |\n"
    markdown_output += "|--" + "|--".join(['-'] * len(header)) + "|\n" # Simpler header separator

    # Create Markdown table rows
    for row in data_rows:
        # Ensure row has the same number of columns as header, padding if necessary
        if len(row) < len(header):
            row.extend([''] * (len(header) - len(row)))
        elif len(row) > len(header):
            logger.warning(f"Row in {filename} has more columns ({len(row)}) than header ({len(header)}). Truncating.")
            row = row[:len(header)] # Truncate if too long
        # Escape pipe characters within cells
        processed_row = [cell.strip().replace('|', '\\|') for cell in row]
        markdown_output += "| " + " | ".join(processed_row) + " |\n"

    # Add Column Definitions section
    if schema_info and 'columns' in schema_info:
        markdown_output += "\n## Column Definitions\n\n"
        markdown_output += "| Column Name | Type | Description |\n"
        markdown_output += "|---|---|---|\n"

        schema_columns_dict = {col['name']: col for col in schema_info['columns']}

        for col_name in header:
            col_schema = schema_columns_dict.get(col_name)
            if col_schema:
                col_type = col_schema.get('type', 'N/A')
                # Clean up description: remove excessive whitespace, escape pipes
                col_desc = ' '.join(col_schema.get('description', 'N/A').split()).replace('|', '\\|')
                markdown_output += f"| `{col_name}` | `{col_type}` | {col_desc} |\n"
            else:
                # It's expected some columns might not be in schema. Log only if debugging.
                logger.debug(f"No schema definition found for column '{col_name}' in table '{table_name}'.")
                markdown_output += f"| `{col_name}` | N/A | _No schema definition found_ |\n"

    return markdown_output


# --- ENSURE THIS FUNCTION IS DEFINED ---
def process_directory(input_dir: Path, output_dir: Path, schema_data: Optional[Dict[str, Any]] = None):
    """Processes all TSV files in the input directory and saves them as Markdown.

    Args:
        input_dir: Path to the input directory containing TSV files.
        output_dir: Path to the output directory for Markdown files.
        schema_data: Optional dictionary containing schema info for all tables.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0
    processed_count = 0
    error_count = 0
    skipped_count = 0
    encodings_to_try = ['utf-8', 'cp1252', 'latin-1'] # Add more if needed

    logger.info(f"Starting processing from '{input_dir}' to '{output_dir}'.")
    if schema_data:
        logger.info(f"Loaded schema data for {len(schema_data)} tables.")
    else:
        logger.warning("No schema data provided or loaded. Markdown files will not include schema details.") # Changed to warning

    # Iterate through items in the input directory
    items = list(input_dir.iterdir()) # Convert iterator to list for progress feedback
    total_items = len(items)
    logger.info(f"Found {total_items} items in the input directory.")

    for i, item in enumerate(items):
        # Provide progress update every 500 files or for the last file
        if (i + 1) % 500 == 0 or (i + 1) == total_items:
            logger.info(f"Processing item {i + 1}/{total_items}: {item.name}")

        if item.is_file() and item.suffix.lower() == '.tsv':
            file_count += 1
            logger.debug(f"Processing file: {item.name}...") # Keep debug for individual file start
            detected_encoding = detect_encoding(item, encodings_to_try)

            if not detected_encoding:
                logger.error(f"Failed to decode {item.name} with tried encodings: {', '.join(encodings_to_try)}")
                error_count += 1
                continue # Skip this file

            try:
                content = read_tsv_content(item, detected_encoding)
                # Pass schema_data to tsv_to_markdown
                markdown_content = tsv_to_markdown(content, item.name, schema_data)

                if not markdown_content:
                    # tsv_to_markdown already logged the warning for empty/header-only files
                    skipped_count += 1 # Count skipped files separately
                    continue # Don't write an empty file or count as error

                # Write the generated Markdown content
                output_filename = output_dir / (item.stem + ".md")
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                processed_count += 1

            except Exception as e:
                # Catch errors during read or markdown generation
                logger.error(f"Failed to process {item.name}: {e}", exc_info=True)
                error_count += 1
        else:
            logger.debug(f"Skipping non-TSV file or directory: {item.name}")


    logger.info(f"Processing complete. Total TSV files found: {file_count}. Processed successfully: {processed_count}. Files skipped (empty/header-only): {skipped_count}. Errors: {error_count}.")


def process_file(file_path: Path, output_dir: Path, schema_data: Optional[Dict[str, Any]] = None):
    """Processes a single TSV file and writes its Markdown representation to the output directory."""
    logger.debug(f"Starting processing for file: {file_path.name}")  # Added log
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    tsv_content = None
    detected_encoding = None

    for encoding in encodings_to_try:
        try:
            logger.debug(f"Attempting to read {file_path.name} with encoding: {encoding}")
            with open(file_path, 'r', encoding=encoding) as file:
                tsv_content = file.read()
            detected_encoding = encoding
            logger.debug(f"Successfully read {file_path.name} with encoding: {encoding}")
            break  # Stop trying encodings if one works
        except UnicodeDecodeError:
            logger.debug(f"Failed to decode {file_path.name} with encoding: {encoding}")
            continue  # Try the next encoding
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path.name} with encoding {encoding}: {e}")
            return # Stop processing this file on other read errors

    if tsv_content is None:
        logger.error(f"Could not read file {file_path.name} with any attempted encoding. Skipping.")
        return

    # Check if the file is empty or only contains whitespace
    if not tsv_content.strip():
        logger.warning(f"File {file_path.name} is empty or contains only whitespace. Skipping.")
        return

    try: # Added try block
        # Use csv.reader to handle potential quoting and delimiter issues robustly
        # Increase the field size limit for potentially large fields
        csv.field_size_limit(2**20) # 1MB limit, adjust if needed
        reader = csv.reader(StringIO(tsv_content), delimiter='\t', quotechar='"')

        # Check for header and data rows
        try:
            header = next(reader)
            # Try to get the first data row to see if there's content
            first_data_row = next(reader)
            # Reset reader by creating a new one if we need to process all rows
            reader = csv.reader(StringIO(tsv_content), delimiter='\t', quotechar='"')
            # Skip header again for markdown conversion
            next(reader)
            has_data = True
        except StopIteration:
            # This means there was only a header or the file was truly empty after stripping
            has_data = False
            logger.warning(f"File {file_path.name} has header but no data rows. Skipping content generation.")
        except csv.Error as e:
            logger.error(f"CSV Error reading header/first row of {file_path.name}: {e}. Skipping.")
            return

        if not has_data:
            # Even if no data, we might still want an empty markdown file or one with just the schema
            # For now, we skip as per the warning log
            return
        # Pass the original full content to tsv_to_markdown, it will handle reading again if needed
        markdown_content = tsv_to_markdown(tsv_content, file_path.name, schema_data)

    except Exception as e: # Added except block
        logger.error(f"Error during initial CSV processing or markdown conversion for {file_path.name}: {e}", exc_info=True)
        return # Stop processing this file if CSV parsing fails

    output_file_path = output_dir / f"{file_path.stem}.md"
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
        # logger.info(f"Successfully converted {file_path.name} to {output_file_path.name}")
    except IOError as e:
        logger.error(f"Could not write markdown file {output_file_path.name}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while writing {output_file_path.name}: {e}")


if __name__ == "__main__":
    # --- Logging Setup ---
    # Configure basic logging (level set later based on args)
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # logger = logging.getLogger(__name__) # Removed from here

    # --- Argument Parsing & Setup ---
    parser = argparse.ArgumentParser(description='Convert TSV files in a directory to Markdown tables, optionally enriching with schema data.')
    parser.add_argument('input_dir', type=str, help='Input directory containing TSV files.')
    parser.add_argument('--output-dir', type=str, default=None, help='Optional: Output directory for Markdown files. Defaults to <input_dir>_Markdown next to the input directory.') # Added optional arg
    parser.add_argument('--schema-json', type=str, help='Optional path to the JSON file containing schema definitions.')
    # Add verbose flag for debug prints
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debug print statements.')

    args = parser.parse_args()

    # --- Configure Logging Level based on args ---
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    # logger is already defined globally, basicConfig configures the root logger which it inherits

    input_path = Path(args.input_dir)
    # Determine output directory path
    if args.output_dir:
        output_dir_path = Path(args.output_dir)
        logger.info(f"Using specified output directory: {output_dir_path}")
    else:
        output_dir_path = input_path.parent / f"{input_path.name}_Markdown"
        logger.info(f"Output directory not specified, defaulting to: {output_dir_path}")

    schema_json_path = Path(args.schema_json) if args.schema_json else None

    loaded_schema_data = None
    if schema_json_path:
        if schema_json_path.is_file():
            try:
                with open(schema_json_path, 'r', encoding='utf-8') as f:
                    loaded_schema_data = json.load(f)
                logger.info(f"Successfully loaded schema data from {schema_json_path}")
            except json.JSONDecodeError:
                logger.error(f"Error: Failed to decode JSON from {schema_json_path}. Proceeding without schema data.", exc_info=True)
            except Exception as e:
                logger.error(f"Error loading schema JSON {schema_json_path}: {e}. Proceeding without schema data.", exc_info=True)
        else:
            logger.warning(f"Schema JSON file not found at {schema_json_path}. Proceeding without schema data.")

    if not input_path.is_dir():
        logger.error(f"Error: Input directory not found: {input_path}")
        sys.exit(1) # Exit if input directory is invalid

    # Call the main processing function
    # file_count = 0 # Removed sequential count
    # error_count = 0 # Removed sequential count
    processed_count = 0

    try:
        all_files = list(Path(input_path).rglob('*.tsv')) # Get all files first
        total_files = len(all_files)
        logger.info(f"Found {total_files} TSV files to process.")

        if total_files > 0:
            # Create a partial function with fixed arguments for output_dir and schema_data
            process_file_partial = functools.partial(
                process_file, 
                output_dir=output_dir_path, 
                schema_data=loaded_schema_data
            )

            # Use ProcessPoolExecutor for parallel processing
            # The number of workers defaults to the number of processors on the machine
            with concurrent.futures.ProcessPoolExecutor() as executor:
                logger.info(f"Starting parallel processing using up to {executor._max_workers} workers...")
                
                # map applies the function to each item in all_files
                # We iterate through the results mainly to ensure completion and potentially catch errors
                # Note: Exceptions in worker processes will be raised here when iterating results
                results = executor.map(process_file_partial, all_files)

                # Iterate over results to track progress and handle potential errors from map
                for i, _ in enumerate(results):
                    processed_count += 1 # Count successful iterations from map
                    if (processed_count % 200 == 0) or (processed_count == total_files):
                       logger.info(f"Processed {processed_count}/{total_files} files...")
                    # Error handling for exceptions raised by map needs refinement
                    # A simple count might not reflect true errors logged within workers
                    # Consider adding try-except around the loop if needed, 
                    # but relying on worker logs is often sufficient.

        logger.info(f"Parallel processing finished. Attempted processing {total_files} files.")
        # Note: Final error count relies on checking logs, as direct return from map is complex.

    except Exception as e:
        # Catch errors during directory traversal or file listing
        logger.critical(f"FATAL: Error during directory processing or executor setup: {e}", exc_info=True)
        sys.exit(f"FATAL: Exiting due to error: {e}")

    # Final Summary - Adjust based on parallel execution
    logger.info(f"Script finished. Attempted processing for {total_files} files.")
    logger.info(f"Check logs above for any specific file processing errors.")
    # logger.info(f"Processed {file_count} files successfully.") # Removed old counts
    # if error_count > 0:
    #     logger.warning(f"{error_count} files encountered errors during processing.")
    print("--- Script finished successfully ---") # Use print for final success message