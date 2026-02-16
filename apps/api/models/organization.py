"""
Organization models for multi-tenancy and team management.

Implements:
- Organization: hierarchical org structure with materialized path
- OrganizationMember: user-org association with roles
- CrossOrgShare: cross-organization project sharing
"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Text, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from backend.database.base import Base


class OrgRole(str, enum.Enum):
    ORG_ADMIN = "org_admin"
    MEMBER = "member"
    VIEWER = "viewer"


class SharePermission(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    # Materialized path stores ancestry as "root-id/child-id/grandchild-id"
    # Enables efficient subtree queries via LIKE 'prefix%' (works on SQLite + PostgreSQL)
    path = Column(String, nullable=False, default="", index=True)
    depth = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent = relationship("Organization", remote_side=[id], backref="children")
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("ProcurementProject", back_populates="organization")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "path": self.path,
            "depth": self.depth,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    org_role = Column(Enum(OrgRole), nullable=False, default=OrgRole.MEMBER)
    is_primary = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="organization_memberships")
    organization = relationship("Organization", back_populates="members")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "organization_id": str(self.organization_id),
            "org_role": self.org_role.value,
            "is_primary": self.is_primary,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "user": {
                "id": str(self.user.id),
                "name": self.user.name,
                "email": self.user.email,
                "role": self.user.role.value,
            } if self.user else None,
            "organization": {
                "id": str(self.organization.id),
                "name": self.organization.name,
                "slug": self.organization.slug,
            } if self.organization else None,
        }


class CrossOrgShare(Base):
    __tablename__ = "cross_org_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    source_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    target_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    permission_level = Column(Enum(SharePermission), nullable=False, default=SharePermission.VIEWER)
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("ProcurementProject", backref="cross_org_shares")
    source_org = relationship("Organization", foreign_keys=[source_org_id])
    target_org = relationship("Organization", foreign_keys=[target_org_id])
    shared_by_user = relationship("User", foreign_keys=[shared_by])

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "source_org_id": str(self.source_org_id),
            "target_org_id": str(self.target_org_id),
            "permission_level": self.permission_level.value,
            "shared_by": str(self.shared_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "source_org": {
                "id": str(self.source_org.id),
                "name": self.source_org.name,
            } if self.source_org else None,
            "target_org": {
                "id": str(self.target_org.id),
                "name": self.target_org.name,
            } if self.target_org else None,
        }
