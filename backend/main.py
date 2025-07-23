from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
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

# Import the dashboard router
from src.routes.dashboard_routes import router as dashboard_router

# --- Fix import path for evidence_retriever --- #
from src.services.evidence_retriever import search_pubmed # Corrected path

# --- Import FHIR parsing functionality --- #
from src.services.ingestion.ehr_parser import parse_fhir_resource, FHIRParsingError

# --- Increase Starlette form part limit --- #
import starlette.formparsers
starlette.formparsers.FormParser._max_parts = 10000 # Default is 1000
starlette.formparsers.MultiPartParser._max_parts = 10000 # Default is 1000

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

# Import database client
from src.database import db_client

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Connect to database
        await db_client.connect()
        logger.info("Database connected successfully")
        
        # Perform health check
        health = await db_client.health_check()
        logger.info(f"Database health: {health}")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't exit - allow app to run without database for now

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        await db_client.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Include the ingestion router using the alias
app.include_router(ingestion_router)

# Include authentication routes
from src.routes.auth_routes import router as auth_router
app.include_router(auth_router)

# Import authentication dependency
from src.services.auth.auth_service import get_current_user, User

# Include dashboard routes
app.include_router(dashboard_router)

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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check including database status."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "healthy"
        }
    }
    
    # Check database
    try:
        db_health = await db_client.health_check()
        health_status["services"]["database"] = db_health["status"]
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")
    
    return health_status


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
    provider: str = Form(...), 
    model_id: str = Form(...), 
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Receives a PDF file, provider, and model ID, returns a summary and saves to database."""
    start_time = time.time()
    logger.info(
        f"Received PDF summarization request for file: {file.filename}, provider: {provider}, model: {model_id}, user: {current_user.id}"
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
        # Read file content for database storage
        await file.seek(0)  # Reset file pointer
        content_bytes = await file.read()
        file_size = len(content_bytes)
        
        # Reset file pointer for LLM processing
        await file.seek(0)
        
        # Call the refactored service function
        summary = await summarize_pdf_auto(
            provider=provider, model_id=model_id, pdf_file=file
        )
        
        # Save to database
        from src.services.database_service import get_database
        from src.services.security.encryption import encryption_service
        from src.services.security.audit import audit_service, AuditAction
        from src.models.file_ingestion import RecordType, ProcessingStatus
        
        db = get_database()
        
        # Encrypt PDF content
        encrypted_pdf = encryption_service.encrypt_bytes(content_bytes, "health_record")
        
        # Create health record for the PDF
        record_title = title or f"PDF Summary - {file.filename}"
        health_record = await db.healthrecord.create({
            "data": {
                "userId": current_user.id,
                "recordType": RecordType.OTHER.value,
                "title": record_title,
                "description": description,
                "encryptedData": encrypted_pdf["ciphertext"],
                "encryptionIv": encrypted_pdf["iv"],
                "encryptionSalt": encrypted_pdf["salt"],
                "status": ProcessingStatus.COMPLETED.value,
                "metadata": {
                    "originalFilename": file.filename,
                    "fileSize": file_size,
                    "contentType": "application/pdf",
                    "processing": {
                        "provider": provider,
                        "model": model_id,
                        "processingTime": time.time() - start_time
                    }
                }
            }
        })
        
        # Create document reference
        document = await db.document.create({
            "data": {
                "healthRecordId": health_record.id,
                "fileName": file.filename,
                "fileType": "application/pdf",
                "fileSize": file_size,
                "uploadedBy": current_user.id,
                "storageUrl": f"encrypted:{health_record.id}",
            }
        })
        
        # Encrypt and save summary
        encrypted_summary = encryption_service.encrypt(summary, "summary")
        summary_record = await db.summary.create({
            "data": {
                "healthRecordId": health_record.id,
                "type": "PDF_SUMMARY",
                "encryptedContent": encrypted_summary["ciphertext"],
                "encryptionIv": encrypted_summary["iv"], 
                "encryptionSalt": encrypted_summary["salt"],
                "generatedBy": f"{provider}:{model_id}",
                "metadata": {
                    "provider": provider,
                    "model": model_id,
                    "processingTime": time.time() - start_time,
                    "originalFilename": file.filename
                }
            }
        })
        
        # Log audit entries
        await audit_service.log_activity(
            user_id=current_user.id,
            action=AuditAction.CREATE,
            resource_type="HealthRecord",
            resource_id=health_record.id,
            details={
                "filename": file.filename,
                "record_type": RecordType.OTHER.value,
                "action": "pdf_upload_and_summarization"
            }
        )
        
        await audit_service.log_activity(
            user_id=current_user.id,
            action=AuditAction.CREATE,
            resource_type="Summary",
            resource_id=summary_record.id,
            details={
                "type": "PDF_SUMMARY",
                "provider": provider,
                "model": model_id,
                "health_record_id": health_record.id
            }
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(
            f"Successfully summarized and saved {file.filename} in {processing_time:.2f} seconds using {provider} model {model_id}. Records: {health_record.id}, Summary: {summary_record.id}"
        )
        
        return {
            "summary": summary,
            "health_record_id": health_record.id,
            "summary_id": summary_record.id,
            "document_id": document.id,
            "processing_time": processing_time
        }

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
async def upload_file(
    file: UploadFile = File(...), 
    title: str = Form(None),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Handles file uploads, parsing FHIR JSON/XML and saving to database."""
    filename = file.filename
    logger.info(f"Received upload request for file: {filename} from user: {current_user.id}")

    if not filename:
        logger.warning("File upload request received without a filename.")
        raise HTTPException(
            status_code=400, detail="No filename provided with the upload."
        )

    # Determine file type and process accordingly
    file_extension = Path(filename).suffix.lower()

    if file_extension in [".json", ".xml"]:
        # Handle FHIR JSON/XML
        try:
            # Read file content
            content_bytes = await file.read()
            file_size = len(content_bytes)
            
            # Create a temporary directory for FHIR parsing
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / filename
                # Save the uploaded file to the temporary path
                with open(tmp_path, "wb") as buffer:
                    buffer.write(content_bytes)

                logger.info(f"Attempting to parse FHIR file: {tmp_path}")
                # Parse the file using the utility function
                fhir_resource = parse_fhir_resource(tmp_path)

                resource_type = getattr(fhir_resource, 'resource_type', 'Unknown')
                resource_id = getattr(fhir_resource, 'id', 'N/A')

                logger.info(
                    f"Successfully parsed FHIR resource: Type='{resource_type}', ID='{resource_id}' from {filename}"
                )
                
                # Save to database
                from src.services.database_service import get_database
                from src.services.security.encryption import encryption_service
                from src.services.security.audit import audit_service, AuditAction
                from src.models.file_ingestion import RecordType, ProcessingStatus
                
                db = get_database()
                
                # Encrypt file content
                encrypted_content = encryption_service.encrypt_bytes(content_bytes, "health_record")
                
                # Create health record
                record_title = title or f"FHIR {resource_type} - {filename}"
                health_record = await db.healthrecord.create({
                    "data": {
                        "userId": current_user.id,
                        "recordType": RecordType.OTHER.value,
                        "title": record_title,
                        "description": description,
                        "encryptedData": encrypted_content["ciphertext"],
                        "encryptionIv": encrypted_content["iv"],
                        "encryptionSalt": encrypted_content["salt"],
                        "status": ProcessingStatus.COMPLETED.value,
                        "metadata": {
                            "originalFilename": filename,
                            "fileSize": file_size,
                            "contentType": file.content_type or f"application/{file_extension[1:]}",
                            "fhir": {
                                "resourceType": resource_type,
                                "resourceId": resource_id
                            }
                        }
                    }
                })
                
                # Create document reference
                document = await db.document.create({
                    "data": {
                        "healthRecordId": health_record.id,
                        "fileName": filename,
                        "fileType": file.content_type or f"application/{file_extension[1:]}",
                        "fileSize": file_size,
                        "uploadedBy": current_user.id,
                        "storageUrl": f"encrypted:{health_record.id}",
                    }
                })
                
                # Log audit entry
                await audit_service.log_activity(
                    user_id=current_user.id,
                    action=AuditAction.CREATE,
                    resource_type="HealthRecord",
                    resource_id=health_record.id,
                    details={
                        "filename": filename,
                        "record_type": RecordType.OTHER.value,
                        "fhir_resource_type": resource_type,
                        "fhir_resource_id": resource_id
                    }
                )
                
                return {
                    "message": f"Successfully parsed and saved FHIR {file_extension.upper()[1:]} file.",
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "health_record_id": health_record.id,
                    "document_id": document.id,
                    "data": fhir_resource.model_dump() if hasattr(fhir_resource, 'model_dump') else str(fhir_resource)
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

    elif file_extension == ".pdf":
        # Handle PDF - redirect to /ingest/files endpoint logic
        try:
            content_bytes = await file.read()
            file_size = len(content_bytes)
            
            # Save to database like other files
            from src.services.database_service import get_database
            from src.services.security.encryption import encryption_service
            from src.services.security.audit import audit_service, AuditAction
            from src.models.file_ingestion import RecordType, ProcessingStatus
            
            db = get_database()
            
            # Encrypt PDF content
            encrypted_content = encryption_service.encrypt_bytes(content_bytes, "health_record")
            
            # Create health record
            record_title = title or f"PDF Document - {filename}"
            health_record = await db.healthrecord.create({
                "data": {
                    "userId": current_user.id,
                    "recordType": RecordType.OTHER.value,
                    "title": record_title,
                    "description": description,
                    "encryptedData": encrypted_content["ciphertext"],
                    "encryptionIv": encrypted_content["iv"],
                    "encryptionSalt": encrypted_content["salt"],
                    "status": ProcessingStatus.COMPLETED.value,
                    "metadata": {
                        "originalFilename": filename,
                        "fileSize": file_size,
                        "contentType": "application/pdf"
                    }
                }
            })
            
            # Create document reference
            document = await db.document.create({
                "data": {
                    "healthRecordId": health_record.id,
                    "fileName": filename,
                    "fileType": "application/pdf",
                    "fileSize": file_size,
                    "uploadedBy": current_user.id,
                    "storageUrl": f"encrypted:{health_record.id}",
                }
            })
            
            # Log audit entry
            await audit_service.log_activity(
                user_id=current_user.id,
                action=AuditAction.CREATE,
                resource_type="HealthRecord",
                resource_id=health_record.id,
                details={
                    "filename": filename,
                    "record_type": RecordType.OTHER.value,
                    "action": "pdf_upload"
                }
            )
            
            logger.info(f"Successfully saved PDF file: {filename} to database as record {health_record.id}")
            return {
                "message": f"PDF file '{filename}' uploaded and saved successfully.",
                "health_record_id": health_record.id,
                "document_id": document.id
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF upload for {filename}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred processing the PDF file.")

    else:
        # Unsupported file type
        logger.warning(f"Unsupported file type uploaded: {filename}")
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
