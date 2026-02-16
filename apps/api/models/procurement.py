"""
Procurement project, phase, and step models
"""
from sqlalchemy import Column, String, DateTime, Date, Enum, Integer, Numeric, ForeignKey, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from backend.database.base import Base


class ProjectType(str, enum.Enum):
    RFP = "rfp"
    RFQ = "rfq"
    TASK_ORDER = "task_order"
    IDIQ = "idiq"
    OTHER = "other"


class ProjectStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    ON_HOLD = "on_hold"


class PhaseName(str, enum.Enum):
    PRE_SOLICITATION = "pre_solicitation"
    SOLICITATION = "solicitation"
    POST_SOLICITATION = "post_solicitation"


class PhaseStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class StepStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PermissionLevel(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


# Status for phase transition requests
class TransitionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProcurementProject(Base):
    __tablename__ = "procurement_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    estimated_value = Column(Numeric(15, 2), nullable=True)
    contracting_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    program_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    current_phase = Column(Enum(PhaseName), default=PhaseName.PRE_SOLICITATION)
    overall_status = Column(Enum(ProjectStatus), default=ProjectStatus.NOT_STARTED)
    start_date = Column(Date, nullable=True)
    target_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    phases = relationship("ProcurementPhase", back_populates="project", cascade="all, delete-orphan")
    steps = relationship("ProcurementStep", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all", passive_deletes=True)
    permissions = relationship("ProjectPermission", back_populates="project", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="projects")

    # User relationships for officer names - use foreign_keys to disambiguate multiple FKs to same table
    contracting_officer = relationship("User", foreign_keys=[contracting_officer_id])
    program_manager = relationship("User", foreign_keys=[program_manager_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type.value,
            "estimated_value": float(self.estimated_value) if self.estimated_value else None,
            "contracting_officer_id": str(self.contracting_officer_id),
            # Include nested officer object with id and name for frontend display
            "contracting_officer": {
                "id": str(self.contracting_officer.id),
                "name": self.contracting_officer.name
            } if self.contracting_officer else None,
            "program_manager_id": str(self.program_manager_id) if self.program_manager_id else None,
            # Include nested program manager object with id and name for frontend display
            "program_manager": {
                "id": str(self.program_manager.id),
                "name": self.program_manager.name
            } if self.program_manager else None,
            "current_phase": self.current_phase.value,
            "overall_status": self.overall_status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_completion_date": self.target_completion_date.isoformat() if self.target_completion_date else None,
            "actual_completion_date": self.actual_completion_date.isoformat() if self.actual_completion_date else None,
            "created_by": str(self.created_by),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "organization": {
                "id": str(self.organization.id),
                "name": self.organization.name,
                "slug": self.organization.slug,
            } if self.organization else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProcurementPhase(Base):
    __tablename__ = "procurement_phases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    phase_name = Column(Enum(PhaseName), nullable=False)
    phase_order = Column(Integer, nullable=False)
    status = Column(Enum(PhaseStatus), default=PhaseStatus.NOT_STARTED)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    estimated_duration_days = Column(Integer, default=30)
    actual_duration_days = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProcurementProject", back_populates="phases")
    steps = relationship("ProcurementStep", back_populates="phase", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "phase_name": self.phase_name.value,
            "phase_order": self.phase_order,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "estimated_duration_days": self.estimated_duration_days,
            "actual_duration_days": self.actual_duration_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProcurementStep(Base):
    __tablename__ = "procurement_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase_id = Column(UUID(as_uuid=True), ForeignKey("procurement_phases.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    step_name = Column(String, nullable=False)
    step_description = Column(Text, nullable=True)
    step_order = Column(Integer, nullable=False)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(StepStatus), default=StepStatus.NOT_STARTED)
    deadline = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    phase = relationship("ProcurementPhase", back_populates="steps")
    project = relationship("ProcurementProject", back_populates="steps")

    def to_dict(self):
        return {
            "id": str(self.id),
            "phase_id": str(self.phase_id),
            "project_id": str(self.project_id),
            "step_name": self.step_name,
            "step_description": self.step_description,
            "step_order": self.step_order,
            "assigned_user_id": str(self.assigned_user_id) if self.assigned_user_id else None,
            "status": self.status.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "notes": self.notes,
            "attachments": self.attachments,
            "requires_approval": self.requires_approval,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
        }


class ProjectPermission(Base):
    __tablename__ = "project_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    permission_level = Column(Enum(PermissionLevel), nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("ProcurementProject", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "project_id": str(self.project_id),
            "permission_level": self.permission_level.value,
            "granted_by": str(self.granted_by) if self.granted_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": str(self.user.id),
                "name": self.user.name,
                "email": self.user.email,
                "role": self.user.role.value,
            } if self.user else None,
        }


class PhaseTransitionRequest(Base):
    """
    Model for tracking phase transition requests and approvals.
    Implements the phase gate enforcement workflow where gatekeepers
    must approve transitions between procurement phases.
    """
    __tablename__ = "phase_transition_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The project this transition belongs to
    project_id = Column(UUID(as_uuid=True), ForeignKey("procurement_projects.id", ondelete="CASCADE"), nullable=False)
    # Source and target phases for the transition
    from_phase = Column(Enum(PhaseName), nullable=False)
    to_phase = Column(Enum(PhaseName), nullable=False)
    # User who requested the transition
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    # Gatekeeper who will approve/reject (CO or Source Selection Authority)
    gatekeeper_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Status of the transition request
    status = Column(Enum(TransitionStatus), default=TransitionStatus.PENDING)
    # JSON field storing validation check results at time of request
    validation_results = Column(JSON, nullable=True)
    # Gatekeeper's comments when approving/rejecting
    gatekeeper_comments = Column(Text, nullable=True)
    # Timestamp when approved/rejected
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProcurementProject")
    requester = relationship("User", foreign_keys=[requested_by])
    gatekeeper = relationship("User", foreign_keys=[gatekeeper_id])

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "requested_by": str(self.requested_by),
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "gatekeeper_id": str(self.gatekeeper_id) if self.gatekeeper_id else None,
            "status": self.status.value,
            "validation_results": self.validation_results,
            "gatekeeper_comments": self.gatekeeper_comments,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            # Include nested objects for display
            "requester": {
                "id": str(self.requester.id),
                "name": self.requester.name
            } if self.requester else None,
            "gatekeeper": {
                "id": str(self.gatekeeper.id),
                "name": self.gatekeeper.name
            } if self.gatekeeper else None,
            "project": {
                "id": str(self.project.id),
                "name": self.project.name
            } if self.project else None,
        }
