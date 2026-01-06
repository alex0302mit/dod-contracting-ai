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
# Document lineage models for tracking AI generation sources
from backend.models.lineage import (
    DocumentLineage,
    KnowledgeDocument,
    InfluenceType,
    DocumentSource
)

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
    # Lineage models
    "DocumentLineage",
    "KnowledgeDocument",
    "InfluenceType",
    "DocumentSource"
]
