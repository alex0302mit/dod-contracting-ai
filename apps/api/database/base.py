"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dod_procurement")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 20))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 10))

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Usage in FastAPI endpoints:
        def my_endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    from backend.models import (
        User, ProcurementProject, ProcurementPhase, ProcurementStep,
        ProjectPermission, Notification, AuditLog,
        DocumentChecklistTemplate, ProjectDocument, DocumentUpload, DocumentApproval,
        AgentFeedback, DocumentContentVersion, GenerationReasoning,
        Organization, OrganizationMember, CrossOrgShare, ProjectActivity
    )
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")
