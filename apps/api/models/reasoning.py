"""
Generation Reasoning Model for Chain-of-Thought Display

Stores reasoning metadata for AI document generation, including:
- Token usage and cost tracking
- RAG context attribution
- Step-by-step reasoning timeline
- Debug data for admins (raw prompts/responses)

This model enables transparency into how AI-generated content was created
and what sources influenced the generation.
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import uuid

from backend.database.base import Base


class GenerationReasoning(Base):
    """
    Stores reasoning metadata for AI document generation.

    Each record represents one generation event for a document, capturing:
    - Which agent generated the content
    - Token usage and cost
    - Which RAG chunks were retrieved and used
    - Step-by-step reasoning timeline with durations
    - Debug data (full prompts/responses) for admin inspection

    Attributes:
        id: Unique identifier for this reasoning record
        document_id: Reference to the generated ProjectDocument
        agent_name: Name of the agent that generated the content
        model_used: LLM model identifier (e.g., claude-sonnet-4-20250514)
        temperature: Sampling temperature used
        input_tokens: Total input tokens consumed
        output_tokens: Total output tokens generated
        total_cost_usd: Estimated cost in USD
        rag_chunks_retrieved: Number of RAG chunks retrieved
        rag_chunk_ids: JSON array of chunk IDs used
        rag_query: The query used for RAG retrieval
        rag_phase_filter: Phase filter applied during RAG search
        confidence_score: Model's confidence in the output (0.0-1.0)
        generation_time_ms: Total generation time in milliseconds
        reasoning_steps: JSON array of step objects with timing
        full_prompt: Complete prompt sent to LLM (admin debug only)
        full_response: Complete response from LLM (admin debug only)
        created_at: Timestamp when this record was created
    """
    __tablename__ = "generation_reasoning"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to the generated document
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("project_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Agent information
    agent_name = Column(String(100), nullable=False)
    model_used = Column(String(100), default="claude-sonnet-4-20250514")
    temperature = Column(Float, default=0.3)

    # Token usage tracking
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # RAG context attribution
    rag_chunks_retrieved = Column(Integer, default=0)
    rag_chunk_ids = Column(JSON, default=list)  # ["chunk_id_1", "chunk_id_2", ...]
    rag_query = Column(Text, nullable=True)
    rag_phase_filter = Column(String(50), nullable=True)

    # Confidence and timing
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0
    generation_time_ms = Column(Integer, default=0)

    # Reasoning steps timeline (JSON array)
    # Format: [{"step_type": "context_retrieval", "description": "...",
    #           "timestamp": "...", "duration_ms": 150, "details": {...}}]
    reasoning_steps = Column(JSON, default=list)

    # Debug data (only returned to admins)
    full_prompt = Column(Text, nullable=True)
    full_response = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to ProjectDocument
    document = relationship(
        "ProjectDocument",
        backref=backref("reasoning_records", passive_deletes=True),
        passive_deletes=True
    )

    def to_dict(self, include_debug: bool = False) -> dict:
        """
        Convert reasoning record to dictionary for API responses.

        Args:
            include_debug: If True, include full_prompt and full_response.
                          Should only be True for admin users.

        Returns:
            Dictionary representation of the reasoning record
        """
        result = {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "agent_name": self.agent_name,
            "model_used": self.model_used,
            "temperature": self.temperature,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "rag_chunks_retrieved": self.rag_chunks_retrieved,
            "rag_chunk_ids": self.rag_chunk_ids or [],
            "rag_query": self.rag_query,
            "rag_phase_filter": self.rag_phase_filter,
            "confidence_score": self.confidence_score,
            "generation_time_ms": self.generation_time_ms,
            "reasoning_steps": self.reasoning_steps or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Only include debug data for admin users
        if include_debug:
            result["full_prompt"] = self.full_prompt
            result["full_response"] = self.full_response

        return result
