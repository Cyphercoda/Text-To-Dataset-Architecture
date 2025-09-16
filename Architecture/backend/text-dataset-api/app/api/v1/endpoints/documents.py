"""
Document management API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc

from app.core.database import get_db
from app.core.security import require_authentication
from app.models.document import Document, ProcessingJob, Dataset, AnalysisResult
from app.services.document.document_service import document_service
from app.services.processing.text_processor import text_processor
from app.services.storage.s3_service import s3_service
from app.workers.tasks.document_tasks import process_document, batch_process_documents
from app.workers.tasks.processing_tasks import generate_dataset, analyze_text_patterns
from app.api.websocket.manager import websocket_manager
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, ProcessingJobResponse,
    DatasetResponse, AnalysisResultResponse, DocumentUploadResponse,
    ProcessingOptionsRequest, DatasetGenerationRequest, AnalysisRequest,
    MessageResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    processing_options: Optional[str] = Form(None),
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new document for processing
    
    - **file**: Document file (PDF, DOCX, TXT)
    - **title**: Optional document title
    - **description**: Optional document description
    - **tags**: Optional comma-separated tags
    - **auto_process**: Whether to automatically start processing
    - **processing_options**: JSON string of processing options
    """
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Validate file size (max 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large (max 50MB)"
            )
        
        # Process tags
        tag_list = [tag.strip() for tag in tags.split(',')] if tags else []
        
        # Process processing options
        processing_opts = {}
        if processing_options:
            try:
                import json
                processing_opts = json.loads(processing_options)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid processing options JSON"
                )
        
        # Upload document
        document = await document_service.upload_document(
            db=db,
            user_id=UUID(current_user_id),
            file=file,
            title=title,
            description=description,
            tags=tag_list
        )
        
        response_data = DocumentUploadResponse(
            document=DocumentResponse.from_orm(document),
            message="Document uploaded successfully"
        )
        
        # Start processing if requested
        if auto_process:
            job = await document_service.create_processing_job(
                db=db,
                user_id=UUID(current_user_id),
                document_id=document.id,
                processing_options=processing_opts
            )
            
            # Queue processing task
            task = process_document.apply_async(
                args=[str(job.id), str(document.id), current_user_id],
                kwargs={"processing_options": processing_opts}
            )
            
            response_data.processing_job = ProcessingJobResponse.from_orm(job)
            response_data.message += " Processing started."
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("uploaded_at"),
    sort_order: str = Query("desc"),
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's documents with filtering and pagination
    
    - **skip**: Number of documents to skip
    - **limit**: Maximum number of documents to return
    - **search**: Search term for title/description
    - **tags**: Comma-separated tags to filter by
    - **status**: Document status filter
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order (asc/desc)
    """
    try:
        documents, total = await document_service.list_documents(
            db=db,
            user_id=UUID(current_user_id),
            skip=skip,
            limit=limit,
            search=search,
            tags=tags.split(',') if tags else None,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            skip=skip,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID"""
    try:
        document = await document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=UUID(current_user_id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse.from_orm(document)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata"""
    try:
        document = await document_service.update_document(
            db=db,
            document_id=document_id,
            user_id=UUID(current_user_id),
            title=title,
            description=description,
            tags=tags
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse.from_orm(document)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document"
        )


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Delete document and associated files"""
    try:
        success = await document_service.delete_document(
            db=db,
            document_id=document_id,
            user_id=UUID(current_user_id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return MessageResponse(
            message="Document deleted successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/{document_id}/process", response_model=ProcessingJobResponse)
async def process_document_endpoint(
    document_id: UUID,
    options: ProcessingOptionsRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Start document processing with specified options"""
    try:
        # Check if document exists
        document = await document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=UUID(current_user_id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Create processing job
        job = await document_service.create_processing_job(
            db=db,
            user_id=UUID(current_user_id),
            document_id=document_id,
            processing_options=options.dict()
        )
        
        # Queue processing task
        task = process_document.apply_async(
            args=[str(job.id), str(document_id), current_user_id],
            kwargs={"processing_options": options.dict()}
        )
        
        return ProcessingJobResponse.from_orm(job)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start document processing"
        )


@router.post("/batch/process", response_model=List[ProcessingJobResponse])
async def batch_process_documents_endpoint(
    document_ids: List[UUID],
    options: ProcessingOptionsRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Process multiple documents in batch"""
    try:
        # Validate document ownership
        documents = await document_service.get_documents_by_ids(
            db=db,
            document_ids=document_ids,
            user_id=UUID(current_user_id)
        )
        
        if len(documents) != len(document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some documents not found or not owned by user"
            )
        
        # Create processing jobs
        jobs = []
        job_ids = []
        
        for doc in documents:
            job = await document_service.create_processing_job(
                db=db,
                user_id=UUID(current_user_id),
                document_id=doc.id,
                processing_options=options.dict()
            )
            jobs.append(job)
            job_ids.append(str(job.id))
        
        # Queue batch processing task
        task = batch_process_documents.apply_async(
            args=[job_ids, [str(doc.id) for doc in documents], current_user_id],
            kwargs={"processing_options": options.dict()}
        )
        
        return [ProcessingJobResponse.from_orm(job) for job in jobs]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start batch processing"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Download original document file"""
    try:
        document = await document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=UUID(current_user_id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Generate presigned URL for download
        download_url = s3_service.generate_presigned_url(
            bucket=document.s3_bucket,
            key=document.s3_key,
            expiration=3600  # 1 hour
        )
        
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL"
            )
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=download_url)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.get("/processing-jobs/", response_model=List[ProcessingJobResponse])
async def list_processing_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """List user's processing jobs"""
    try:
        jobs = await document_service.list_processing_jobs(
            db=db,
            user_id=UUID(current_user_id),
            skip=skip,
            limit=limit,
            status_filter=status_filter
        )
        
        return [ProcessingJobResponse.from_orm(job) for job in jobs]
    
    except Exception as e:
        logger.error(f"Processing jobs listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list processing jobs"
        )


@router.get("/processing-jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: UUID,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Get processing job status"""
    try:
        job = await document_service.get_processing_job(
            db=db,
            job_id=job_id,
            user_id=UUID(current_user_id)
        )
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found"
            )
        
        return ProcessingJobResponse.from_orm(job)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get processing job failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing job"
        )


@router.post("/datasets/generate", response_model=DatasetResponse)
async def generate_dataset_endpoint(
    request: DatasetGenerationRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Generate training dataset from documents"""
    try:
        # Validate document ownership
        documents = await document_service.get_documents_by_ids(
            db=db,
            document_ids=request.document_ids,
            user_id=UUID(current_user_id)
        )
        
        if len(documents) != len(request.document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some documents not found or not owned by user"
            )
        
        # Check if all documents are processed
        unprocessed = [doc for doc in documents if not doc.is_processed]
        if unprocessed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{len(unprocessed)} documents are not yet processed"
            )
        
        # Queue dataset generation task
        task = generate_dataset.apply_async(
            args=[[str(doc.id) for doc in documents], current_user_id, request.config.dict()]
        )
        
        # Create placeholder dataset record
        dataset = await document_service.create_dataset_placeholder(
            db=db,
            user_id=UUID(current_user_id),
            name=request.config.name,
            description=request.config.description,
            config=request.config.dict(),
            document_ids=[str(doc.id) for doc in documents]
        )
        
        return DatasetResponse.from_orm(dataset)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset"
        )


@router.get("/datasets/", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """List user's datasets"""
    try:
        datasets = await document_service.list_datasets(
            db=db,
            user_id=UUID(current_user_id),
            skip=skip,
            limit=limit
        )
        
        return [DatasetResponse.from_orm(dataset) for dataset in datasets]
    
    except Exception as e:
        logger.error(f"Dataset listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list datasets"
        )


@router.post("/analyze", response_model=AnalysisResultResponse)
async def analyze_documents(
    request: AnalysisRequest,
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Analyze patterns across multiple documents"""
    try:
        # Validate document ownership
        documents = await document_service.get_documents_by_ids(
            db=db,
            document_ids=request.document_ids,
            user_id=UUID(current_user_id)
        )
        
        if len(documents) != len(request.document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some documents not found or not owned by user"
            )
        
        # Queue analysis task
        task = analyze_text_patterns.apply_async(
            args=[[str(doc.id) for doc in documents], current_user_id, request.analysis_type]
        )
        
        # Create placeholder analysis result
        analysis = await document_service.create_analysis_placeholder(
            db=db,
            user_id=UUID(current_user_id),
            analysis_type=request.analysis_type,
            document_ids=[str(doc.id) for doc in documents]
        )
        
        return AnalysisResultResponse.from_orm(analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze documents"
        )


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user_id: str = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Get user's document analytics summary"""
    try:
        summary = await document_service.get_user_analytics_summary(
            db=db,
            user_id=UUID(current_user_id)
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Analytics summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics summary"
        )