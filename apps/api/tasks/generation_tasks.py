"""
Document Generation Celery Tasks

Background tasks for:
- Single document generation
- Batch document generation
- Quality analysis

These tasks are executed by Celery workers and communicate
progress back to the FastAPI application via Redis pub/sub.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any

from backend.celery_app import celery_app
from backend.tasks.base import GenerationTask, QualityTask


def run_async(coro):
    """
    Helper to run async code in Celery tasks.

    Celery tasks are synchronous, but our generation code is async.
    This creates a new event loop to run the coroutine.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    base=GenerationTask,
    bind=True,
    name="backend.tasks.generation_tasks.generate_single_document",
    queue="dod.generation.high",
    priority=9
)
def generate_single_document(
    self,
    task_id: str,
    document_id: str,
    project_id: str,
    assumptions: List[Dict[str, str]],
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate content for a single document.

    This task:
    1. Loads document from database
    2. Checks dependencies
    3. Generates content using appropriate agent
    4. Runs quality analysis
    5. Saves result to database
    6. Sends WebSocket notifications

    Args:
        task_id: Task tracking ID
        document_id: ID of document to generate
        project_id: Project ID
        assumptions: List of assumption dictionaries
        additional_context: Optional additional context

    Returns:
        Dict with success status, content, and metadata
    """
    from backend.database.base import SessionLocal
    from backend.models.document import ProjectDocument, GenerationStatus, DocumentStatus
    from backend.services.document_generator import get_document_generator

    db = SessionLocal()

    try:
        # Send started notification
        self.send_started(
            project_id=project_id,
            document_type="document",
            document_id=document_id
        )

        # Load document
        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            self.send_error(project_id, "Document not found", document_id)
            return {"success": False, "error": "Document not found"}

        # Update progress
        self.update_progress(
            progress=10,
            message=f"Generating {document.document_name}...",
            project_id=project_id,
            extra_data={"document_id": document_id, "document_name": document.document_name}
        )

        # Create progress callback
        def progress_callback(task):
            self.update_progress(
                progress=task.progress,
                message=task.message,
                project_id=project_id,
                extra_data={"document_id": document_id}
            )

        # Generate content
        generator = get_document_generator()
        success, content_or_error, metadata = run_async(
            generator.generate_document(
                db=db,
                document=document,
                assumptions=assumptions,
                additional_context=additional_context,
                progress_callback=progress_callback
            )
        )

        if success:
            # Save generated content
            document.generated_content = content_or_error
            document.generated_at = datetime.utcnow()
            document.generation_status = GenerationStatus.GENERATED

            if document.status == DocumentStatus.PENDING:
                document.status = DocumentStatus.UPLOADED

            # Save quality score if available
            if metadata and metadata.get("quality_analysis"):
                doc_quality = metadata["quality_analysis"].get(document.document_name, {})
                score = doc_quality.get("score", doc_quality.get("overall_score"))
                if score is not None:
                    document.ai_quality_score = int(score)

            db.commit()

            # Update progress to complete
            self.update_progress(
                progress=100,
                message="Generation complete!",
                project_id=project_id,
                extra_data={"document_id": document_id}
            )

            # Send completion notification
            self.send_completed(
                project_id=project_id,
                document_type=document.document_name,
                document_id=document_id
            )

            return {
                "success": True,
                "document_id": document_id,
                "document_name": document.document_name,
                "content": content_or_error,
                "metadata": metadata
            }

        else:
            # Generation failed
            document.generation_status = GenerationStatus.FAILED
            db.commit()

            self.send_error(
                project_id=project_id,
                error_message=content_or_error,
                document_id=document_id
            )

            return {
                "success": False,
                "document_id": document_id,
                "error": content_or_error
            }

    except Exception as e:
        import traceback
        error_msg = f"Generation failed: {str(e)}"
        print(f"Error in generate_single_document: {error_msg}")
        print(traceback.format_exc())

        # Update document status
        try:
            document = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()
            if document:
                document.generation_status = GenerationStatus.FAILED
                db.commit()
        except Exception:
            pass

        self.send_error(project_id, error_msg, document_id)

        return {
            "success": False,
            "document_id": document_id,
            "error": error_msg
        }

    finally:
        db.close()


@celery_app.task(
    base=GenerationTask,
    bind=True,
    name="backend.tasks.generation_tasks.generate_batch_documents",
    queue="dod.generation.batch",
    priority=3
)
def generate_batch_documents(
    self,
    batch_task_id: str,
    project_id: str,
    document_ids: List[str],
    assumptions: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate content for multiple documents in dependency order.

    This task:
    1. Sorts documents by dependencies
    2. Generates each document sequentially (using previous as context)
    3. Tracks progress across all documents
    4. Sends WebSocket notifications

    Args:
        batch_task_id: Batch task tracking ID
        project_id: Project ID
        document_ids: List of document IDs to generate
        assumptions: List of assumption dictionaries

    Returns:
        Dict with success status, completed docs, and any errors
    """
    from backend.database.base import SessionLocal
    from backend.models.document import ProjectDocument, GenerationStatus, DocumentStatus
    from backend.services.document_generator import get_document_generator

    db = SessionLocal()
    completed_docs = []
    failed_docs = []

    try:
        # Load documents
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(document_ids),
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            self.send_error(project_id, "No documents found", None)
            return {"success": False, "error": "No documents found"}

        # Send started notification
        self.send_started(
            project_id=project_id,
            document_type="batch",
            document_id=batch_task_id
        )

        # Sort documents by dependency order
        generator = get_document_generator()
        doc_names = [d.document_name for d in documents]
        sorted_names = generator.sort_by_dependencies(doc_names)

        # Map names back to documents
        doc_map = {d.document_name: d for d in documents}
        sorted_docs = [doc_map[name] for name in sorted_names if name in doc_map]

        total_docs = len(sorted_docs)

        # Generate each document
        for idx, document in enumerate(sorted_docs):
            try:
                progress = int(10 + (idx / total_docs) * 80)

                self.update_progress(
                    progress=progress,
                    message=f"Generating {document.document_name} ({idx + 1}/{total_docs})...",
                    project_id=project_id,
                    extra_data={
                        "current_document": document.document_name,
                        "completed": idx,
                        "total": total_docs
                    }
                )

                # Create progress callback for this document
                def doc_progress_callback(task):
                    doc_progress = int(10 + (idx / total_docs) * 80 + (task.progress / total_docs) * 0.8)
                    self.update_progress(
                        progress=doc_progress,
                        message=task.message,
                        project_id=project_id,
                        extra_data={"current_document": document.document_name}
                    )

                # Generate document
                success, content_or_error, metadata = run_async(
                    generator.generate_document(
                        db=db,
                        document=document,
                        assumptions=assumptions,
                        progress_callback=doc_progress_callback
                    )
                )

                if success:
                    # Save generated content
                    document.generated_content = content_or_error
                    document.generated_at = datetime.utcnow()
                    document.generation_status = GenerationStatus.GENERATED

                    if document.status == DocumentStatus.PENDING:
                        document.status = DocumentStatus.UPLOADED

                    # Save quality score
                    if metadata and metadata.get("quality_analysis"):
                        doc_quality = metadata["quality_analysis"].get(document.document_name, {})
                        score = doc_quality.get("score", doc_quality.get("overall_score"))
                        if score is not None:
                            document.ai_quality_score = int(score)

                    db.commit()
                    completed_docs.append({
                        "id": str(document.id),
                        "name": document.document_name
                    })

                else:
                    document.generation_status = GenerationStatus.FAILED
                    db.commit()
                    failed_docs.append({
                        "id": str(document.id),
                        "name": document.document_name,
                        "error": content_or_error
                    })

            except Exception as e:
                document.generation_status = GenerationStatus.FAILED
                db.commit()
                failed_docs.append({
                    "id": str(document.id),
                    "name": document.document_name,
                    "error": str(e)
                })

        # Update final progress
        self.update_progress(
            progress=100,
            message=f"Batch complete! {len(completed_docs)}/{total_docs} documents generated.",
            project_id=project_id,
            extra_data={
                "completed_count": len(completed_docs),
                "failed_count": len(failed_docs),
                "total": total_docs
            }
        )

        # Send completion notification
        self.send_completed(
            project_id=project_id,
            document_type="batch",
            document_id=batch_task_id
        )

        return {
            "success": len(failed_docs) == 0,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "total": total_docs
        }

    except Exception as e:
        import traceback
        error_msg = f"Batch generation failed: {str(e)}"
        print(f"Error in generate_batch_documents: {error_msg}")
        print(traceback.format_exc())

        self.send_error(project_id, error_msg, batch_task_id)

        return {
            "success": False,
            "error": error_msg,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs
        }

    finally:
        db.close()


@celery_app.task(
    base=QualityTask,
    bind=True,
    name="backend.tasks.generation_tasks.run_quality_analysis",
    queue="dod.quality",
    priority=5
)
def run_quality_analysis(
    self,
    document_id: str,
    project_id: str,
    content: str,
    document_type: str,
    assumptions: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Run quality analysis on document content.

    This task:
    1. Analyzes content using QualityAgent
    2. Updates document with quality score
    3. Sends WebSocket notification with results

    Args:
        document_id: Document ID
        project_id: Project ID
        content: Document content to analyze
        document_type: Type of document
        assumptions: Optional assumptions for context

    Returns:
        Dict with quality analysis results
    """
    import os
    from backend.database.base import SessionLocal
    from backend.models.document import ProjectDocument
    from backend.agents.quality_agent import QualityAgent

    db = SessionLocal()

    try:
        self.update_progress(
            progress=10,
            message="Starting quality analysis...",
            project_id=project_id,
            extra_data={"document_id": document_id}
        )

        # Run quality analysis
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        quality_agent = QualityAgent(api_key=api_key)

        project_info = {"assumptions": assumptions} if assumptions else {}

        self.update_progress(
            progress=50,
            message="Analyzing document quality...",
            project_id=project_id,
            extra_data={"document_id": document_id}
        )

        quality_result = quality_agent.evaluate(
            content=content,
            document_type=document_type,
            project_info=project_info
        )

        # Update document with quality score
        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if document:
            overall_score = quality_result.get("overall_score", 0)
            document.ai_quality_score = int(overall_score)
            db.commit()

        self.update_progress(
            progress=100,
            message="Quality analysis complete!",
            project_id=project_id,
            extra_data={
                "document_id": document_id,
                "quality_score": quality_result.get("overall_score", 0)
            }
        )

        # Send completion with results
        self._send_ws_notification(
            project_id=project_id,
            event_type="quality_analysis_complete",
            data={
                "document_id": document_id,
                "task_id": self.request.id,
                "quality_result": {
                    "overall_score": quality_result.get("overall_score", 0),
                    "breakdown": {
                        "hallucination": quality_result.get("detailed_checks", {}).get("hallucination", {}),
                        "vague_language": quality_result.get("detailed_checks", {}).get("vague_language", {}),
                        "citations": quality_result.get("detailed_checks", {}).get("citations", {}),
                        "compliance": quality_result.get("detailed_checks", {}).get("compliance", {}),
                        "completeness": quality_result.get("detailed_checks", {}).get("completeness", {}),
                    },
                    "analyzed_at": datetime.utcnow().isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "success": True,
            "document_id": document_id,
            "quality_result": quality_result
        }

    except Exception as e:
        import traceback
        error_msg = f"Quality analysis failed: {str(e)}"
        print(f"Error in run_quality_analysis: {error_msg}")
        print(traceback.format_exc())

        self.send_error(project_id, error_msg, document_id)

        return {
            "success": False,
            "document_id": document_id,
            "error": error_msg
        }

    finally:
        db.close()
