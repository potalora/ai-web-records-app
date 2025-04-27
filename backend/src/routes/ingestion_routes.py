from fastapi import APIRouter, BackgroundTasks, HTTPException, status, File, UploadFile
from pathlib import Path
import logging

from backend.src.models.ingestion import EhrIngestionRequest
from backend.src.services.ingestion.ehr_parser import run_ehr_parsing

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
