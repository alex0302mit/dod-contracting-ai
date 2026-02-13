"""
Reasoning Tracker Service

Captures AI thought process during document generation for Chain-of-Thought display.
Provides transparency into:
- Token usage and cost
- RAG context attribution (which chunks were used)
- Step-by-step reasoning timeline with durations
- Debug data for admin inspection

Usage:
    tracker = ReasoningTracker(document_name="PWS", agent_name="PWSWriterAgent")

    with tracker.step("context_retrieval", "Searching knowledge base"):
        results = rag_service.search(...)
        tracker.record_rag_context(results, query)

    response = agent.call_llm(prompt, tracker=tracker)

    metadata = tracker.finalize()
"""
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


class ReasoningTracker:
    """
    Captures reasoning metadata during document generation.

    Provides a context manager for tracking step durations and methods
    for recording LLM calls, RAG context, and other metadata.

    Attributes:
        document_name: Name of the document being generated
        agent_name: Name of the agent performing generation
        steps: List of recorded reasoning steps
        total_input_tokens: Accumulated input token count
        total_output_tokens: Accumulated output token count
        rag_chunk_ids: List of RAG chunk IDs used
        rag_query: Query used for RAG retrieval
        rag_phase_filter: Phase filter applied during RAG
        full_prompt: Complete prompt for debug (admin only)
        full_response: Complete response for debug (admin only)
        confidence_score: Model confidence (0.0-1.0)
    """

    # Claude Sonnet 4 pricing (as of 2025)
    INPUT_COST_PER_MILLION = 3.00
    OUTPUT_COST_PER_MILLION = 15.00

    def __init__(self, document_name: str, agent_name: str):
        """
        Initialize reasoning tracker.

        Args:
            document_name: Name of the document being generated
            agent_name: Name of the agent class performing generation
        """
        self.document_name = document_name
        self.agent_name = agent_name
        self.steps: List[Dict] = []
        self._current_step: Optional[Dict] = None
        self._start_time = time.time()

        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # RAG tracking
        self.rag_chunk_ids: List[str] = []
        self.rag_query: Optional[str] = None
        self.rag_phase_filter: Optional[str] = None

        # Debug data
        self.full_prompt: Optional[str] = None
        self.full_response: Optional[str] = None

        # Confidence
        self.confidence_score: Optional[float] = None

    def step(self, step_type: str, description: str) -> '_StepContext':
        """
        Context manager for tracking a reasoning step with automatic timing.

        Args:
            step_type: Type of step (e.g., 'context_retrieval', 'llm_generation')
            description: Human-readable description of the step

        Returns:
            _StepContext that tracks duration and allows adding details

        Usage:
            with tracker.step("context_retrieval", "Searching FAR/DFARS"):
                results = rag_service.search(query)
        """
        return _StepContext(self, step_type, description)

    def add_step(
        self,
        step_type: str,
        description: str,
        duration_ms: int = 0,
        **details
    ) -> None:
        """
        Add a reasoning step manually (without using context manager).

        Args:
            step_type: Type of step (e.g., 'agent_selection', 'validation')
            description: Human-readable description
            duration_ms: Duration in milliseconds (0 if not measured)
            **details: Additional key-value details to include
        """
        self.steps.append({
            "step_type": step_type,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "details": details if details else {}
        })

    def record_llm_call(
        self,
        response: Any,
        prompt: Optional[str] = None
    ) -> None:
        """
        Capture token usage from Anthropic API response.

        Args:
            response: Anthropic API response object with usage attribute
            prompt: Optional prompt string to store for debug
        """
        if hasattr(response, 'usage'):
            self.total_input_tokens += getattr(response.usage, 'input_tokens', 0)
            self.total_output_tokens += getattr(response.usage, 'output_tokens', 0)

        if prompt:
            self.full_prompt = prompt

        if hasattr(response, 'content') and response.content:
            if hasattr(response.content[0], 'text'):
                self.full_response = response.content[0].text

    def record_rag_context(
        self,
        chunks: List[Dict],
        query: str,
        phase_filter: Optional[str] = None
    ) -> None:
        """
        Capture RAG retrieval metadata.

        Args:
            chunks: List of chunk dictionaries from RAG search
            query: The search query used
            phase_filter: Optional phase filter applied (e.g., 'pre_solicitation')
        """
        # Extract chunk IDs, handling different chunk formats
        for chunk in chunks:
            if not chunk:
                continue
            chunk_id = chunk.get("chunk_id") or chunk.get("id", "")
            if chunk_id and chunk_id not in self.rag_chunk_ids:
                self.rag_chunk_ids.append(chunk_id)

        self.rag_query = query
        self.rag_phase_filter = phase_filter

    def set_confidence(self, score: float) -> None:
        """
        Set confidence score for the generation.

        Args:
            score: Confidence value between 0.0 and 1.0
        """
        self.confidence_score = max(0.0, min(1.0, score))

    def finalize(self) -> Dict:
        """
        Return complete reasoning metadata for storage.

        Calculates total generation time and cost, then returns
        a dictionary ready for database insertion.

        Returns:
            Dictionary with all reasoning metadata
        """
        total_time_ms = int((time.time() - self._start_time) * 1000)

        # Calculate cost based on token usage
        input_cost = (self.total_input_tokens / 1_000_000) * self.INPUT_COST_PER_MILLION
        output_cost = (self.total_output_tokens / 1_000_000) * self.OUTPUT_COST_PER_MILLION

        return {
            "agent_name": self.agent_name,
            "model_used": "claude-sonnet-4-20250514",
            "temperature": 0.7,  # Default, can be passed in if needed
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost_usd": round(input_cost + output_cost, 6),
            "rag_chunks_retrieved": len(self.rag_chunk_ids),
            "rag_chunk_ids": self.rag_chunk_ids,
            "rag_query": self.rag_query,
            "rag_phase_filter": self.rag_phase_filter,
            "confidence_score": self.confidence_score,
            "generation_time_ms": total_time_ms,
            "reasoning_steps": self.steps,
            "full_prompt": self.full_prompt,
            "full_response": self.full_response,
        }


class _StepContext:
    """
    Context manager for tracking step duration automatically.

    Used by ReasoningTracker.step() to measure execution time
    of reasoning steps and record them with their duration.
    """

    def __init__(self, tracker: ReasoningTracker, step_type: str, description: str):
        """
        Initialize step context.

        Args:
            tracker: Parent ReasoningTracker instance
            step_type: Type of step being tracked
            description: Human-readable step description
        """
        self.tracker = tracker
        self.step_type = step_type
        self.description = description
        self.start_time = 0.0
        self.details: Dict = {}

    def __enter__(self) -> '_StepContext':
        """Start timing the step."""
        self.start_time = time.time()
        return self

    def __exit__(self, *args) -> None:
        """Record step with measured duration."""
        duration_ms = int((time.time() - self.start_time) * 1000)
        self.tracker.add_step(
            self.step_type,
            self.description,
            duration_ms,
            **self.details
        )

    def add_detail(self, key: str, value: Any) -> None:
        """
        Add a detail to the step record.

        Args:
            key: Detail name
            value: Detail value (should be JSON-serializable)
        """
        self.details[key] = value
