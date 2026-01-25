"""
Document version history model for tracking content snapshots
"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.database.base import Base


class DocumentContentVersion(Base):
    """Stores version history for document content (markdown/HTML)."""
    __tablename__ = "document_content_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_document_id = Column(UUID(as_uuid=True), ForeignKey("project_documents.id", ondelete="CASCADE"), nullable=False)

    # Version info
    version_number = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False)

    # Content
    content = Column(Text, nullable=False)
    sections_json = Column(Text, nullable=True)  # JSON of section name -> content

    # Metadata
    message = Column(String(500), nullable=True)  # Commit message
    author = Column(String(255), nullable=True)  # "AI Agent" or user name

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quality
    ai_quality_score = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    # Relationships
    document = relationship("ProjectDocument", backref="content_versions")

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_document_id": str(self.project_document_id),
            "version_number": self.version_number,
            "is_current": self.is_current,
            "content": self.content,
            "sections_json": self.sections_json,
            "message": self.message,
            "author": self.author,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ai_quality_score": self.ai_quality_score,
            "word_count": self.word_count,
        }
