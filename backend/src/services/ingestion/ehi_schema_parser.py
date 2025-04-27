"""
Parses HTML schema files from the Epic EHI export to extract table metadata.

Reads .htm files from a specified directory, extracts schema information
(table description, primary keys, column names, types, descriptions),
and outputs the consolidated schema as a JSON file.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

try:
    from bs4 import BeautifulSoup
except ImportError:
    logging.error("BeautifulSoup4 is not installed. Please install it: pip install beautifulsoup4")
    # Consider adding lxml for performance: pip install lxml
    exit(1)

def extract_text(element: Optional[Any], default: str = "") -> str:
    """Safely extract text from a BeautifulSoup element."""
    return element.get_text(strip=True) if element else default

def parse_schema_html(html_content: str) -> Optional[Dict[str, Any]]:
    """Parses a single HTML schema file content.

    Args:
        html_content: The HTML content as a string.

    Returns:
        A dictionary containing the extracted schema, or None if parsing fails.
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml') # Use lxml for speed if available, otherwise 'html.parser'
        schema: Dict[str, Any] = {}

        # --- Extract Table Description ---
        desc_table = soup.find('table', class_='KeyValue')
        if desc_table:
            desc_td = desc_table.find('td', class_='T1Value')
            schema['description'] = extract_text(desc_td)
        else:
            schema['description'] = "No description found."
            logging.warning("Could not find description table with class 'KeyValue'")

        # --- Extract Primary Key ---
        pk_header = soup.find('td', string='Primary Key')
        if pk_header:
            pk_table = pk_header.find_parent('table', class_='SubHeader3')
            if pk_table:
                list_table = pk_table.find_next_sibling('table', class_='List')
                if list_table:
                    pk_rows = list_table.find_all('tr')[1:] # Skip header row
                    schema['primary_key'] = [extract_text(row.find('td')) for row in pk_rows if row.find('td')]
                else:
                    schema['primary_key'] = []
                    logging.warning("Could not find primary key list table with class 'List' after header.")
            else:
                 schema['primary_key'] = []
                 logging.warning("Could not find parent table for primary key header.")
        else:
            schema['primary_key'] = []
            logging.warning("Could not find 'Primary Key' header td.")


        # --- Extract Column Information ---
        col_info_header = soup.find('td', string='Column Information')
        schema['columns'] = []
        if col_info_header:
            col_info_parent_table = col_info_header.find_parent('table', class_='SubHeader3')
            if col_info_parent_table:
                logging.debug("Found 'Column Information' parent table (SubHeader3).")
                col_table = col_info_parent_table.find_next_sibling('table', class_='SubList List')
                if col_table:
                    logging.debug("Found column data table ('SubList List') after parent.")
                    tbody = col_table.find('tbody') # Find the tbody within the table
                    if tbody:
                        # Find all direct 'tr' children of the tbody
                        all_rows_in_section = tbody.find_all('tr', recursive=False)
                        logging.debug(f"Found {len(all_rows_in_section)} total rows in the column section tbody.")
                    else:
                        logging.warning("Could not find tbody within the column data table.")
                        all_rows_in_section = [] # Ensure it's an empty list if tbody not found

                    current_column = None
                    rows_processed = 0 # Debugging counter
                    columns_found = 0 # Debugging counter
                    i = 0 # Explicitly initialize index before header check

                    # Skip potential header row if present within this table section
                    if all_rows_in_section and all_rows_in_section[0].find_all('th', recursive=False):
                        logging.debug("Skipping first row as it appears to be a header row (contains th).")
                        i = 1

                    while i < len(all_rows_in_section):
                        row = all_rows_in_section[i]
                        rows_processed += 1
                        logging.debug(f"Processing row index {i} (absolute index in section)")

                        # Find ALL direct child TDs, not just those with class T1Head
                        direct_tds = row.find_all('td', recursive=False)
                        logging.debug(f"  Row {i} has {len(direct_tds)} direct TD children.")

                        # Simpler check: Does it look like a row defining a column (at least 4 cells)?
                        is_potential_column_row = len(direct_tds) >= 4

                        if is_potential_column_row:
                            logging.debug(f"  Row {i} IS potential column definition.")
                            try:
                                current_column = {
                                    'name': extract_text(direct_tds[1]),
                                    'type': extract_text(direct_tds[2]),
                                    'discontinued': extract_text(direct_tds[3]),
                                    'description': '' # Placeholder
                                }
                                logging.debug(f"    Extracted basic info for: {current_column.get('name', 'N/A')}")
                            except IndexError:
                                logging.warning(f"  Row {i} looked like column def, but IndexError occurred accessing cells 1, 2, or 3.", exc_info=False) # Reduce noise
                                current_column = None # Reset if extraction failed
                                i += 1
                                continue # Skip to next row

                            # Look ahead for the description row(s)
                            j = i + 1
                            description_parts = []
                            while j < len(all_rows_in_section):
                                next_row = all_rows_in_section[j]
                                next_row_direct_tds = next_row.find_all('td', recursive=False)

                                # Check if the next row *also* looks like a column definition row
                                is_next_row_column_def = len(next_row_direct_tds) >= 4

                                if is_next_row_column_def:
                                    logging.debug(f"    Next row {j} looks like new column def (>=4 TDs). Stopping description search.")
                                    break # Stop if we hit the next column definition

                                # Otherwise, assume it's part of the description
                                logging.debug(f"    Assuming row {j} is description.")
                                desc_td = next_row.find('td', class_='T1Value', style='white-space: normal;')
                                nested_desc_td = None # Initialize
                                if not desc_td:
                                     # Sometimes description is in a nested table structure
                                    nested_desc_td = next_row.find('td', style='white-space: normal;') # Find any td with this style

                                if desc_td:
                                    description_parts.append(extract_text(desc_td))
                                    logging.debug(f"      Found description part in T1Value td.")
                                elif nested_desc_td:
                                    description_parts.append(extract_text(nested_desc_td))
                                    logging.debug(f"      Found description part in nested td (style='white-space: normal;').")
                                j += 1

                            # Append completed column data
                            if current_column:
                                current_column['description'] = ' '.join(description_parts).strip()
                                logging.debug(f"    Final description for {current_column.get('name', 'N/A')}: '{current_column.get('description', '')[:50]}...'" )
                                schema['columns'].append(current_column)
                                columns_found += 1
                                logging.debug(f"    Appended column {current_column.get('name', 'N/A')}. Total columns found so far: {columns_found}")
                                current_column = None # Reset for next iteration
                            i = j # Move main index past description rows
                        else:
                            logging.debug(f"  Row {i} is NOT potential column definition (only {len(direct_tds)} TDs). Skipping.")
                            i += 1 # Move to next row

                    logging.info(f"Finished processing rows for columns. Rows processed: {rows_processed}. Columns appended: {columns_found}")
                else:
                    logging.warning("Could not find column data table with class 'SubList List' after parent.")
            else:
                 logging.warning("Could not find parent table (SubHeader3) for 'Column Information' header.")
        else:
             logging.warning("Could not find 'Column Information' header td.")

        if not schema.get('columns'):
            logging.warning("No columns extracted.")
            return None # Indicate failure if no columns found

        return schema

    except Exception as e:
        logging.error(f"Error parsing HTML: {e}", exc_info=True)
        return None

def parse_all_schemas(schema_dir: Path, output_file: Path) -> None:
    """Parses all .htm schema files in a directory and saves to JSON.

    Args:
        schema_dir: The directory containing the .htm schema files.
        output_file: The path to the output JSON file.
    """
    all_schemas: Dict[str, Dict[str, Any]] = {}
    file_count = 0
    parsed_count = 0
    error_files = []

    logging.info(f"Starting schema parsing from directory: {schema_dir}")

    for item in schema_dir.iterdir():
        if item.is_file() and item.suffix.lower() == '.htm':
            file_count += 1
            table_name = item.stem # Use filename without extension as table name
            logging.info(f"Parsing schema for table: {table_name} (File: {item.name})")
            try:
                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                schema_data = parse_schema_html(html_content)
                
                if schema_data:
                    all_schemas[table_name] = schema_data
                    parsed_count += 1
                else:
                    logging.error(f"Failed to parse schema from file: {item.name}")
                    error_files.append(item.name)
            except Exception as e:
                logging.error(f"Error processing file {item.name}: {e}", exc_info=True)
                error_files.append(item.name)

    logging.info(f"Finished parsing. Total files found: {file_count}")
    logging.info(f"Successfully parsed: {parsed_count}")
    if error_files:
        logging.warning(f"Errors occurred in {len(error_files)} files: {', '.join(error_files)}")

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_schemas, f, indent=4)
        logging.info(f"Schema successfully saved to: {output_file}")
    except IOError as e:
        logging.error(f"Failed to write schema JSON to {output_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse Epic EHI HTML schema files into JSON.")
    parser.add_argument(
        "schema_dir",
        type=str,
        help="Directory containing the .htm schema files."
    )
    parser.add_argument(
        "output_file",
        type=str,
        help="Path to the output JSON file to save the schema."
    )
    args = parser.parse_args()

    schema_path = Path(args.schema_dir)
    output_path = Path(args.output_file)

    if not schema_path.is_dir():
        logging.error(f"Error: Schema directory not found or is not a directory: {schema_path}")
        exit(1)

    parse_all_schemas(schema_path, output_path)
