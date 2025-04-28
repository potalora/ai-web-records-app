from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv
from typing import List, Optional, Dict
from pydantic import BaseModel
import time
from google.api_core import exceptions as GoogleAPIErrors
from src.services.model_registry import (
    get_available_pdf_models,
)
from src.services.llm_service import (
    summarize_pdf_auto,
)

# Import specific exceptions from LLM services
from openai import APIError as OpenAIAPIError
from anthropic import APIError as AnthropicAPIError

# Remove FHIR loading/parsing from main.py - should be handled in services

# Import libraries for temp file handling
import shutil
import tempfile
from pathlib import Path

# Import the ingestion router from src.routes.ingestion_routes with an alias
from src.routes.ingestion_routes import router as ingestion_router

# --- Fix import path for evidence_retriever --- #
from src.services.evidence_retriever import search_pubmed # Corrected path

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS Middleware Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3010",
    "http://127.0.0.1:3010",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the ingestion router using the alias
app.include_router(ingestion_router)

# --- Pydantic Models ---
class PubMedQuery(BaseModel):
    query: str
    max_results: Optional[int] = 10


class PubMedArticle(BaseModel):
    title: str
    abstract: Optional[str] = None
    url: str


@app.get("/")
def read_root():
    return {"message": "AI Health Records API is running!"}


# Example endpoint
@app.get("/hello")
def hello_world():
    return {"message": "Hello World"}


# --- New Endpoint for Available Models ---
@app.get("/available-models/")
async def available_models():
    """Returns a dictionary of available PDF-capable models grouped by provider."""
    logger.info("Request received for /available-models/")
    try:
        models = await get_available_pdf_models()
        return models
    except Exception as e:
        logger.error(
            f"Unexpected error in /available-models/ endpoint: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving available models.",
        )


# Endpoint to list available models
@app.get("/models/")
async def list_models():
    """
    Endpoint to get a list of available models suitable for PDF summarization,
    grouped by provider. Fetches dynamically where implemented.
    """
    try:
        models = await get_available_pdf_models()
        if not models or all(not v for v in models.values()):
            # Handle cases where fetching might fail for all providers
            raise HTTPException(
                status_code=503, detail="Could not retrieve models from providers."
            )
        return models
    except Exception as e:
        logging.error(f"Error retrieving available models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving models."
        )


@app.post("/summarize-pdf/")
async def summarize_pdf(
    provider: str = Form(...), model_id: str = Form(...), file: UploadFile = File(...)
):
    """Receives a PDF file, provider, and model ID, and returns a summary."""
    start_time = time.time()
    logger.info(
        f"Received PDF summarization request for file: {file.filename}, provider: {provider}, model: {model_id}"
    )

    # Basic validation
    if provider not in ["openai", "google", "anthropic"]:
        logger.warning(f"Invalid provider specified: {provider}")
        raise HTTPException(
            status_code=400,
            detail="Invalid provider specified. Choose 'openai', 'google', or 'anthropic'.",
        )

    if not file.filename:
        logger.warning("File upload request received without a filename.")
        raise HTTPException(
            status_code=400, detail="No filename provided with the upload."
        )

    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are accepted."
        )

    try:
        # Call the refactored service function
        summary = await summarize_pdf_auto(
            provider=provider, model_id=model_id, pdf_file=file
        )
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(
            f"Successfully summarized {file.filename} in {processing_time:.2f} seconds using {provider} model {model_id}."
        )
        return {"summary": summary}

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions raised from the service layer (e.g., conversion failure)
        logger.error(
            f"HTTPException during summarization for {file.filename}: {http_exc.detail}"
        )
        raise http_exc
    except ValueError as ve:
        # Catch ValueErrors (e.g., unsupported provider from service layer, though unlikely now)
        logger.error(f"ValueError during summarization for {file.filename}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except (
        OpenAIAPIError,
        GoogleAPIErrors.GoogleAPIError,
        AnthropicAPIError,
    ) as api_error:
        # Specific API errors caught in service, re-raised, caught here
        logger.error(
            f"API Error during summarization for {file.filename} with {provider}: {api_error}",
            exc_info=True,
        )
        # Provide a generic message to the client
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with the {provider.capitalize()} API.",
        )
    except Exception as e:
        # Catch-all for other unexpected errors
        logger.critical(
            f"Unexpected error during summarization for {file.filename}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred during summarization."
        )


# --- New Upload Endpoint --- 
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Handles file uploads, parsing FHIR JSON/XML and acknowledging PDFs."""
    filename = file.filename
    logger.info(f"Received upload request for file: {filename}")

    if not filename:
        logger.warning("File upload request received without a filename.")
        raise HTTPException(
            status_code=400, detail="No filename provided with the upload."
        )

    # Determine file type and process accordingly
    file_extension = Path(filename).suffix.lower()

    if file_extension in [".json", ".xml"]:
        # Handle FHIR JSON/XML
        # Create a temporary file to store the uploaded content
        # because parse_fHIR_resource expects a file path
        try:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / filename
                # Save the uploaded file to the temporary path
                with open(tmp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                logger.info(f"Attempting to parse FHIR file: {tmp_path}")
                # Parse the file using the utility function
                fhir_resource = parse_fhir_resource(tmp_path)

                resource_type = getattr(fhir_resource, 'resource_type', 'Unknown')
                resource_id = getattr(fhir_resource, 'id', 'N/A')

                logger.info(
                    f"Successfully parsed FHIR resource: Type='{resource_type}', ID='{resource_id}' from {filename}"
                )
                return {
                    "message": f"Successfully parsed FHIR {file_extension.upper()[1:]} file.",
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }

        except FHIRParsingError as e:
            logger.error(f"FHIR parsing failed for {filename}: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Invalid FHIR file: {e}")
        except IOError as e:
            logger.error(f"File IO error during upload processing for {filename}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Server error reading uploaded file.")
        except Exception as e:
            logger.critical(
                f"Unexpected error during FHIR file upload processing for {filename}: {e}",
                exc_info=True
            )
            raise HTTPException(status_code=500, detail="An unexpected server error occurred.")
        finally:
            # Ensure the file object is closed
            # (shutil.copyfileobj should handle this, but belt-and-suspenders)
            file.file.close()

    elif file_extension == ".pdf":
        # Handle PDF (Placeholder - just acknowledge for now)
        # Actual PDF ingestion/processing logic would go here or be called from here
        logger.info(f"Received PDF file: {filename}. Ingestion logic pending.")
        file.file.close() # Close the file
        return {"message": f"PDF file '{filename}' received. Processing TBD."}

    else:
        # Unsupported file type
        logger.warning(f"Unsupported file type uploaded: {filename}")
        file.file.close() # Close the file
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{file_extension}'. Only PDF, JSON, and XML are currently supported."
        )


# --- New Endpoint for PubMed Search ---
@app.post("/retrieve-evidence/pubmed", response_model=List[Dict[str, Optional[str]]])
async def retrieve_pubmed_evidence(pubmed_query: PubMedQuery):
    """
    Accepts a query and searches PubMed via the evidence_retriever service.
    """
    logger.info(
        f"Received PubMed search request: query='{pubmed_query.query}', max_results={pubmed_query.max_results}"
    )
    try:
        results = search_pubmed(
            query=pubmed_query.query, max_results=pubmed_query.max_results
        )
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No PubMed articles found for the query or an error occurred during the search.",
            )
        return results
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        logger.exception(
            f"Error during PubMed search for query: '{pubmed_query.query}'"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving PubMed evidence."
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Uvicorn server on port {port} with reload enabled.")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
