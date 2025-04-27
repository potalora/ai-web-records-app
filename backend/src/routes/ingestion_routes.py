from fastapi import APIRouter, BackgroundTasks, HTTPException, status
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
