"""
Pydantic models for file ingestion requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class RecordType(str, Enum):
    """Types of health records"""
    LAB_RESULT = "LAB_RESULT"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    RADIOLOGY = "RADIOLOGY"
    PRESCRIPTION = "PRESCRIPTION"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    PATHOLOGY = "PATHOLOGY"
    CARDIOLOGY = "CARDIOLOGY"
    OTHER = "OTHER"

class ProcessingStatus(str, Enum):
    """Processing status for uploaded files"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class FileIngestionRequest(BaseModel):
    """Request model for file ingestion"""
    title: str = Field(..., min_length=1, max_length=255, description="Title for the health record")
    record_type: RecordType = Field(default=RecordType.OTHER, description="Type of medical record")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

class TextIngestionRequest(FileIngestionRequest):
    """Request model for text ingestion"""
    content: str = Field(..., min_length=1, description="Text content to ingest")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

class FileIngestionResponse(BaseModel):
    """Response model for file ingestion"""
    batch_id: str = Field(..., description="Unique identifier for the ingestion batch")
    message: str = Field(..., description="Success message")
    files_processed: int = Field(..., description="Number of files processed")
    health_record_ids: List[str] = Field(default_factory=list, description="Created health record IDs")
    document_ids: List[str] = Field(default_factory=list, description="Created document IDs")

class TextIngestionResponse(BaseModel):
    """Response model for text ingestion"""
    health_record_id: str = Field(..., description="Created health record ID")
    message: str = Field(..., description="Success message")
    content_length: int = Field(..., description="Length of processed content")

class HealthRecordResponse(BaseModel):
    """Response model for health record data"""
    id: str
    title: str
    record_type: str
    status: str
    created_at: str
    file_count: int
    has_summary: bool

class BatchStatus(BaseModel):
    """Status of a batch processing operation"""
    batch_id: str
    status: ProcessingStatus
    total_files: int
    processed_files: int
    failed_files: int
    created_at: str
    updated_at: str
    error_messages: List[str] = Field(default_factory=list)