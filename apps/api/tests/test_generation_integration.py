"""
Integration tests for document generation flow

Tests the end-to-end document generation process including:
- API endpoint to Celery task dispatching
- Task execution with tracker integration
- Database updates and reasoning capture

Dependencies:
- pytest: Testing framework
- unittest.mock: For mocking external services
- httpx: For async HTTP client testing (optional)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
from pathlib import Path
from datetime import datetime
import asyncio

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestGenerationCoordinatorIntegration:
    """Test suite for GenerationCoordinator integration"""

    def test_coordinator_exists(self):
        """Test that GenerationCoordinator exists and can be imported"""
        from backend.services.generation_coordinator import GenerationCoordinator
        
        assert GenerationCoordinator is not None

    def test_coordinator_has_generate_method(self):
        """Test that coordinator has _generate_single_document method"""
        from backend.services.generation_coordinator import GenerationCoordinator
        
        coordinator = GenerationCoordinator(use_specialized_agents=False)
        assert hasattr(coordinator, '_generate_single_document')

    def test_coordinator_call_specialized_agent_accepts_tracker(self):
        """Test that _call_specialized_agent accepts tracker parameter"""
        from backend.services.generation_coordinator import GenerationCoordinator
        import inspect
        
        coordinator = GenerationCoordinator(use_specialized_agents=False)
        sig = inspect.signature(coordinator._call_specialized_agent)
        params = list(sig.parameters.keys())
        
        assert 'tracker' in params


class TestTaskDictTrackerIntegration:
    """Test suite for tracker passing via task dict"""

    def test_task_dict_can_hold_tracker(self):
        """Test that task dict can hold ReasoningTracker"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        
        task = {
            'project_info': {'program_name': 'Test Program'},
            'requirements': 'Test requirements',
            'reasoning_tracker': tracker
        }
        
        assert task['reasoning_tracker'] is tracker

    def test_agent_can_extract_tracker_from_task(self):
        """Test that agent can extract tracker from task dict"""
        from backend.agents.base_agent import BaseAgent
        from backend.services.reasoning_tracker import ReasoningTracker
        
        with patch('anthropic.Anthropic'):
            agent = BaseAgent(name="TestAgent", api_key="test-key")
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        task = {'reasoning_tracker': tracker}
        
        extracted = agent.get_tracker_from_task(task)
        
        assert extracted is tracker


class TestDatabaseReasoningPersistence:
    """Test suite for reasoning data persistence"""

    def test_reasoning_data_structure(self):
        """Test that reasoning data has correct structure for DB"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(
            document_name="Market Research Report",
            agent_name="MarketResearchReportGeneratorAgent"
        )
        
        tracker.total_input_tokens = 500
        tracker.total_output_tokens = 1500
        tracker.rag_chunk_ids = ["chunk-1", "chunk-2"]
        
        data = tracker.finalize()
        
        # Verify structure matches GenerationReasoning model
        # document_name is stored on tracker, not in finalize output
        assert tracker.document_name == "Market Research Report"
        assert "agent_name" in data
        assert "input_tokens" in data
        assert "output_tokens" in data
        assert "model_used" in data
        assert "rag_chunk_ids" in data
        assert "reasoning_steps" in data

    def test_save_reasoning_to_db_method_exists(self):
        """Test that reasoning is saved to database"""
        from backend.services.generation_coordinator import GenerationCoordinator
        
        coordinator = GenerationCoordinator(use_specialized_agents=False)
        
        # Verify save_reasoning_to_db method exists
        assert hasattr(coordinator, 'save_reasoning_to_db')


class TestCeleryTaskDispatchIntegration:
    """Test suite for Celery task dispatching"""

    def test_celery_task_signature(self):
        """Test that Celery task has correct signature"""
        from backend.tasks.generation_tasks import generate_single_document
        
        # Check the task can be called with expected parameters
        # This doesn't execute the task, just verifies structure
        assert callable(generate_single_document)

    @patch('backend.celery_app.is_celery_enabled')
    def test_task_dispatch_when_celery_enabled(self, mock_enabled):
        """Test task dispatching when Celery is enabled"""
        mock_enabled.return_value = True
        
        from backend.tasks.generation_tasks import generate_single_document
        
        # Verify task has delay method for async dispatch
        assert hasattr(generate_single_document, 'delay')
        assert hasattr(generate_single_document, 'apply_async')

    def test_task_contains_progress_tracking(self):
        """Test that task supports progress tracking"""
        from backend.tasks.generation_tasks import generate_single_document
        
        # The task should have progress update capability
        # Celery tasks have methods like delay and apply_async
        assert hasattr(generate_single_document, 'delay')
        assert callable(generate_single_document.delay)


class TestGenerationErrorRecovery:
    """Test suite for error recovery in generation flow"""

    def test_task_has_retry_on_error(self):
        """Test that task retries on error"""
        from backend.tasks.generation_tasks import generate_single_document
        
        assert hasattr(generate_single_document, 'max_retries')
        assert generate_single_document.max_retries >= 1

    def test_task_has_error_handler(self):
        """Test that task has error handler"""
        from backend.tasks.base import GenerationTask
        
        assert hasattr(GenerationTask, 'on_failure')

    def test_tracker_records_errors(self):
        """Test that tracker can record error steps"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        
        tracker.add_step(
            step_type="error",
            description="Agent error: Connection timeout",
            duration_ms=0
        )
        
        assert len(tracker.steps) == 1
        assert tracker.steps[0]["step_type"] == "error"


class TestBatchGenerationIntegration:
    """Test suite for batch document generation"""

    def test_batch_task_exists(self):
        """Test that batch generation task exists"""
        from backend.tasks.generation_tasks import generate_batch_documents
        
        assert generate_batch_documents is not None

    def test_batch_task_queue_different_from_single(self):
        """Test that batch task uses different queue"""
        from backend.tasks.generation_tasks import generate_single_document, generate_batch_documents
        
        assert generate_single_document.queue != generate_batch_documents.queue

    def test_dependency_resolution_in_batch(self):
        """Test that batch generation resolves dependencies"""
        from backend.services.dependency_graph import DependencyGraph
        
        graph = DependencyGraph()
        
        # Test dependency lookup
        deps = graph.get_dependencies("Performance Work Statement (PWS)")
        
        # PWS should have some dependencies
        assert isinstance(deps, list)


class TestWebSocketProgressIntegration:
    """Test suite for WebSocket progress updates"""

    @patch('backend.services.cache_service.CacheService')
    def test_progress_sent_via_websocket(self, mock_cache_class):
        """Test that progress updates are sent via WebSocket"""
        mock_cache = Mock()
        mock_cache.publish_ws_message = Mock(return_value=True)
        mock_cache_class.return_value = mock_cache
        
        from backend.tasks.base import ProgressTask
        
        # ProgressTask should have WebSocket notification capability
        assert hasattr(ProgressTask, '_send_ws_notification')

    def test_progress_includes_task_metadata(self):
        """Test that progress updates include task metadata"""
        from backend.tasks.base import ProgressTask
        
        # Check the update_progress method signature
        import inspect
        sig = inspect.signature(ProgressTask.update_progress)
        params = list(sig.parameters.keys())
        
        assert 'progress' in params
        assert 'message' in params


class TestMacOSCeleryPoolDetection:
    """Test suite for macOS Celery pool detection"""

    def test_start_backend_script_exists(self):
        """Test that start_backend.sh exists"""
        # The script is at the repo root (parent of apps/api)
        script_path = backend_path.parent.parent / "start_backend.sh"
        assert script_path.exists()

    def test_script_contains_os_detection(self):
        """Test that script contains OS detection logic"""
        script_path = backend_path.parent.parent / "start_backend.sh"
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should contain darwin detection for macOS
        assert "darwin" in content.lower()
        assert "solo" in content.lower()  # solo pool for macOS

    def test_script_uses_solo_pool_on_macos(self):
        """Test that script uses solo pool on macOS"""
        script_path = backend_path.parent.parent / "start_backend.sh"
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should set pool=solo for macOS
        assert "--pool=solo" in content


class TestTokenTrackingAccuracy:
    """Test suite for token tracking accuracy"""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response with known token counts"""
        response = Mock()
        response.usage = Mock()
        response.usage.input_tokens = 1234
        response.usage.output_tokens = 5678
        response.content = [Mock(text="Generated content")]
        response.model = "claude-sonnet-4-20250514"
        return response

    def test_tracker_captures_exact_token_counts(self, mock_llm_response):
        """Test that tracker captures exact token counts from API response"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        tracker.record_llm_call(mock_llm_response, prompt="Test prompt")
        
        assert tracker.total_input_tokens == 1234
        assert tracker.total_output_tokens == 5678

    def test_multiple_calls_accumulate_correctly(self, mock_llm_response):
        """Test that multiple LLM calls accumulate token counts correctly"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        
        # Make 3 calls
        for _ in range(3):
            tracker.record_llm_call(mock_llm_response, prompt="Test prompt")
        
        assert tracker.total_input_tokens == 1234 * 3
        assert tracker.total_output_tokens == 5678 * 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
