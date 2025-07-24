"""
Dashboard API Routes

Provides endpoints for dashboard data including user statistics,
recent uploads, health summaries, and medical records overview.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.auth.auth_service import get_current_user, User
from ..database.client import db_client
from ..services.security.encryption import encryption_service
from ..services.security.audit import audit_service, AccessType

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Response models
class DashboardStats(BaseModel):
    totalRecords: int
    evidenceSearches: int
    summariesGenerated: int
    recentRecordsChange: int
    recentEvidenceChange: int
    recentSummariesChange: int

class RecentUpload(BaseModel):
    id: str
    filename: str
    fileType: str
    uploadedAt: str
    status: str
    recordType: str

class HealthSummaryData(BaseModel):
    id: str
    title: str
    content: str
    createdAt: str
    provider: str
    model: str
    recordsAnalyzed: int

class MedicalRecord(BaseModel):
    id: str
    title: str
    recordType: str
    createdAt: str
    status: str
    fileCount: int
    summaryAvailable: bool

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for the current user"""
    try:        
        # Get current date ranges for comparison
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Count total records for this user
        total_records = await db_client.prisma.healthrecord.count(
            where={"userId": current_user.id, "deletedAt": None}
        )
        
        # Count records from last week for comparison
        recent_records = await db_client.prisma.healthrecord.count(
            where={
                "userId": current_user.id,
                "createdAt": {"gte": week_ago},
                "deletedAt": None
            }
        )
        
        # Count summaries generated
        summaries_generated = await db_client.prisma.summary.count(
            where={
                "healthRecord": {
                    "userId": current_user.id,
                    "deletedAt": None
                }
            }
        )
        
        # Count recent summaries
        recent_summaries = await db_client.prisma.summary.count(
            where={
                "createdAt": {"gte": week_ago},
                "healthRecord": {
                    "userId": current_user.id,
                    "deletedAt": None
                }
            }
        )
        
        # Count evidence searches (from audit logs) - placeholder for now
        evidence_searches = 0  # We'll implement this when audit logging is re-enabled
        
        # Recent evidence searches - placeholder for now
        recent_evidence_searches = 0  # We'll implement this when audit logging is re-enabled
        
        return DashboardStats(
            totalRecords=total_records,
            evidenceSearches=evidence_searches,
            summariesGenerated=summaries_generated,
            recentRecordsChange=recent_records,
            recentEvidenceChange=recent_evidence_searches,
            recentSummariesChange=recent_summaries
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")

@router.get("/recent-uploads", response_model=List[RecentUpload])
async def get_recent_uploads(
    limit: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Get recent uploads for the current user"""
    try:
        # Get recent health records with document info
        records = await db_client.prisma.healthrecord.find_many(
            where={"userId": current_user.id, "deletedAt": None},
            include={"documents": True},
            order={"createdAt": "desc"},
            take=limit
        )
        
        uploads = []
        for record in records:
            # Get the first document for filename
            first_doc = record.documents[0] if record.documents else None
            filename = first_doc.filename if first_doc else record.title
            file_type = first_doc.mimeType if first_doc else "unknown"
            
            uploads.append(RecentUpload(
                id=record.id,
                filename=filename,
                fileType=file_type,
                uploadedAt=record.createdAt.isoformat(),
                status=record.status,
                recordType=record.recordType
            ))
        
        return uploads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent uploads: {str(e)}")

@router.get("/health-summary", response_model=Optional[HealthSummaryData])
async def get_health_summary(
    current_user: User = Depends(get_current_user)
):
    """Get the latest health summary for the current user"""
    try:
        # Get the most recent summary
        summary = await db_client.prisma.summary.find_first(
            where={
                "healthRecord": {
                    "userId": current_user.id,
                    "deletedAt": None
                }
            },
            order={"createdAt": "desc"}
        )
        
        if not summary:
            return None
        
        # Log access to health summary for HIPAA compliance
        try:
            await audit_service.log_access(
                user_id=current_user.id,
                health_record_id=summary.healthRecordId,
                access_type=AccessType.VIEW,
                purpose="Dashboard health summary view",
                ip_address="127.0.0.1"  # TODO: Get real IP from request
            )
        except Exception as log_error:
            # Don't fail the request if logging fails
            pass
        
        # Count records analyzed for this summary
        records_count = await db_client.prisma.healthrecord.count(
            where={
                "userId": current_user.id,
                "createdAt": {"lte": summary.createdAt},
                "deletedAt": None
            }
        )
        
        # Decrypt summary content
        try:
            decrypted_content = encryption_service.decrypt(
                {"ciphertext": summary.summaryText, "iv": summary.encryptionIv},
                purpose="health_summary"
            )
        except Exception as e:
            # If decryption fails, use a placeholder
            decrypted_content = "Summary content could not be decrypted"
        
        return HealthSummaryData(
            id=summary.id,
            title=f"Health Summary - {summary.createdAt.strftime('%B %d, %Y')}",
            content=decrypted_content,
            createdAt=summary.createdAt.isoformat(),
            provider=summary.llmProvider,
            model=summary.llmModel,
            recordsAnalyzed=records_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch health summary: {str(e)}")

@router.get("/medical-records", response_model=List[MedicalRecord])
async def get_medical_records(
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get medical records for the current user"""
    try:
        # Build query parameters
        query_params = {
            "where": {"userId": current_user.id, "deletedAt": None},
            "include": {"documents": True, "summaries": True},
            "order": {"createdAt": "desc"}
        }
        
        if limit:
            query_params["take"] = limit
        
        records = await db_client.prisma.healthrecord.find_many(**query_params)
        
        medical_records = []
        for record in records:
            # Log access to each medical record for HIPAA compliance
            try:
                await audit_service.log_access(
                    user_id=current_user.id,
                    health_record_id=record.id,
                    access_type=AccessType.VIEW,
                    purpose="Dashboard medical records list view",
                    ip_address="127.0.0.1"  # TODO: Get real IP from request
                )
            except Exception as log_error:
                # Don't fail the request if logging fails
                pass
            
            medical_records.append(MedicalRecord(
                id=record.id,
                title=record.title,
                recordType=record.recordType,
                createdAt=record.createdAt.isoformat(),
                status=record.status,
                fileCount=len(record.documents),
                summaryAvailable=len(record.summaries) > 0
            ))
        
        return medical_records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch medical records: {str(e)}")