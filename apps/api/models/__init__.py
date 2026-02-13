"""
SQLAlchemy ORM models matching the front-end database schema
"""
from backend.models.user import User
from backend.models.procurement import (
    ProcurementProject,
    ProcurementPhase,
    ProcurementStep,
    ProjectPermission
)
from backend.models.document import (
    DocumentChecklistTemplate,
    ProjectDocument,
    DocumentUpload,
    DocumentApproval
)
from backend.models.notification import Notification
from backend.models.audit import AuditLog
from backend.models.agent_feedback import AgentFeedback
from backend.models.document_version import DocumentContentVersion
# Document lineage models for tracking AI generation sources
from backend.models.lineage import (
    DocumentLineage,
    KnowledgeDocument,
    InfluenceType,
    DocumentSource
)
# Generation reasoning for Chain-of-Thought display
from backend.models.reasoning import GenerationReasoning

__all__ = [
    "User",
    "ProcurementProject",
    "ProcurementPhase",
    "ProcurementStep",
    "ProjectPermission",
    "DocumentChecklistTemplate",
    "ProjectDocument",
    "DocumentUpload",
    "DocumentApproval",
    "Notification",
    "AuditLog",
    "AgentFeedback",
    "DocumentContentVersion",
    # Lineage models
    "DocumentLineage",
    "KnowledgeDocument",
    "InfluenceType",
    "DocumentSource",
    # Reasoning model for Chain-of-Thought
    "GenerationReasoning"
]
