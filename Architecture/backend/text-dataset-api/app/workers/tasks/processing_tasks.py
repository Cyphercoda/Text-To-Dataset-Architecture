"""
Text processing and analysis tasks
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from celery import Task, group, chain
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.models.document import Document, Dataset, AnalysisResult
from app.models.analytics import AnalyticsEvent, ProcessingMetrics
from app.services.processing.nlp_processor import nlp_processor
from app.services.processing.dataset_generator import dataset_generator
from app.api.websocket.manager import websocket_manager
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_dataset")
def generate_dataset(
    self: Task,
    document_ids: List[str],
    user_id: str,
    dataset_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate training dataset from processed documents
    
    Args:
        document_ids: List of document IDs to include
        user_id: User ID who requested the dataset
        dataset_config: Dataset generation configuration
    
    Returns:
        Dataset generation results
    """
    db = SessionLocal()
    
    try:
        # Create dataset record
        dataset = Dataset(
            user_id=user_id,
            name=dataset_config.get("name", "Generated Dataset"),
            description=dataset_config.get("description", ""),
            config=dataset_config,
            status="generating"
        )
        db.add(dataset)
        db.flush()
        db.commit()
        
        # Send WebSocket update
        websocket_manager.send_to_user(user_id, {
            "type": "dataset_generation_started",
            "dataset_id": str(dataset.id),
            "progress": 0.0,
            "message": "Starting dataset generation"
        })
        
        # Get documents
        documents = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.is_processed == True
        ).all()
        
        if not documents:
            raise ValueError("No processed documents found")
        
        # Generate dataset
        dataset_results = dataset_generator.generate_from_documents(
            documents=documents,
            config=dataset_config,
            progress_callback=lambda p, msg: websocket_manager.send_to_user(user_id, {
                "type": "dataset_generation_progress",
                "dataset_id": str(dataset.id),
                "progress": p,
                "message": msg
            })
        )
        
        # Update dataset with results
        dataset.status = "completed"
        dataset.file_path = dataset_results["file_path"]
        dataset.file_size = dataset_results["file_size"]
        dataset.record_count = dataset_results["record_count"]
        dataset.schema = dataset_results["schema"]
        dataset.created_at = datetime.utcnow()
        db.commit()
        
        # Send completion update
        websocket_manager.send_to_user(user_id, {
            "type": "dataset_generation_completed",
            "dataset_id": str(dataset.id),
            "progress": 1.0,
            "message": "Dataset generation completed successfully",
            "download_url": dataset_results.get("download_url")
        })
        
        logger.info(f"Dataset generated successfully: {dataset.id}")
        
        return {
            "success": True,
            "dataset_id": str(dataset.id),
            "results": dataset_results
        }
    
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        
        # Update dataset status
        if 'dataset' in locals():
            dataset.status = "failed"
            dataset.error_message = str(e)
            db.commit()
        
        # Send error update
        websocket_manager.send_to_user(user_id, {
            "type": "dataset_generation_failed",
            "dataset_id": str(dataset.id) if 'dataset' in locals() else None,
            "error": str(e)
        })
        
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="analyze_text_patterns")
def analyze_text_patterns(
    self: Task,
    document_ids: List[str],
    user_id: str,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Analyze text patterns across multiple documents
    
    Args:
        document_ids: List of document IDs to analyze
        user_id: User ID
        analysis_type: Type of analysis to perform
    
    Returns:
        Analysis results
    """
    db = SessionLocal()
    
    try:
        # Get documents
        documents = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.is_processed == True
        ).all()
        
        if not documents:
            raise ValueError("No processed documents found")
        
        # Combine all text content
        combined_text = "\n\n".join([doc.processed_content for doc in documents])
        
        # Perform analysis
        analysis_results = nlp_processor.analyze_patterns(
            text=combined_text,
            analysis_type=analysis_type
        )
        
        # Create analysis result record
        analysis_result = AnalysisResult(
            user_id=user_id,
            analysis_type=analysis_type,
            document_ids=document_ids,
            results=analysis_results,
            created_at=datetime.utcnow()
        )
        db.add(analysis_result)
        db.commit()
        
        # Send WebSocket update
        websocket_manager.send_to_user(user_id, {
            "type": "analysis_completed",
            "analysis_id": str(analysis_result.id),
            "analysis_type": analysis_type,
            "results": analysis_results
        })
        
        logger.info(f"Pattern analysis completed for {len(documents)} documents")
        
        return {
            "success": True,
            "analysis_id": str(analysis_result.id),
            "results": analysis_results
        }
    
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="sentiment_analysis")
def sentiment_analysis(
    self: Task,
    document_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Perform sentiment analysis on document
    
    Args:
        document_id: Document ID
        user_id: User ID
    
    Returns:
        Sentiment analysis results
    """
    db = SessionLocal()
    
    try:
        # Get document
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.processed_content:
            raise ValueError(f"Document {document_id} has not been processed yet")
        
        # Perform sentiment analysis
        sentiment_results = nlp_processor.analyze_sentiment(document.processed_content)
        
        # Store results in document metadata
        document.metadata = {
            **document.metadata,
            "sentiment_analysis": sentiment_results
        }
        db.commit()
        
        logger.info(f"Sentiment analysis completed for document {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "sentiment": sentiment_results
        }
    
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="topic_modeling")
def topic_modeling(
    self: Task,
    document_ids: List[str],
    user_id: str,
    num_topics: int = 10
) -> Dict[str, Any]:
    """
    Perform topic modeling on documents
    
    Args:
        document_ids: List of document IDs
        user_id: User ID
        num_topics: Number of topics to extract
    
    Returns:
        Topic modeling results
    """
    db = SessionLocal()
    
    try:
        # Get documents
        documents = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.is_processed == True
        ).all()
        
        if not documents:
            raise ValueError("No processed documents found")
        
        # Extract texts
        texts = [doc.processed_content for doc in documents]
        doc_ids = [str(doc.id) for doc in documents]
        
        # Perform topic modeling
        topic_results = nlp_processor.extract_topics(
            texts=texts,
            num_topics=num_topics,
            doc_ids=doc_ids
        )
        
        # Store topic assignments in document metadata
        for doc, topics in zip(documents, topic_results["document_topics"]):
            doc.metadata = {
                **doc.metadata,
                "topic_modeling": {
                    "topics": topics,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        db.commit()
        
        # Create analysis result
        analysis_result = AnalysisResult(
            user_id=user_id,
            analysis_type="topic_modeling",
            document_ids=document_ids,
            results=topic_results,
            created_at=datetime.utcnow()
        )
        db.add(analysis_result)
        db.commit()
        
        logger.info(f"Topic modeling completed for {len(documents)} documents")
        
        return {
            "success": True,
            "analysis_id": str(analysis_result.id),
            "topics": topic_results
        }
    
    except Exception as e:
        logger.error(f"Topic modeling failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="similarity_analysis")
def similarity_analysis(
    self: Task,
    document_ids: List[str],
    user_id: str,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Analyze document similarities
    
    Args:
        document_ids: List of document IDs
        user_id: User ID
        threshold: Similarity threshold
    
    Returns:
        Similarity analysis results
    """
    db = SessionLocal()
    
    try:
        # Get documents
        documents = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.is_processed == True
        ).all()
        
        if not documents:
            raise ValueError("No processed documents found")
        
        # Calculate similarities
        similarity_results = nlp_processor.calculate_similarities(
            documents=[(str(doc.id), doc.processed_content) for doc in documents],
            threshold=threshold
        )
        
        # Create analysis result
        analysis_result = AnalysisResult(
            user_id=user_id,
            analysis_type="similarity_analysis",
            document_ids=document_ids,
            results=similarity_results,
            created_at=datetime.utcnow()
        )
        db.add(analysis_result)
        db.commit()
        
        logger.info(f"Similarity analysis completed for {len(documents)} documents")
        
        return {
            "success": True,
            "analysis_id": str(analysis_result.id),
            "similarities": similarity_results
        }
    
    except Exception as e:
        logger.error(f"Similarity analysis failed: {e}")
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True, name="process_pipeline")
def process_pipeline(
    self: Task,
    document_ids: List[str],
    user_id: str,
    pipeline_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a complete processing pipeline
    
    Args:
        document_ids: List of document IDs
        user_id: User ID
        pipeline_config: Pipeline configuration
    
    Returns:
        Pipeline execution results
    """
    try:
        # Create task chain based on pipeline configuration
        tasks = []
        
        # Basic processing
        if pipeline_config.get("extract_entities", False):
            for doc_id in document_ids:
                tasks.append(extract_entities.s(doc_id, user_id))
        
        # Advanced analysis
        if pipeline_config.get("sentiment_analysis", False):
            for doc_id in document_ids:
                tasks.append(sentiment_analysis.s(doc_id, user_id))
        
        if pipeline_config.get("topic_modeling", False):
            tasks.append(topic_modeling.s(document_ids, user_id, 
                        pipeline_config.get("num_topics", 10)))
        
        if pipeline_config.get("similarity_analysis", False):
            tasks.append(similarity_analysis.s(document_ids, user_id,
                        pipeline_config.get("similarity_threshold", 0.7)))
        
        # Dataset generation
        if pipeline_config.get("generate_dataset", False):
            tasks.append(generate_dataset.s(document_ids, user_id,
                        pipeline_config.get("dataset_config", {})))
        
        # Execute pipeline
        if tasks:
            job = group(tasks)
            result = job.apply_async()
            
            # Send WebSocket update
            websocket_manager.send_to_user(user_id, {
                "type": "pipeline_started",
                "pipeline_id": result.id,
                "total_tasks": len(tasks),
                "message": "Processing pipeline started"
            })
            
            return {
                "success": True,
                "pipeline_id": result.id,
                "total_tasks": len(tasks)
            }
        
        return {
            "success": True,
            "message": "No tasks to execute"
        }
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


@celery_app.task(bind=True, name="generate_insights")
def generate_insights(
    self: Task,
    analysis_result_ids: List[str],
    user_id: str
) -> Dict[str, Any]:
    """
    Generate insights from analysis results
    
    Args:
        analysis_result_ids: List of analysis result IDs
        user_id: User ID
    
    Returns:
        Generated insights
    """
    db = SessionLocal()
    
    try:
        # Get analysis results
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.id.in_(analysis_result_ids),
            AnalysisResult.user_id == user_id
        ).all()
        
        if not analysis_results:
            raise ValueError("No analysis results found")
        
        # Generate insights
        insights = nlp_processor.generate_insights([result.results for result in analysis_results])
        
        logger.info(f"Generated insights from {len(analysis_results)} analysis results")
        
        return {
            "success": True,
            "insights": insights
        }
    
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise
    
    finally:
        db.close()