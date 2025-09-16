"""
Document processing tasks for background processing
"""

import os
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from celery import Task
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.models.document import Document, ProcessingJob, JobStatus, DocumentType
from app.models.user import User
from app.services.document.document_service import document_service
from app.services.storage.s3_service import s3_service
from app.services.processing.text_processor import text_processor
from app.api.websocket.manager import websocket_manager
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_document")
def process_document(
    self: Task,
    job_id: str,
    document_id: str,
    user_id: str,
    processing_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main document processing task
    
    Args:
        job_id: Processing job ID
        document_id: Document ID to process
        user_id: User ID who initiated the processing
        processing_options: Optional processing configuration
    
    Returns:
        Processing results
    """
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(ProcessingJob).filter_by(id=job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Send WebSocket update
        websocket_manager.send_processing_update(
            user_id=user_id,
            job_id=job_id,
            status="processing",
            progress=0.1,
            message="Starting document processing"
        )
        
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Download document from S3
        logger.info(f"Downloading document {document_id} from S3")
        file_content = s3_service.download_file(
            bucket=document.s3_bucket,
            key=document.s3_key
        )
        
        # Update progress
        websocket_manager.send_processing_update(
            user_id=user_id,
            job_id=job_id,
            status="processing",
            progress=0.3,
            message="Document downloaded, starting text extraction"
        )
        
        # Extract text based on document type
        if document.document_type == DocumentType.PDF:
            text_content = text_processor.extract_pdf_text(file_content)
        elif document.document_type == DocumentType.TEXT:
            text_content = file_content.decode('utf-8')
        elif document.document_type == DocumentType.DOCX:
            text_content = text_processor.extract_docx_text(file_content)
        else:
            text_content = file_content.decode('utf-8', errors='ignore')
        
        # Update progress
        websocket_manager.send_processing_update(
            user_id=user_id,
            job_id=job_id,
            status="processing",
            progress=0.5,
            message="Text extracted, performing analysis"
        )
        
        # Process text
        processing_results = text_processor.process_text(
            text=text_content,
            options=processing_options or {}
        )
        
        # Update document with processed content
        document.processed_content = processing_results.get("cleaned_text", "")
        document.word_count = processing_results.get("word_count", 0)
        document.metadata = {
            **document.metadata,
            "processing_results": processing_results
        }
        document.is_processed = True
        document.processed_at = datetime.utcnow()
        
        # Update job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 1.0
        job.result = processing_results
        
        db.commit()
        
        # Send final WebSocket update
        websocket_manager.send_processing_update(
            user_id=user_id,
            job_id=job_id,
            status="completed",
            progress=1.0,
            message="Document processing completed successfully"
        )
        
        logger.info(f"Document {document_id} processed successfully")
        
        return {
            "success": True,
            "document_id": document_id,
            "job_id": job_id,
            "results": processing_results
        }
    
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        
        # Update job status to failed
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        # Send error WebSocket update
        websocket_manager.send_processing_update(
            user_id=user_id,
            job_id=job_id,
            status="failed",
            progress=job.progress if job else 0,
            message=f"Processing failed: {str(e)}"
        )
        
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="batch_process_documents")
def batch_process_documents(
    self: Task,
    job_ids: List[str],
    document_ids: List[str],
    user_id: str,
    processing_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process multiple documents in batch
    
    Args:
        job_ids: List of processing job IDs
        document_ids: List of document IDs to process
        user_id: User ID who initiated the processing
        processing_options: Optional processing configuration
    
    Returns:
        Batch processing results
    """
    results = []
    failed = []
    
    for job_id, document_id in zip(job_ids, document_ids):
        try:
            # Process each document
            result = process_document.apply_async(
                args=[job_id, document_id, user_id],
                kwargs={"processing_options": processing_options}
            )
            results.append({
                "document_id": document_id,
                "job_id": job_id,
                "task_id": result.id
            })
        except Exception as e:
            logger.error(f"Failed to queue document {document_id}: {e}")
            failed.append({
                "document_id": document_id,
                "error": str(e)
            })
    
    return {
        "success": len(failed) == 0,
        "queued": results,
        "failed": failed,
        "total": len(document_ids)
    }


@celery_app.task(bind=True, name="extract_entities")
def extract_entities(
    self: Task,
    document_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Extract named entities from document
    
    Args:
        document_id: Document ID
        user_id: User ID
    
    Returns:
        Extracted entities
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.processed_content:
            raise ValueError(f"Document {document_id} has not been processed yet")
        
        # Extract entities
        entities = text_processor.extract_entities(document.processed_content)
        
        # Store entities in document metadata
        document.metadata = {
            **document.metadata,
            "entities": entities
        }
        db.commit()
        
        logger.info(f"Extracted {len(entities)} entities from document {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "entities": entities
        }
    
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_summary")
def generate_summary(
    self: Task,
    document_id: str,
    user_id: str,
    max_length: int = 500
) -> Dict[str, Any]:
    """
    Generate document summary
    
    Args:
        document_id: Document ID
        user_id: User ID
        max_length: Maximum summary length
    
    Returns:
        Document summary
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.processed_content:
            raise ValueError(f"Document {document_id} has not been processed yet")
        
        # Generate summary
        summary = text_processor.generate_summary(
            text=document.processed_content,
            max_length=max_length
        )
        
        # Store summary
        document.summary = summary
        document.metadata = {
            **document.metadata,
            "summary_generated_at": datetime.utcnow().isoformat()
        }
        db.commit()
        
        logger.info(f"Generated summary for document {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="classify_document")
def classify_document(
    self: Task,
    document_id: str,
    user_id: str,
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Classify document into categories
    
    Args:
        document_id: Document ID
        user_id: User ID
        categories: Optional list of allowed categories
    
    Returns:
        Classification results
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.processed_content:
            raise ValueError(f"Document {document_id} has not been processed yet")
        
        # Classify document
        classification = text_processor.classify_text(
            text=document.processed_content,
            categories=categories
        )
        
        # Store classification
        document.category = classification.get("primary_category")
        document.metadata = {
            **document.metadata,
            "classification": classification
        }
        db.commit()
        
        logger.info(f"Classified document {document_id} as {classification.get('primary_category')}")
        
        return {
            "success": True,
            "document_id": document_id,
            "classification": classification
        }
    
    except Exception as e:
        logger.error(f"Document classification failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="extract_keywords")
def extract_keywords(
    self: Task,
    document_id: str,
    user_id: str,
    num_keywords: int = 10
) -> Dict[str, Any]:
    """
    Extract keywords from document
    
    Args:
        document_id: Document ID
        user_id: User ID
        num_keywords: Number of keywords to extract
    
    Returns:
        Extracted keywords
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.processed_content:
            raise ValueError(f"Document {document_id} has not been processed yet")
        
        # Extract keywords
        keywords = text_processor.extract_keywords(
            text=document.processed_content,
            num_keywords=num_keywords
        )
        
        # Store keywords
        document.keywords = keywords
        document.metadata = {
            **document.metadata,
            "keywords_extracted_at": datetime.utcnow().isoformat()
        }
        db.commit()
        
        logger.info(f"Extracted {len(keywords)} keywords from document {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "keywords": keywords
        }
    
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="check_document_status")
def check_document_status(
    self: Task,
    job_id: str
) -> Dict[str, Any]:
    """
    Check document processing status
    
    Args:
        job_id: Processing job ID
    
    Returns:
        Job status information
    """
    db = SessionLocal()
    
    try:
        job = db.query(ProcessingJob).filter_by(id=job_id).first()
        if not job:
            return {
                "success": False,
                "error": f"Job {job_id} not found"
            }
        
        return {
            "success": True,
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "result": job.result
        }
    
    finally:
        db.close()