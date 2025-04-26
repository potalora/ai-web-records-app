# /backend/scripts/update_anthropic_models.py
"""
Script to update the hardcoded list of Anthropic models in model_registry.py.

Usage:
1.  Update the `LATEST_ANTHROPIC_MODELS` list below with models from
    Anthropic's documentation (https://docs.anthropic.com/en/docs/about-claude/models/all-models).
2.  Run this script from the root of the `backend` directory:
    `python scripts/update_anthropic_models.py`
"""

import os
import re

# --- UPDATE THIS LIST --- #
# Sourced from: https://docs.anthropic.com/en/docs/about-claude/models/all-models (as of 2025-04-26)
# Include specific, dated model versions suitable for vision/PDF tasks.
LATEST_ANTHROPIC_MODELS = [
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
]
# --- END UPDATE LIST --- #

MODEL_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "services", "model_registry.py"
)


def update_model_list_in_file(file_path: str, new_models: list[str]):
    """Reads the file, replaces the model list, and writes it back."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    # Create the new list string representation (formatted like the original)
    new_list_str = "["
    for model in new_models:
        new_list_str += f"\n        '{model}',"
    new_list_str += "\n    ]"

    # Define start and end markers for the list within the function
    # This regex looks for `known_models = [` and the closing `]` of that list
    # It uses non-greedy matching `.*?` and handles potential whitespace/newlines `\s*`
    pattern = re.compile(
        r"(known_models\s*=\s*\[).*?(\]\s*# End known_models marker - DO NOT REMOVE)",
        re.DOTALL,  # . matches newline
    )

    # Construct the replacement string
    replacement = f"\1{new_list_str} # End known_models marker - DO NOT REMOVE"

    # Perform the replacement
    new_content, num_replacements = pattern.subn(replacement, content)

    if num_replacements == 1:
        try:
            with open(file_path, "w") as f:
                f.write(new_content)
            print(f"Successfully updated model list in {file_path}")
        except IOError as e:
            print(f"Error writing updated file: {e}")
    elif num_replacements == 0:
        print("Error: Could not find the 'known_models' list block.")
        print(
            "Ensure the start marker 'known_models = [' and end marker ']# End known_models marker - DO NOT REMOVE' exist."
        )
    else:
        print(
            f"Error: Found {num_replacements} matches for the model block. Expected 1. Manual check required."
        )


if __name__ == "__main__":
    # Add a marker to the source file to make replacement safer
    # This needs to be done manually once or by a separate edit
    print("Checking for end marker in model_registry.py...")
    try:
        with open(MODEL_REGISTRY_PATH, "r") as f:
            content = f.read()
        if "# End known_models marker - DO NOT REMOVE" not in content:
            print("WARNING: End marker not found in get_anthropic_pdf_models.")
            print(
                "Please manually add the comment '# End known_models marker - DO NOT REMOVE' immediately after the closing ']' of the known_models list in that function."
            )
            print(
                "Example:\n            known_models = [\n                'model-1',\n                'model-2',\n            ] # End known_models marker - DO NOT REMOVE"
            )
        else:
            print("End marker found. Proceeding with update...")
            update_model_list_in_file(MODEL_REGISTRY_PATH, LATEST_ANTHROPIC_MODELS)
    except FileNotFoundError:
        print(
            f"Error: model_registry.py not found at expected path: {MODEL_REGISTRY_PATH}"
        )
