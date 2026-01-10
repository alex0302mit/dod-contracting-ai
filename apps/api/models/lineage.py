"""
Document Lineage Models

Tracks relationships between source documents (uploaded knowledge) and derived documents
(AI-generated content) for explainability and traceability.

This module provides:
- DocumentLineage: Tracks which source documents influenced AI-generated documents
- Supports relevance scoring based on RAG chunk usage
- Maintains chunk_ids for fine-grained traceability

Dependencies:
- SQLAlchemy ORM for database models
- ProjectDocument from document.py for foreign key relationships
"""
from sqlalchemy import Column, String, DateTime, Float, Enum, ForeignKey, Text, JSON, Integer, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from backend.database.base import Base


class InfluenceType(str, enum.Enum):
    """
    Types of influence a source document can have on a generated document.
    
    - CONTEXT: General context provided to the AI during generation
    - TEMPLATE: Used as a structural template for the output
    - REGULATION: FAR/DFARS or policy document that was referenced
    - DATA_SOURCE: Primary data source (e.g., market research, prior awards)
    - REFERENCE: Cited or referenced in the generated content
    """
    CONTEXT = "context"
    TEMPLATE = "template"
    REGULATION = "regulation"
    DATA_SOURCE = "data_source"
    REFERENCE = "reference"


class DocumentSource(str, enum.Enum):
    """
    Tracks the origin of a document.
    
    - UPLOADED: User-uploaded document (manual)
    - AI_GENERATED: Created by AI document generation
    - MANUAL: Manually created in the editor
    - IMPORTED: Imported from external system
    """
    UPLOADED = "uploaded"
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"
    IMPORTED = "imported"


class DocumentLineage(Base):
    """
    Tracks the lineage relationship between source and derived documents.
    
    When AI generates a document, this table records which source documents
    (uploaded knowledge) were used to inform the generation. This provides:
    - Explainability: Users can see what influenced AI decisions
    - Auditability: Required for DoD/FAR compliance
    - Traceability: Track document evolution over time
    
    Attributes:
        id: Unique identifier for this lineage record
        source_document_id: Reference to the source/input document (knowledge base)
        derived_document_id: Reference to the generated/output document
        influence_type: How the source influenced the output
        relevance_score: 0.0-1.0 score indicating relevance/importance
        chunk_ids_used: JSON array of RAG chunk IDs that were retrieved
        context: Additional context about why this source was used
        created_at: When this lineage was recorded
    """
    __tablename__ = "document_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source document (the uploaded knowledge document)
    source_document_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("project_documents.id", ondelete="CASCADE"), 
        nullable=True,  # Nullable because source may be external (RAG file)
        index=True
    )
    
    # Alternative: source can be a RAG filename if not in project_documents
    source_filename = Column(String(500), nullable=True)
    
    # Derived document (the AI-generated document)
    derived_document_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("project_documents.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Type of influence
    influence_type = Column(
        Enum(InfluenceType), 
        default=InfluenceType.DATA_SOURCE, 
        nullable=False
    )
    
    # Relevance score (0.0 - 1.0) based on chunk usage and similarity
    relevance_score = Column(Float, default=0.0)
    
    # RAG chunk IDs that were used from this source
    chunk_ids_used = Column(JSON, default=list)
    
    # Number of chunks from this source that were used
    chunks_used_count = Column(Integer, default=0)
    
    # Additional context or notes
    context = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source_document = relationship(
        "ProjectDocument", 
        foreign_keys=[source_document_id],
        backref="derived_documents"
    )
    derived_document = relationship(
        "ProjectDocument", 
        foreign_keys=[derived_document_id],
        backref="source_lineage"
    )

    def to_dict(self):
        """Convert lineage record to dictionary for API responses"""
        return {
            "id": str(self.id),
            "source_document_id": str(self.source_document_id) if self.source_document_id else None,
            "source_filename": self.source_filename,
            "derived_document_id": str(self.derived_document_id),
            "influence_type": self.influence_type.value if self.influence_type else None,
            "relevance_score": self.relevance_score,
            "chunk_ids_used": self.chunk_ids_used or [],
            "chunks_used_count": self.chunks_used_count,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Include source document info if loaded
            "source_document": {
                "id": str(self.source_document.id),
                "document_name": self.source_document.document_name,
                "category": self.source_document.category,
            } if self.source_document else None
        }


class KnowledgeDocument(Base):
    """
    Represents a document in the project's knowledge base (RAG-indexed).
    
    This extends the RAG file system with database tracking for:
    - Project association
    - Phase tagging
    - Purpose categorization
    - Chunk tracking for lineage
    
    Note: This table complements the RAG file storage - the actual content
    and vectors are in FAISS, this provides relational metadata.
    """
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Project association
    project_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("procurement_projects.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(BigInteger, default=0)
    file_path = Column(String(1000), nullable=True)
    
    # Categorization
    phase = Column(String(50), nullable=True)  # pre_solicitation, solicitation, post_solicitation
    purpose = Column(String(50), nullable=True)  # regulation, template, market_research, prior_award, strategy_memo
    
    # RAG indexing status
    rag_indexed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    chunk_ids = Column(JSON, default=list)  # Array of chunk IDs in vector store
    
    # Upload information
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("ProcurementProject", backref="knowledge_documents")
    uploader = relationship("User", backref="uploaded_knowledge")

    def to_dict(self):
        """Convert knowledge document to dictionary for API responses"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "phase": self.phase,
            "purpose": self.purpose,
            "rag_indexed": self.rag_indexed,
            "chunk_count": self.chunk_count,
            "chunk_ids": self.chunk_ids or [],
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None,
            "upload_date": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
