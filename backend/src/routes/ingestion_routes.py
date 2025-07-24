from fastapi import APIRouter, BackgroundTasks, HTTPException, status, File, UploadFile, Form, Depends
from pathlib import Path
import logging
from typing import List
import tempfile
import shutil
import os
import uuid
from datetime import datetime

from ..models.ingestion import EhrIngestionRequest
from ..models.file_ingestion import (
    TextIngestionRequest, 
    TextIngestionResponse, 
    FileIngestionResponse,
    RecordType,
    ProcessingStatus
)
from ..services.ingestion.ehr_parser import run_ehr_parsing
from ..services.auth.auth_service import get_current_user, User
from ..services.database_service import get_database
from ..services.security.encryption import encryption_service
from ..services.security.audit import audit_service, AuditAction

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

@router.post("/text", status_code=status.HTTP_200_OK, response_model=TextIngestionResponse)
async def ingest_text_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    record_type: RecordType = Form(RecordType.OTHER),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Accepts a plain text file upload and saves it to the database."""
    logger.info(f"--- Entered /ingest/text endpoint for user {current_user.id} ---")
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

    db = get_database()
    
    try:
        # Read and decode file content
        content_bytes = await file.read()
        content_text = content_bytes.decode('utf-8')
        
        logger.info(f"Successfully read text file '{file.filename}'. Content length: {len(content_text)}")

        # Encrypt the content as bytes for consistency
        encrypted_content = encryption_service.encrypt_bytes(content_text.encode('utf-8'), "health_record")
        
        # Create health record in database
        health_record = await db.healthrecord.create({
            "data": {
                "userId": current_user.id,
                "recordType": record_type.value,
                "title": title.strip(),
                "description": description.strip() if description else None,
                "encryptedData": encrypted_content["ciphertext"],  # bytes
                "encryptionIv": encrypted_content["iv"],
                "encryptionSalt": encrypted_content["salt"],
                "status": ProcessingStatus.COMPLETED.value,
                "metadata": {
                    "originalFilename": file.filename,
                    "fileSize": len(content_bytes),
                    "contentType": file.content_type or "text/plain"
                }
            }
        })
        
        # Create document reference
        document = await db.document.create({
            "data": {
                "healthRecordId": health_record.id,
                "fileName": file.filename,
                "fileType": file.content_type or "text/plain",
                "fileSize": len(content_bytes),
                "uploadedBy": current_user.id,
                "storageUrl": f"encrypted:{health_record.id}",  # Indicates data is encrypted in health record
            }
        })

        # Log the activity for audit
        await audit_service.log_activity(
            user_id=current_user.id,
            action=AuditAction.CREATE.value,
            resource_type="HealthRecord",
            resource_id=health_record.id,
            details={"filename": file.filename, "record_type": record_type.value}
        )

        logger.info(f"Successfully created health record {health_record.id} and document {document.id}")
        
        return TextIngestionResponse(
            health_record_id=health_record.id,
            message=f"Text file '{file.filename}' ingested successfully",
            content_length=len(content_text)
        )

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

@router.post("/files", status_code=status.HTTP_200_OK, response_model=FileIngestionResponse)
async def ingest_files(
    files: List[UploadFile] = File(...), 
    upload_type: str = Form("files"),
    title: str = Form(None),
    record_type: RecordType = Form(RecordType.OTHER),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Accepts file uploads and saves them to the database with proper encryption."""
    logger.info(f"--- Entered /ingest/files endpoint for user {current_user.id} ---")
    logger.info(f"Processing {len(files)} files with upload_type: {upload_type}")

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    # Generate batch ID
    batch_id = str(uuid.uuid4())
    batch_title = title or f"File batch uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    db = get_database()
    health_record_ids = []
    document_ids = []
    processed_files = 0

    try:
        for file in files:
            logger.info(f"Processing file: {file.filename} (Content-Type: {file.content_type})")
            
            if not file.filename:
                logger.warning("Skipping file without filename")
                continue

            # Read file content
            content_bytes = await file.read()
            file_size = len(content_bytes)
            
            # Determine appropriate record type based on file extension if not specified
            file_extension = Path(file.filename).suffix.lower()
            determined_record_type = _determine_record_type(file_extension, file.content_type)
            final_record_type = record_type if record_type != RecordType.OTHER else determined_record_type

            # Create individual title for this file
            file_title = f"{batch_title} - {file.filename}" if len(files) > 1 else (title or file.filename)

            # For text files, encrypt text content as bytes
            if file_extension == '.txt' or (file.content_type and 'text/' in file.content_type):
                try:
                    content_text = content_bytes.decode('utf-8')
                    # Use encrypt_bytes for consistency - all data stored as bytes
                    encrypted_content = encryption_service.encrypt_bytes(content_text.encode('utf-8'), "health_record")
                    
                    # Store as encrypted bytes
                    health_record = await db.healthrecord.create({
                        "data": {
                            "userId": current_user.id,
                            "recordType": final_record_type.value,
                            "title": file_title,
                            "description": description,
                            "encryptedData": encrypted_content["ciphertext"],  # bytes
                            "encryptionIv": encrypted_content["iv"],
                            "encryptionSalt": encrypted_content["salt"],
                            "status": ProcessingStatus.COMPLETED.value,
                            "metadata": {
                                "originalFilename": file.filename,
                                "fileSize": file_size,
                                "contentType": file.content_type,
                                "batchId": batch_id,
                                "uploadType": upload_type
                            }
                        }
                    })
                    
                except UnicodeDecodeError:
                    # If text decoding fails, treat as binary
                    encrypted_content = encryption_service.encrypt_bytes(content_bytes, "health_record")
                    
                    health_record = await db.healthrecord.create({
                        "data": {
                            "userId": current_user.id,
                            "recordType": final_record_type.value,
                            "title": file_title,
                            "description": description,
                            "encryptedData": encrypted_content["ciphertext"],  # bytes for binary data
                            "encryptionIv": encrypted_content["iv"],
                            "encryptionSalt": encrypted_content["salt"],
                            "status": ProcessingStatus.COMPLETED.value,
                            "metadata": {
                                "originalFilename": file.filename,
                                "fileSize": file_size,
                                "contentType": file.content_type,
                                "batchId": batch_id,
                                "uploadType": upload_type
                            }
                        }
                    })
            else:
                # For binary files (PDFs, images, etc.), encrypt as binary
                encrypted_content = encryption_service.encrypt_bytes(content_bytes, "health_record")
                
                health_record = await db.healthrecord.create({
                    "data": {
                        "userId": current_user.id,
                        "recordType": final_record_type.value,
                        "title": file_title,
                        "description": description,
                        "encryptedData": encrypted_content["ciphertext"],  # bytes for binary data
                        "encryptionIv": encrypted_content["iv"],
                        "encryptionSalt": encrypted_content["salt"],
                        "status": ProcessingStatus.COMPLETED.value,
                        "metadata": {
                            "originalFilename": file.filename,
                            "fileSize": file_size,
                            "contentType": file.content_type,
                            "batchId": batch_id,
                            "uploadType": upload_type
                        }
                    }
                })

            # Create document reference
            document = await db.document.create({
                "data": {
                    "healthRecordId": health_record.id,
                    "fileName": file.filename,
                    "fileType": file.content_type or "application/octet-stream",
                    "fileSize": file_size,
                    "uploadedBy": current_user.id,
                    "storageUrl": f"encrypted:{health_record.id}",
                    "metadata": {
                        "batchId": batch_id,
                        "uploadType": upload_type
                    }
                }
            })

            # Log audit entry
            await audit_service.log_activity(
                user_id=current_user.id,
                action=AuditAction.CREATE.value,
                resource_type="HealthRecord",
                resource_id=health_record.id,
                details={
                    "filename": file.filename,
                    "record_type": final_record_type.value,
                    "batch_id": batch_id,
                    "file_size": file_size
                }
            )

            health_record_ids.append(health_record.id)
            document_ids.append(document.id)
            processed_files += 1

            logger.info(f"Successfully processed file {file.filename} -> record {health_record.id}")

        logger.info(f"Successfully processed {processed_files} files in batch {batch_id}")
        
        return FileIngestionResponse(
            batch_id=batch_id,
            message=f"Successfully processed {processed_files} files",
            files_processed=processed_files,
            health_record_ids=health_record_ids,
            document_ids=document_ids
        )

    except Exception as e:
        logger.error(f"Error processing file batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred processing the files: {str(e)}"
        )


def _determine_record_type(file_extension: str, content_type: str) -> RecordType:
    """Determine record type based on file extension and content type."""
    # Map file extensions to record types
    extension_map = {
        '.pdf': RecordType.OTHER,
        '.txt': RecordType.CLINICAL_NOTE,
        '.jpg': RecordType.RADIOLOGY,
        '.jpeg': RecordType.RADIOLOGY,
        '.png': RecordType.RADIOLOGY,
        '.dcm': RecordType.RADIOLOGY,
        '.xml': RecordType.OTHER,
        '.json': RecordType.OTHER,
    }
    
    # Check content type for additional hints
    if content_type:
        if 'image/' in content_type:
            return RecordType.RADIOLOGY
        elif 'text/' in content_type:
            return RecordType.CLINICAL_NOTE
    
    return extension_map.get(file_extension, RecordType.OTHER)
