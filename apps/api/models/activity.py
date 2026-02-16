"""
Project activity model for user-facing activity feeds.

Separate from AuditLog (which is compliance-focused, not user-facing).
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.database.base import Base


class ProjectActivity(Base):
    __tablename__ = "project_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    activity_type = Column(String, nullable=False)  # e.g. document_generated, phase_changed, member_added
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    activity_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("ProcurementProject", backref="activities")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "activity_type": self.activity_type,
            "title": self.title,
            "description": self.description,
            "metadata": self.activity_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": str(self.user.id),
                "name": self.user.name,
            } if self.user else None,
        }
