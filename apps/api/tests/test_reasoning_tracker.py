"""
Unit tests for ReasoningTracker integration

Tests the ReasoningTracker service for capturing AI chain-of-thought,
token usage, and RAG context during document generation.

Dependencies:
- pytest: Testing framework
- unittest.mock: For mocking LLM responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime
import time

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestReasoningTrackerCreation:
    """Test suite for ReasoningTracker initialization"""

    def test_tracker_creation(self):
        """Test that ReasoningTracker can be created"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(
            document_name="Market Research Report",
            agent_name="MarketResearchReportGeneratorAgent"
        )
        
        assert tracker is not None
        assert tracker.document_name == "Market Research Report"
        assert tracker.agent_name == "MarketResearchReportGeneratorAgent"

    def test_tracker_initial_state(self):
        """Test that tracker initializes with correct default state"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(
            document_name="Test Doc",
            agent_name="TestAgent"
        )
        
        # Check initial state
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert len(tracker.steps) == 0

    def test_tracker_timestamps(self):
        """Test that tracker records start time"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(
            document_name="Test Doc",
            agent_name="TestAgent"
        )
        
        # Tracker uses _start_time internally for duration calculation
        assert tracker._start_time is not None
        assert isinstance(tracker._start_time, float)


class TestStepRecording:
    """Test suite for step recording functionality"""

    @pytest.fixture
    def tracker(self):
        """Create a tracker instance for testing"""
        from backend.services.reasoning_tracker import ReasoningTracker
        return ReasoningTracker(document_name="Test", agent_name="TestAgent")

    def test_add_step(self, tracker):
        """Test adding a step to tracker"""
        tracker.add_step(
            step_type="context_retrieval",
            description="Retrieved 5 knowledge chunks",
            duration_ms=100
        )
        
        assert len(tracker.steps) == 1
        assert tracker.steps[0]["step_type"] == "context_retrieval"
        assert tracker.steps[0]["description"] == "Retrieved 5 knowledge chunks"

    def test_step_context_manager(self, tracker):
        """Test step context manager for timing"""
        with tracker.step("llm_generation", "Generating content"):
            # Simulate some work
            time.sleep(0.01)
        
        assert len(tracker.steps) == 1
        assert tracker.steps[0]["step_type"] == "llm_generation"
        assert tracker.steps[0]["duration_ms"] >= 10  # At least 10ms

    def test_multiple_steps(self, tracker):
        """Test recording multiple steps"""
        tracker.add_step("step1", "First step", duration_ms=50)
        tracker.add_step("step2", "Second step", duration_ms=100)
        tracker.add_step("step3", "Third step", duration_ms=75)
        
        assert len(tracker.steps) == 3

    def test_step_with_metadata(self, tracker):
        """Test step recording with additional metadata"""
        tracker.add_step(
            step_type="context_retrieval",
            description="Retrieved chunks",
            duration_ms=100,
            chunks_count=5,
            phase_filter="PRE_SOLICITATION"
        )
        
        step = tracker.steps[0]
        # Additional details are stored in a 'details' sub-dict
        assert step["details"].get("chunks_count") == 5
        assert step["details"].get("phase_filter") == "PRE_SOLICITATION"


class TestLLMCallRecording:
    """Test suite for LLM call recording"""

    @pytest.fixture
    def tracker(self):
        """Create a tracker instance for testing"""
        from backend.services.reasoning_tracker import ReasoningTracker
        return ReasoningTracker(document_name="Test", agent_name="TestAgent")

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response"""
        response = Mock()
        response.usage = Mock()
        response.usage.input_tokens = 500
        response.usage.output_tokens = 1500
        response.content = [Mock(text="Generated content")]
        response.model = "claude-sonnet-4-20250514"
        return response

    def test_record_llm_call(self, tracker, mock_llm_response):
        """Test recording LLM call with token usage"""
        tracker.record_llm_call(
            response=mock_llm_response,
            prompt="Test prompt"
        )
        
        assert tracker.total_input_tokens == 500
        assert tracker.total_output_tokens == 1500

    def test_multiple_llm_calls_accumulate_tokens(self, tracker, mock_llm_response):
        """Test that multiple LLM calls accumulate token counts"""
        tracker.record_llm_call(mock_llm_response, prompt="First call")
        tracker.record_llm_call(mock_llm_response, prompt="Second call")
        
        assert tracker.total_input_tokens == 1000  # 500 * 2
        assert tracker.total_output_tokens == 3000  # 1500 * 2

    def test_llm_call_records_response(self, tracker, mock_llm_response):
        """Test that LLM call records the full response"""
        tracker.record_llm_call(mock_llm_response, prompt="Test")
        
        # Model is set during finalize(), not on the tracker directly
        # The response text should be stored
        assert tracker.full_response is not None


class TestRAGContextRecording:
    """Test suite for RAG context recording"""

    @pytest.fixture
    def tracker(self):
        """Create a tracker instance for testing"""
        from backend.services.reasoning_tracker import ReasoningTracker
        return ReasoningTracker(document_name="Test", agent_name="TestAgent")

    def test_record_rag_chunk_ids(self, tracker):
        """Test recording RAG chunk IDs"""
        chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]
        tracker.rag_chunk_ids = chunk_ids
        
        assert tracker.rag_chunk_ids == chunk_ids
        assert len(tracker.rag_chunk_ids) == 3

    def test_record_rag_phase_filter(self, tracker):
        """Test recording RAG phase filter"""
        tracker.rag_phase_filter = "PRE_SOLICITATION"
        
        assert tracker.rag_phase_filter == "PRE_SOLICITATION"

    def test_record_rag_context_in_step(self, tracker):
        """Test recording RAG context as a step"""
        tracker.add_step(
            step_type="context_retrieval",
            description="Retrieved 5 chunks from knowledge base",
            duration_ms=200,
            chunks_count=5,
            phase_filter="SOLICITATION"
        )
        
        assert len(tracker.steps) == 1
        # Additional details are in the 'details' sub-dict
        assert tracker.steps[0]["details"]["chunks_count"] == 5


class TestFinalize:
    """Test suite for tracker finalization"""

    @pytest.fixture
    def tracker_with_data(self):
        """Create a tracker with sample data"""
        from backend.services.reasoning_tracker import ReasoningTracker
        
        tracker = ReasoningTracker(
            document_name="Market Research Report",
            agent_name="MarketResearchReportGeneratorAgent"
        )
        
        tracker.add_step("context_retrieval", "Retrieved chunks", duration_ms=100)
        tracker.add_step("llm_generation", "Generated content", duration_ms=2000)
        tracker.total_input_tokens = 500
        tracker.total_output_tokens = 1500
        tracker.rag_chunk_ids = ["chunk-1", "chunk-2"]
        # model_used is set in finalize(), not on tracker
        
        return tracker

    def test_finalize_returns_dict(self, tracker_with_data):
        """Test that finalize returns a dictionary"""
        result = tracker_with_data.finalize()
        
        assert isinstance(result, dict)

    def test_finalize_includes_document_info(self, tracker_with_data):
        """Test that finalize includes agent information"""
        result = tracker_with_data.finalize()
        
        # document_name is on tracker, agent_name is in result
        assert tracker_with_data.document_name == "Market Research Report"
        assert result["agent_name"] == "MarketResearchReportGeneratorAgent"

    def test_finalize_includes_token_counts(self, tracker_with_data):
        """Test that finalize includes token counts"""
        result = tracker_with_data.finalize()
        
        assert result["input_tokens"] == 500
        assert result["output_tokens"] == 1500

    def test_finalize_includes_steps(self, tracker_with_data):
        """Test that finalize includes reasoning steps"""
        result = tracker_with_data.finalize()
        
        assert "reasoning_steps" in result
        assert len(result["reasoning_steps"]) == 2

    def test_finalize_includes_rag_info(self, tracker_with_data):
        """Test that finalize includes RAG information"""
        result = tracker_with_data.finalize()
        
        assert "rag_chunk_ids" in result
        assert len(result["rag_chunk_ids"]) == 2

    def test_finalize_includes_model_info(self, tracker_with_data):
        """Test that finalize includes model information"""
        result = tracker_with_data.finalize()
        
        assert result["model_used"] == "claude-sonnet-4-20250514"

    def test_finalize_includes_generation_time(self, tracker_with_data):
        """Test that finalize includes generation time"""
        result = tracker_with_data.finalize()
        
        # Uses generation_time_ms instead of timestamps
        assert "generation_time_ms" in result
        assert result["generation_time_ms"] >= 0


class TestTrackerIntegrationWithBaseAgent:
    """Test suite for tracker integration with BaseAgent"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client"""
        client = Mock()
        response = Mock()
        response.usage = Mock()
        response.usage.input_tokens = 300
        response.usage.output_tokens = 800
        response.content = [Mock(text="Generated response")]
        response.model = "claude-sonnet-4-20250514"
        client.messages.create.return_value = response
        return client

    def test_get_tracker_from_task_method_exists(self):
        """Test that BaseAgent has get_tracker_from_task method"""
        from backend.agents.base_agent import BaseAgent
        
        assert hasattr(BaseAgent, 'get_tracker_from_task')

    def test_get_tracker_from_task_returns_tracker(self):
        """Test that get_tracker_from_task extracts tracker from task"""
        from backend.agents.base_agent import BaseAgent
        from backend.services.reasoning_tracker import ReasoningTracker
        
        # Create a test agent (needs API key)
        with patch('anthropic.Anthropic'):
            agent = BaseAgent(name="TestAgent", api_key="test-key")
        
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        task = {"reasoning_tracker": tracker, "requirements": "test"}
        
        extracted = agent.get_tracker_from_task(task)
        
        assert extracted is tracker

    def test_get_tracker_from_task_returns_none_if_missing(self):
        """Test that get_tracker_from_task returns None if no tracker"""
        from backend.agents.base_agent import BaseAgent
        
        with patch('anthropic.Anthropic'):
            agent = BaseAgent(name="TestAgent", api_key="test-key")
        
        task = {"requirements": "test"}
        
        extracted = agent.get_tracker_from_task(task)
        
        assert extracted is None

    @patch('anthropic.Anthropic')
    def test_call_llm_uses_instance_tracker(self, mock_anthropic, mock_anthropic_client):
        """Test that call_llm uses instance tracker if available"""
        mock_anthropic.return_value = mock_anthropic_client
        
        from backend.agents.base_agent import BaseAgent
        from backend.services.reasoning_tracker import ReasoningTracker
        
        agent = BaseAgent(name="TestAgent", api_key="test-key")
        tracker = ReasoningTracker(document_name="Test", agent_name="TestAgent")
        
        # Set instance tracker (simulating execute() behavior)
        agent._current_tracker = tracker
        
        # Call LLM without explicit tracker
        agent.call_llm("Test prompt", max_tokens=100)
        
        # Tracker should have recorded the call
        assert tracker.total_input_tokens == 300
        assert tracker.total_output_tokens == 800


class TestGenerationReasoningModel:
    """Test suite for GenerationReasoning database model"""

    def test_model_exists(self):
        """Test that GenerationReasoning model exists"""
        from backend.models.reasoning import GenerationReasoning
        
        assert GenerationReasoning is not None

    def test_model_has_required_fields(self):
        """Test that model has required fields"""
        from backend.models.reasoning import GenerationReasoning
        
        # Check for essential columns
        mapper = GenerationReasoning.__mapper__
        columns = [c.name for c in mapper.columns]
        
        assert "id" in columns
        assert "document_id" in columns
        assert "agent_name" in columns
        assert "input_tokens" in columns
        assert "output_tokens" in columns

    def test_model_has_json_fields(self):
        """Test that model has JSON fields for complex data"""
        from backend.models.reasoning import GenerationReasoning
        
        mapper = GenerationReasoning.__mapper__
        columns = [c.name for c in mapper.columns]
        
        # Should have JSON fields for structured data
        assert "reasoning_steps" in columns
        assert "rag_chunk_ids" in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
