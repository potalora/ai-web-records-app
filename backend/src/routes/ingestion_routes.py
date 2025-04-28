from fastapi import APIRouter, BackgroundTasks, HTTPException, status, File, UploadFile, Form
from pathlib import Path
import logging
from typing import List
import tempfile
import shutil
import os

from ..models.ingestion import EhrIngestionRequest
from ..services.ingestion.ehr_parser import run_ehr_parsing

# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if main app doesn't configure root logger
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


router = APIRouter(
    prefix="/ingest",
    tags=["Ingestion"],
)

@router.post("/ehr", status_code=status.HTTP_202_ACCEPTED)
def trigger_ehr_ingestion(request: EhrIngestionRequest, background_tasks: BackgroundTasks):
    """Triggers the background process to ingest EHR TSV files from a specified directory."""
    logger.info(f"Received request to ingest EHR data from: {request.input_dir}")

    # Basic input validation: Check if input directory exists
    input_path = Path(request.input_dir)
    if not input_path.is_dir():
        logger.error(f"Input directory not found: {request.input_dir}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input directory not found: {request.input_dir}"
        )

    # Add the parsing task to run in the background
    background_tasks.add_task(
        run_ehr_parsing,
        input_dir=request.input_dir,
        output_dir=request.output_dir,
        schema_json=request.schema_json,
        verbose=True # Enable verbose logging for background task for now
    )

    logger.info(f"EHR ingestion task added to background for: {request.input_dir}")
    return {"message": "EHR ingestion process started in the background."}

@router.post("/text", status_code=status.HTTP_200_OK)
async def ingest_text_file(file: UploadFile = File(...)):
    """Accepts a plain text file upload and logs its reception."""
    logger.info("--- Entered /ingest/text endpoint --- ")
    logger.info(f"Received request to ingest text file: {file.filename}")

    if not file.filename:
        logger.warning("Text file upload request received without a filename.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No filename provided with the upload."
        )

    if not file.filename.lower().endswith(".txt"):
        logger.warning(f"Invalid file type uploaded to /text: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only .txt files are accepted at this endpoint."
        )

    try:
        # Read the file content
        content_bytes = await file.read()
        # Decode assuming UTF-8, adjust if other encodings are expected
        content_text = content_bytes.decode('utf-8') 
        
        logger.info(f"Successfully read text file '{file.filename}'. Content starts with: '{content_text[:100]}...' (Length: {len(content_text)}) ")

        # TODO: Implement further processing (e.g., saving, sending to LLM, RAG indexing)

        return {"message": "Text file received successfully.", "filename": file.filename, "size": len(content_text)}

    except UnicodeDecodeError:
        logger.error(f"Failed to decode '{file.filename}' as UTF-8.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Could not decode file content as UTF-8."
        )
    except Exception as e:
        logger.error(f"Error processing text file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred processing the text file."
        )

@router.post("/files", status_code=status.HTTP_200_OK)
async def ingest_files(files: List[UploadFile] = File(...), upload_type: str = Form("files")):
    """Accepts file uploads, handling single files or directories based on upload_type."""
    logger.info(f"--- Entered /ingest/files endpoint --- ")
    logger.info(f"Attempting to process upload with type: {upload_type}")

    # Create a unique temporary directory for this batch
    # Consider making the base path configurable (e.g., via env var)
    base_temp_dir = Path(tempfile.gettempdir()) / "healthai_uploads"
    base_temp_dir.mkdir(parents=True, exist_ok=True)
    batch_temp_dir = Path(tempfile.mkdtemp(prefix=f"{upload_type}_", dir=base_temp_dir))
    logger.info(f"Created temporary directory for batch: {batch_temp_dir}")

    filenames = []
    saved_paths = []

    try:
        for file in files:
            logger.info(f"Processing file: {file.filename} (Content-Type: {file.content_type})")
            original_filename = file.filename or "unknown_file"
            target_path: Path

            if upload_type == 'directory':
                # Assume filename contains the relative path for directory uploads
                # Sanitize the path to prevent directory traversal issues
                # IMPORTANT: This assumes the browser provides relative paths in filename.
                # Needs verification across browsers.
                # A more robust way might involve sending metadata separately.
                sanitized_relative_path = Path(*[part for part in Path(original_filename).parts if part not in (".", "..")])
                target_path = batch_temp_dir / sanitized_relative_path
                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # TODO: Add logic here to detect if the saved file is in a 'media' subdirectory
                # and if it's a PDF. If so, trigger a different processing pipeline
                # (e.g., the one designed for standalone PDF ingestion) instead of assuming
                # it's part of the standard EHR structure (TSV/HTM).

            elif upload_type == 'files':
                # Sanitize filename for direct saving
                sanitized_filename = Path(original_filename).name # Get only the filename part
                target_path = batch_temp_dir / sanitized_filename
            else:
                # This case should ideally not be hit if default is 'files'
                logger.warning(f"Received unexpected upload_type: {upload_type}, treating as 'files'.")
                sanitized_filename = Path(original_filename).name
                target_path = batch_temp_dir / sanitized_filename
                # raise HTTPException(status_code=400, detail="Invalid upload type specified.") # Temporarily treat unexpected as 'files'

            # Save the file
            try:
                with open(target_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                logger.info(f"Successfully saved {original_filename} to {target_path}")
                filenames.append(original_filename)
                saved_paths.append(str(target_path))
            except Exception as e:
                logger.error(f"Failed to save file {original_filename} to {target_path}: {e}")
                # Decide if one failure should abort the whole batch
                raise HTTPException(status_code=500, detail=f"Failed to save file {original_filename}.")
            finally:
                 # Ensure file handle is closed even if copyfileobj fails mid-way
                 await file.close()

        logger.info(f"Successfully processed and saved {len(filenames)} files to {batch_temp_dir}")
        # TODO: Trigger next steps (validation, parsing, etc.) using the batch_temp_dir
        return {
            "message": f"Successfully received and saved {len(filenames)} files.",
            "upload_type": upload_type,
            "filenames": filenames,
            "temp_directory": str(batch_temp_dir) # Return temp dir path for potential further use
        }
    except HTTPException: # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"An error occurred processing the batch in {batch_temp_dir}: {e}", exc_info=True)
        # Clean up potentially partially created temp directory on general failure
        # shutil.rmtree(batch_temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during file processing.")
    # Note: Consider background tasks for longer processing steps after saving.
