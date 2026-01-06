"""
Notification model for user alerts
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from backend.database.base import Base


class Notification(Base):
    """
    Notification model for user alerts and messages.
    
    Supports various notification types including:
    - Document approvals
    - Phase transitions
    - Assignments
    - Deadline warnings
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # project_id is optional - some notifications may not be project-specific
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=True)
    # Using String for flexibility instead of enum - allows new notification types without migration
    notification_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    # JSON data field for additional context (e.g., transition_request_id, from_phase, etc.)
    data = Column(JSON, nullable=True)
    link_url = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    sent_via_email = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "link_url": self.link_url,
            "is_read": self.is_read,
            "sent_via_email": self.sent_via_email,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
