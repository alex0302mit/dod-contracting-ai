"""
Base Task Classes for Celery

Provides:
- ProgressTask: Base class with progress tracking and WebSocket notification
- Automatic state updates to Redis
- WebSocket pub/sub for real-time frontend updates
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from celery import Task


class ProgressTask(Task):
    """
    Base task class with progress tracking and WebSocket notification.

    Features:
    - Automatic progress state updates
    - WebSocket notification via Redis pub/sub
    - Graceful error handling with state preservation
    - Task result caching

    Usage:
        @celery_app.task(base=ProgressTask, bind=True)
        def my_task(self, ...):
            self.update_progress(25, "Processing...")
            ...
            self.update_progress(100, "Complete!")
    """

    # Don't track by default (override in specific tasks)
    track_started = True
    ignore_result = False

    def __init__(self):
        super().__init__()
        self._cache_service = None
        self._project_id = None

    @property
    def cache_service(self):
        """Lazy load cache service."""
        if self._cache_service is None:
            try:
                from backend.services.cache_service import get_cache_service
                self._cache_service = get_cache_service()
            except ImportError:
                pass
        return self._cache_service

    def update_progress(
        self,
        progress: int,
        message: str,
        project_id: Optional[str] = None,
        extra_data: Optional[Dict] = None
    ) -> None:
        """
        Update task progress and notify via WebSocket.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
            project_id: Project ID for WebSocket routing
            extra_data: Additional data to include in status
        """
        # Store project_id for later use
        if project_id:
            self._project_id = project_id

        # Build state meta
        meta = {
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat(),
            "task_id": self.request.id,
        }

        if extra_data:
            meta.update(extra_data)

        # Update Celery task state
        self.update_state(state="PROGRESS", meta=meta)

        # Send WebSocket notification via Redis pub/sub
        self._send_ws_notification(
            project_id=self._project_id,
            event_type="progress",
            data=meta
        )

    def send_started(
        self,
        project_id: str,
        document_type: str,
        document_id: Optional[str] = None
    ) -> None:
        """
        Send generation started notification.

        Args:
            project_id: Project ID
            document_type: Type of document being generated
            document_id: Optional document ID
        """
        self._project_id = project_id

        data = {
            "task_id": self.request.id,
            "document_type": document_type,
            "document_id": document_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._send_ws_notification(
            project_id=project_id,
            event_type="generation_started",
            data=data
        )

    def send_completed(
        self,
        project_id: str,
        document_type: str,
        document_id: Optional[str] = None,
        document_url: Optional[str] = None
    ) -> None:
        """
        Send generation completed notification.

        Args:
            project_id: Project ID
            document_type: Type of document generated
            document_id: Optional document ID
            document_url: Optional URL to generated document
        """
        data = {
            "task_id": self.request.id,
            "document_type": document_type,
            "document_id": document_id,
            "document_url": document_url,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._send_ws_notification(
            project_id=project_id,
            event_type="generation_complete",
            data=data
        )

    def send_error(
        self,
        project_id: str,
        error_message: str,
        document_id: Optional[str] = None
    ) -> None:
        """
        Send error notification.

        Args:
            project_id: Project ID
            error_message: Error message
            document_id: Optional document ID
        """
        data = {
            "task_id": self.request.id,
            "error": error_message,
            "document_id": document_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._send_ws_notification(
            project_id=project_id,
            event_type="error",
            data=data
        )

    def _send_ws_notification(
        self,
        project_id: Optional[str],
        event_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send WebSocket notification via Redis pub/sub.

        This allows Celery workers to communicate with the FastAPI
        WebSocket manager through Redis.

        Args:
            project_id: Project ID for routing
            event_type: Type of event (progress, generation_started, etc.)
            data: Event data

        Returns:
            True if published successfully
        """
        if not project_id:
            return False

        cache = self.cache_service
        if not cache or not cache.is_connected:
            return False

        try:
            message = {
                "type": event_type,
                **data
            }

            return cache.publish_ws_message(project_id, message)

        except Exception as e:
            print(f"Failed to send WS notification: {e}")
            return False

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        if self._project_id:
            # Send completion notification
            self._send_ws_notification(
                project_id=self._project_id,
                event_type="task_complete",
                data={
                    "task_id": task_id,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        if self._project_id:
            self.send_error(
                project_id=self._project_id,
                error_message=str(exc)
            )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        if self._project_id:
            self._send_ws_notification(
                project_id=self._project_id,
                event_type="task_retry",
                data={
                    "task_id": task_id,
                    "error": str(exc),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )


class QualityTask(ProgressTask):
    """
    Base task for quality analysis operations.

    Extends ProgressTask with quality-specific defaults.
    """

    # Quality tasks are faster, allow more concurrency
    rate_limit = "30/m"
    soft_time_limit = 60  # 1 minute soft limit
    time_limit = 120  # 2 minute hard limit


class GenerationTask(ProgressTask):
    """
    Base task for document generation operations.

    Extends ProgressTask with generation-specific defaults
    and retry configuration.
    """

    # Generation tasks take longer
    rate_limit = "10/m"
    soft_time_limit = 300  # 5 minutes soft limit
    time_limit = 600  # 10 minutes hard limit

    # Retry configuration
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True
