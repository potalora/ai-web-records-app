from pydantic import BaseModel, Field
from typing import Optional

class EhrIngestionRequest(BaseModel):
    """Request model for triggering EHR TSV ingestion."""
    input_dir: str = Field(..., description="Absolute path to the directory containing EHR TSV files.")
    output_dir: Optional[str] = Field(None, description="Optional absolute path for the output Markdown directory. Defaults to '<input_dir>_Markdown'.")
    schema_json: Optional[str] = Field(None, description="Optional absolute path to the JSON schema file.")
