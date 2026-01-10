"""
User model for authentication and authorization
"""
from sqlalchemy import Column, String, DateTime, JSON, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from backend.database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"  # System administrator - can manage users and roles
    CONTRACTING_OFFICER = "contracting_officer"
    PROGRAM_MANAGER = "program_manager"
    APPROVER = "approver"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    department = Column(String, nullable=True)
    notification_preferences = Column(
        JSON,
        default={"email": True, "in_app": True, "deadline_days": [1, 3, 7]}
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def has_role(self, *roles):
        """Check if user has any of the specified roles"""
        return self.role in roles

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "department": self.department,
            "notification_preferences": self.notification_preferences,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
