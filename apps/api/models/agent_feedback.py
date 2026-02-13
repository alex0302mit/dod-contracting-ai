"""
Agent Feedback Model

Stores user ratings (thumbs up/down) and optional comments for AI-generated content.
Used to track agent performance and improve generation quality over time.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  # Use PostgreSQL UUID for consistency with other models
from sqlalchemy.orm import relationship, backref
from backend.database.base import Base
import uuid
from datetime import datetime


class AgentFeedback(Base):
    """
    Records user feedback for AI-generated document content.

    Each record represents a single rating event (thumbs up/down) with
    optional comment. Aggregated for agent performance metrics.
    """
    __tablename__ = "agent_feedback"

    # Primary key - UUID to match other models (ProjectDocument, User, etc.)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What was rated - UUID foreign keys to match referenced table column types
    document_id = Column(UUID(as_uuid=True), ForeignKey("project_documents.id", ondelete="CASCADE"), nullable=False)
    section_name = Column(String(255), nullable=True)  # Optional section within document
    agent_name = Column(String(255), nullable=False)  # Name of the agent that generated content

    # The rating
    rating = Column(String(20), nullable=False)  # "positive" or "negative"
    comment = Column(Text, nullable=True)  # Optional user comment

    # Context - UUID foreign keys to match referenced table column types
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id"), nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship(
        "ProjectDocument",
        backref=backref("feedback", passive_deletes=True),
        passive_deletes=True
    )
    user = relationship("User", backref="feedback_given")

    def to_dict(self):
        """Convert to dictionary for API responses.
        
        UUID fields are converted to strings for JSON serialization.
        """
        return {
            "id": str(self.id) if self.id else None,
            "document_id": str(self.document_id) if self.document_id else None,
            "section_name": self.section_name,
            "agent_name": self.agent_name,
            "rating": self.rating,
            "comment": self.comment,
            "user_id": str(self.user_id) if self.user_id else None,
            "project_id": str(self.project_id) if self.project_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<AgentFeedback(id={self.id}, agent={self.agent_name}, rating={self.rating})>"
