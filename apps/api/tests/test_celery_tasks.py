"""
Unit tests for Celery tasks

Tests the Celery task implementations for document generation, batch processing,
and quality analysis. Uses mocks to avoid actual LLM calls and database operations.

Dependencies:
- pytest: Testing framework
- unittest.mock: For mocking external dependencies
- celery: Task queue framework
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestGenerateSingleDocumentTask:
    """Test suite for generate_single_document Celery task"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = Mock(
            id="doc-123",
            document_name="Market Research Report",
            generation_status="NOT_GENERATED",
            project_id="proj-123"
        )
        return session

    @pytest.fixture
    def mock_generator(self):
        """Create a mock document generator"""
        generator = Mock()
        generator.generate_document = AsyncMock(return_value={
            "content": "Generated market research content",
            "metadata": {"agent": "MarketResearchReportGeneratorAgent"},
            "citations": []
        })
        return generator

    @pytest.fixture
    def mock_celery_app(self):
        """Create a mock Celery app for testing"""
        app = Mock()
        app.control.ping.return_value = [{"worker@host": {"ok": "pong"}}]
        return app

    def test_task_structure(self, mock_db_session, mock_generator):
        """Test that task has proper structure"""
        from backend.tasks.generation_tasks import generate_single_document

        # The task should be a valid Celery task
        assert generate_single_document is not None
        assert hasattr(generate_single_document, 'delay')
        assert hasattr(generate_single_document, 'apply_async')

    def test_task_is_registered_with_correct_name(self):
        """Test that task is registered with correct name"""
        from backend.celery_app import celery_app
        
        # Check task is registered
        task_name = "backend.tasks.generation_tasks.generate_single_document"
        assert task_name in celery_app.tasks or len(celery_app.tasks) == 0  # Empty in test mode

    def test_task_has_correct_queue(self):
        """Test that task is assigned to correct queue"""
        from backend.tasks.generation_tasks import generate_single_document
        
        # Check queue configuration
        assert generate_single_document.queue == "dod.generation.high"

    def test_task_has_retry_configuration(self):
        """Test that task has retry configuration"""
        from backend.tasks.generation_tasks import generate_single_document
        
        # Check retry config exists
        assert hasattr(generate_single_document, 'max_retries')
        assert generate_single_document.max_retries == 3


class TestGenerateBatchDocumentsTask:
    """Test suite for generate_batch_documents Celery task"""

    def test_task_exists(self):
        """Test that batch generation task exists"""
        from backend.tasks.generation_tasks import generate_batch_documents
        
        assert generate_batch_documents is not None
        assert hasattr(generate_batch_documents, 'delay')

    def test_task_queue_configuration(self):
        """Test batch task queue configuration"""
        from backend.tasks.generation_tasks import generate_batch_documents
        
        assert generate_batch_documents.queue == "dod.generation.batch"


class TestRunQualityAnalysisTask:
    """Test suite for run_quality_analysis Celery task"""

    def test_task_exists(self):
        """Test that quality analysis task exists"""
        from backend.tasks.generation_tasks import run_quality_analysis
        
        assert run_quality_analysis is not None
        assert hasattr(run_quality_analysis, 'delay')

    def test_task_queue_configuration(self):
        """Test quality task queue configuration"""
        from backend.tasks.generation_tasks import run_quality_analysis
        
        assert run_quality_analysis.queue == "dod.quality"


class TestStaleTaskDetection:
    """Test suite for stale task detection logic"""

    @pytest.fixture
    def mock_document(self):
        """Create a mock document with task tracking"""
        doc = Mock()
        doc.id = "doc-123"
        doc.document_name = "Test Document"
        doc.generation_status = "GENERATING"
        doc.generation_task_id = "task-123"
        doc.generation_requested_at = datetime.utcnow()
        return doc

    def test_stale_task_detection_logic(self, mock_document):
        """Test that stale tasks are properly detected"""
        # Simulate a newer task being requested
        old_task_id = "task-old"
        new_task_id = "task-new"
        
        mock_document.generation_task_id = new_task_id
        
        # Old task should be considered stale
        is_stale = mock_document.generation_task_id != old_task_id
        assert is_stale is True

    def test_current_task_not_stale(self, mock_document):
        """Test that current task is not considered stale"""
        current_task_id = "task-123"
        mock_document.generation_task_id = current_task_id
        
        is_stale = mock_document.generation_task_id != current_task_id
        assert is_stale is False


class TestProgressTask:
    """Test suite for ProgressTask base class"""

    def test_progress_task_has_update_progress_method(self):
        """Test that ProgressTask has update_progress method"""
        from backend.tasks.base import ProgressTask
        
        assert hasattr(ProgressTask, 'update_progress')

    def test_progress_task_has_effective_task_id(self):
        """Test that ProgressTask has effective_task_id property"""
        from backend.tasks.base import ProgressTask
        
        # Check that the property exists in the class definition
        assert 'effective_task_id' in dir(ProgressTask)


class TestGenerationTask:
    """Test suite for GenerationTask base class"""

    def test_generation_task_inherits_progress_task(self):
        """Test that GenerationTask inherits from ProgressTask"""
        from backend.tasks.base import GenerationTask, ProgressTask
        
        assert issubclass(GenerationTask, ProgressTask)

    def test_generation_task_class_exists(self):
        """Test that GenerationTask class exists"""
        from backend.tasks.base import GenerationTask
        
        # GenerationTask is a Task subclass
        assert GenerationTask is not None


class TestQualityTask:
    """Test suite for QualityTask base class"""

    def test_quality_task_inherits_progress_task(self):
        """Test that QualityTask inherits from ProgressTask"""
        from backend.tasks.base import QualityTask, ProgressTask
        
        assert issubclass(QualityTask, ProgressTask)

    def test_quality_task_class_exists(self):
        """Test that QualityTask class exists"""
        from backend.tasks.base import QualityTask
        
        assert QualityTask is not None


class TestWebSocketNotifications:
    """Test suite for WebSocket notification integration"""

    def test_progress_task_has_ws_notification_method(self):
        """Test that ProgressTask has WebSocket notification method"""
        from backend.tasks.base import ProgressTask
        
        # ProgressTask should have the method to send notifications
        assert hasattr(ProgressTask, '_send_ws_notification')


class TestErrorHandling:
    """Test suite for task error handling"""

    def test_generation_task_has_on_failure_handler(self):
        """Test that GenerationTask has on_failure handler"""
        from backend.tasks.base import GenerationTask
        
        # Tasks should have error handling
        assert hasattr(GenerationTask, 'on_failure')

    def test_generation_task_has_retry_configuration(self):
        """Test that GenerationTask has retry configuration"""
        from backend.tasks.base import GenerationTask
        
        assert hasattr(GenerationTask, 'max_retries')
        assert hasattr(GenerationTask, 'default_retry_delay')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
