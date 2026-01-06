"""
Document Initializer Service

Handles initialization of project document checklists from templates.
When a new project is created, this service creates ProjectDocument records
based on DocumentChecklistTemplate entries that match the project's contract type.

This ensures users see the required document checklist immediately after project
creation, rather than having to manually create each document entry.

Dependencies:
- DocumentChecklistTemplate: Source templates for document initialization
- ProjectDocument: Target records to create
- phase_definitions.yaml: Defines which documents are required for each phase
"""
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.procurement import ProjectType, PhaseName
from backend.models.document import (
    DocumentChecklistTemplate, 
    ProjectDocument, 
    DocumentStatus,
    ApprovalRouting
)


class DocumentInitializer:
    """
    Service for initializing project document checklists from templates.
    
    Creates ProjectDocument records based on DocumentChecklistTemplate entries,
    ensuring the document checklist is populated when a project is created.
    """
    
    def initialize_project_documents(
        self,
        db: Session,
        project_id: str,
        contract_type: ProjectType,
        phase: Optional[PhaseName] = None,
        skip_existing: bool = True
    ) -> List[ProjectDocument]:
        """
        Initialize project documents from templates.
        
        Args:
            db: Database session
            project_id: UUID of the project to initialize documents for
            contract_type: Type of contract (RFP, RFQ, etc.) to filter templates
            phase: Optional phase to filter templates (e.g., only create pre-solicitation docs)
            skip_existing: If True, skip creating documents that already exist for this project
            
        Returns:
            List of created ProjectDocument records
        """
        # Build query for templates
        query = db.query(DocumentChecklistTemplate).filter(
            DocumentChecklistTemplate.contract_type == contract_type
        )
        
        # Optionally filter by phase
        if phase:
            query = query.filter(DocumentChecklistTemplate.phase == phase)
        
        # Order by display_order for consistent ordering
        templates = query.order_by(DocumentChecklistTemplate.display_order).all()
        
        if not templates:
            return []
        
        # Get existing document names for this project if skip_existing is True
        existing_names = set()
        if skip_existing:
            existing_docs = db.query(ProjectDocument.document_name).filter(
                ProjectDocument.project_id == project_id
            ).all()
            existing_names = {doc.document_name for doc in existing_docs}
        
        # Create ProjectDocument records from templates
        created_documents = []
        for template in templates:
            # Skip if document already exists
            if template.document_name in existing_names:
                continue
            
            # Calculate deadline based on template's typical_deadline_days
            deadline = None
            if template.typical_deadline_days:
                deadline = date.today() + timedelta(days=template.typical_deadline_days)
            
            # Create new ProjectDocument from template
            document = ProjectDocument(
                project_id=project_id,
                document_name=template.document_name,
                description=template.description,
                category=template.category,
                phase=template.phase,
                is_required=template.is_required,
                status=DocumentStatus.PENDING,  # All new docs start as PENDING
                deadline=deadline,
                requires_approval=template.requires_approval,
                display_order=template.display_order,
                # Use auto-CO routing by default for smart approval workflow
                approval_routing=ApprovalRouting.AUTO_CO
            )
            
            db.add(document)
            created_documents.append(document)
        
        # Commit all new documents
        if created_documents:
            db.commit()
            # Refresh to get IDs
            for doc in created_documents:
                db.refresh(doc)
        
        return created_documents
    
    def get_missing_required_documents(
        self,
        db: Session,
        project_id: str,
        contract_type: ProjectType,
        phase: Optional[PhaseName] = None
    ) -> List[str]:
        """
        Get list of required document names that don't exist for a project.
        
        Useful for displaying what documents still need to be created.
        
        Args:
            db: Database session
            project_id: UUID of the project
            contract_type: Type of contract to filter templates
            phase: Optional phase to filter by
            
        Returns:
            List of document names that are required but don't exist
        """
        # Get required templates
        query = db.query(DocumentChecklistTemplate).filter(
            DocumentChecklistTemplate.contract_type == contract_type,
            DocumentChecklistTemplate.is_required == True
        )
        
        if phase:
            query = query.filter(DocumentChecklistTemplate.phase == phase)
        
        required_templates = query.all()
        required_names = {t.document_name for t in required_templates}
        
        # Get existing documents for this project
        existing_docs = db.query(ProjectDocument.document_name).filter(
            ProjectDocument.project_id == project_id
        ).all()
        existing_names = {doc.document_name for doc in existing_docs}
        
        # Return names that are required but don't exist
        missing = required_names - existing_names
        return list(missing)


# Singleton instance for easy access
_initializer_instance: Optional[DocumentInitializer] = None


def get_document_initializer() -> DocumentInitializer:
    """
    Get singleton instance of DocumentInitializer.
    
    Returns:
        DocumentInitializer instance
    """
    global _initializer_instance
    if _initializer_instance is None:
        _initializer_instance = DocumentInitializer()
    return _initializer_instance
