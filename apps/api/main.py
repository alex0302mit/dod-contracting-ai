"""
Main FastAPI application - DoD Procurement Document Generation System
"""
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, UploadFile, File, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager  # For modern FastAPI lifespan events
from pydantic import BaseModel
from datetime import datetime  # For timestamp generation in exports
import os
import uvicorn
from dotenv import load_dotenv

from backend.database.base import get_db, init_db
from backend.middleware.auth import get_current_user, authenticate_user, create_access_token, get_password_hash
from backend.models.user import User, UserRole
from backend.models.procurement import ProcurementProject, ProcurementPhase, ProcurementStep
# GenerationStatus enum needed for filtering generated documents in export
from backend.models.document import ProjectDocument, DocumentUpload, GenerationStatus
from backend.models.notification import Notification
from backend.services.websocket_manager import WebSocketManager
from backend.services.rag_service import get_rag_service, initialize_rag_service
from backend.services.generation_coordinator import get_generation_coordinator, GenerationTask
from backend.services.phase_detector import get_phase_detector
from backend.services.export_service import ExportService
from backend.services.agent_comparison_service import get_comparison_service, AgentVariant
from backend.services.document_initializer import get_document_initializer
from backend.agents.quality_agent import QualityAgent

load_dotenv()


# ============================================================================
# Lifespan Context Manager (Modern FastAPI startup/shutdown pattern)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    This is the modern replacement for @app.on_event("startup") and @app.on_event("shutdown").
    
    Startup: Initialize database and RAG service
    Shutdown: Optional cleanup (currently just logs)
    """
    # === STARTUP ===
    print("🚀 Starting DoD Procurement API...")
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    print("✅ Database initialized successfully")
    
    # Initialize RAG service
    print("🧠 Initializing RAG system...")
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            initialize_rag_service(api_key)
            print("✅ RAG system initialized successfully")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set - RAG system will not be available")
    except Exception as e:
        print(f"⚠️  Failed to initialize RAG system: {e}")
    
    print("🌐 API is ready at http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    print("🛑 Shutting down DoD Procurement API...")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="DoD Procurement Document Generation API",
    description="Backend API for AI-powered DoD procurement document generation",
    version="1.0.0",
    lifespan=lifespan  # Use modern lifespan pattern instead of on_event
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
ws_manager = WebSocketManager()

# Serve static files (uploaded documents, generated PDFs, etc.)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", tags=["Authentication"])
def register(
    email: str,
    password: str,
    name: str,
    db: Session = Depends(get_db)
):
    """Register a new user.
    
    All new users are created with 'viewer' role by default.
    An admin must upgrade their role to contracting_officer, program_manager, etc.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user - always as viewer (admins upgrade roles later)
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        role=UserRole.VIEWER  # Always viewer - admins upgrade roles
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user": new_user.to_dict()}


@app.post("/api/auth/login", tags=["Authentication"])
def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@app.get("/api/auth/me", tags=["Authentication"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict()


@app.get("/api/users", tags=["Users"])
def get_users(
    role: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active users, optionally filtered by role.
    
    Args:
        role: Optional role filter (contracting_officer, program_manager, approver, viewer)
    
    Returns list of users with id, name, email, and role.
    """
    query = db.query(User).filter(User.is_active == True)
    
    # Filter by role if specified
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
            )
    
    users = query.order_by(User.name).all()
    return {"users": [u.to_dict() for u in users]}


# ============================================================================
# Admin Endpoints - User and Role Management
# ============================================================================

@app.get("/api/admin/users", tags=["Admin"])
def admin_list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users with full details (Admin only).
    
    Returns all users regardless of active status, with role information.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [u.to_dict() for u in users]}


@app.put("/api/admin/users/{user_id}/role", tags=["Admin"])
def admin_update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user's role (Admin only).
    
    Allows admins to upgrade users from viewer to contracting_officer,
    program_manager, approver, or even admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate role
    try:
        new_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from demoting themselves (safety)
    if str(user.id) == str(current_user.id) and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )
    
    old_role = user.role.value
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"User role updated from {old_role} to {new_role.value}",
        "user": user.to_dict()
    }


@app.post("/api/admin/bootstrap", tags=["Admin"])
def bootstrap_first_admin(
    email: str,
    password: str,
    name: str,
    db: Session = Depends(get_db)
):
    """Create the first admin user (only works if no admin exists).
    
    This is a one-time setup endpoint that allows creating the first admin
    when the system has no admin users. Once an admin exists, this endpoint
    will reject all requests.
    """
    # Check if any admin already exists
    existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An admin already exists. Use the admin panel to create more admins."
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        # If user exists, upgrade them to admin
        existing_user.role = UserRole.ADMIN
        db.commit()
        db.refresh(existing_user)
        return {
            "message": "Existing user upgraded to admin",
            "user": existing_user.to_dict()
        }
    
    # Create new admin user
    hashed_password = get_password_hash(password)
    admin_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        role=UserRole.ADMIN
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return {
        "message": "First admin user created successfully",
        "user": admin_user.to_dict()
    }


@app.post("/api/admin/users", tags=["Admin"])
def admin_create_user(
    email: str,
    password: str,
    name: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user with a specific role (Admin only).
    
    Unlike the public registration endpoint, this allows admins to create
    users with any role (contracting_officer, program_manager, etc.).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with specified role
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        role=user_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": f"User created successfully with role {role}",
        "user": new_user.to_dict()
    }


@app.delete("/api/admin/users/{user_id}", tags=["Admin"])
def admin_delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (Admin only).
    
    Doesn't actually delete the user, just sets is_active to False.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.email} has been deactivated"}


@app.post("/api/admin/reset-database", tags=["Admin"])
def reset_database_for_testing(
    confirm: str = Query(..., description="Must be 'CONFIRM_RESET' to proceed"),
    db: Session = Depends(get_db)
):
    """Reset database by deleting all users, projects, and related data.
    
    WARNING: This is a destructive operation for development/testing only.
    Pass confirm='CONFIRM_RESET' to proceed.
    """
    if confirm != "CONFIRM_RESET":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must pass confirm='CONFIRM_RESET' to proceed with database reset"
        )
    
    from backend.models.procurement import ProjectPermission
    from backend.models.document import DocumentApproval
    
    try:
        # Delete in order respecting foreign key constraints
        db.query(DocumentApproval).delete()
        db.query(DocumentUpload).delete()
        db.query(ProjectDocument).delete()
        db.query(ProjectPermission).delete()
        db.query(Notification).delete()
        db.query(ProcurementStep).delete()
        db.query(ProcurementPhase).delete()
        db.query(ProcurementProject).delete()
        db.query(User).delete()
        
        db.commit()
        
        return {
            "message": "Database reset successfully. All users, projects, and related data deleted.",
            "next_step": "Run the seed script: python backend/scripts/simple_seed.py"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset database: {str(e)}"
        )


# ============================================================================
# Procurement Project Endpoints
# ============================================================================

@app.get("/api/projects", tags=["Projects"])
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects accessible to the current user"""
    # TODO: Add proper permission filtering
    projects = db.query(ProcurementProject).all()
    return {"projects": [p.to_dict() for p in projects]}


@app.post("/api/projects", tags=["Projects"])
def create_project(
    name: str,
    description: str,
    project_type: str,
    estimated_value: float = None,
    contracting_officer_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new procurement project.
    
    Args:
        contracting_officer_id: Optional ID of the contracting officer to assign.
                               Defaults to current user if they have the role.
    """
    # Verify user has permission to create projects
    if current_user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only contracting officers and program managers can create projects"
        )

    # Determine contracting officer
    # If not specified, default to current user (if they're a CO) or raise an error
    final_co_id = contracting_officer_id
    if not final_co_id:
        if current_user.role == UserRole.CONTRACTING_OFFICER:
            final_co_id = str(current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A contracting officer must be assigned to the project"
            )
    else:
        # Verify the specified CO exists and has the right role
        co_user = db.query(User).filter(User.id == contracting_officer_id).first()
        if not co_user:
            raise HTTPException(status_code=404, detail="Contracting officer not found")
        if co_user.role != UserRole.CONTRACTING_OFFICER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified user is not a contracting officer"
        )

    # Create project
    project = ProcurementProject(
        name=name,
        description=description,
        project_type=project_type,
        estimated_value=estimated_value,
        contracting_officer_id=final_co_id,
        created_by=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create default phases
    phases = [
        ProcurementPhase(
            project_id=project.id,
            phase_name="pre_solicitation",
            phase_order=1,
            estimated_duration_days=60
        ),
        ProcurementPhase(
            project_id=project.id,
            phase_name="solicitation",
            phase_order=2,
            estimated_duration_days=90
        ),
        ProcurementPhase(
            project_id=project.id,
            phase_name="post_solicitation",
            phase_order=3,
            estimated_duration_days=45
        )
    ]
    db.add_all(phases)
    db.commit()
    
    # Auto-initialize document checklist from templates
    # This creates ProjectDocument records based on DocumentChecklistTemplate entries
    # so users see the required documents immediately after project creation
    from backend.models.procurement import ProjectType as PT
    try:
        initializer = get_document_initializer()
        created_docs = initializer.initialize_project_documents(
            db=db,
            project_id=str(project.id),
            contract_type=PT(project_type)
        )
        print(f"Auto-initialized {len(created_docs)} documents for project {project.name}")
    except Exception as e:
        # Don't fail project creation if document initialization fails
        print(f"Warning: Failed to auto-initialize documents: {e}")

    return {"project": project.to_dict()}


@app.get("/api/projects/{project_id}", tags=["Projects"])
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project by ID"""
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"project": project.to_dict()}


@app.post("/api/projects/{project_id}/initialize-documents", tags=["Projects"])
def initialize_project_documents(
    project_id: str,
    phase: Optional[str] = Query(None, description="Optional phase to filter documents (pre_solicitation, solicitation, post_solicitation)"),
    force: bool = Query(False, description="If true, initialize even if documents already exist (will skip duplicates)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize document checklist for an existing project from templates.
    
    This endpoint creates ProjectDocument records based on DocumentChecklistTemplate entries
    that match the project's contract type. Useful for projects created before auto-initialization
    was implemented, or to add documents for a specific phase.
    
    Args:
        project_id: UUID of the project
        phase: Optional phase filter (pre_solicitation, solicitation, post_solicitation)
        force: If False and documents exist, returns existing documents. If True, creates missing ones.
    
    Returns:
        List of created document records and count of existing documents
    """
    from backend.models.procurement import ProjectType as PT, PhaseName
    
    # Get the project
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check existing documents
    existing_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()
    
    # If not forcing and documents exist, return info about existing docs
    if not force and existing_docs:
        return {
            "message": "Documents already initialized for this project",
            "existing_count": len(existing_docs),
            "documents": [d.to_dict() for d in existing_docs],
            "created": []
        }
    
    # Convert phase string to enum if provided
    phase_enum = None
    if phase:
        try:
            phase_enum = PhaseName(phase)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phase: {phase}. Use: pre_solicitation, solicitation, or post_solicitation"
            )
    
    # Initialize documents
    try:
        initializer = get_document_initializer()
        created_docs = initializer.initialize_project_documents(
            db=db,
            project_id=str(project.id),
            contract_type=PT(project.project_type.value),
            phase=phase_enum,
            skip_existing=True  # Always skip existing to prevent duplicates
        )
        
        return {
            "message": f"Successfully initialized {len(created_docs)} documents",
            "existing_count": len(existing_docs),
            "created_count": len(created_docs),
            "created": [d.to_dict() for d in created_docs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize documents: {str(e)}")


@app.delete("/api/projects/{project_id}", tags=["Projects"])
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a procurement project and all related data.
    
    Only contracting officers and program managers can delete projects.
    Cascades deletion to phases, steps, documents, and permissions.
    """
    # Verify user has permission to delete projects
    if current_user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only contracting officers and program managers can delete projects"
        )
    
    # Find the project
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Optional: Verify user is associated with this project (owns it or is assigned)
    is_owner = str(project.contracting_officer_id) == str(current_user.id)
    is_pm = project.program_manager_id and str(project.program_manager_id) == str(current_user.id)
    is_creator = str(project.created_by) == str(current_user.id)
    
    if not (is_owner or is_pm or is_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete projects you own or are assigned to"
        )
    
    project_name = project.name
    
    # Delete the project (cascades to phases, steps, documents, permissions)
    db.delete(project)
    db.commit()
    
    return {"message": f"Project '{project_name}' deleted successfully"}


# Pydantic model for project updates - accepts JSON body
from pydantic import BaseModel
from typing import Optional

class ProjectUpdateRequest(BaseModel):
    """Request body for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    estimated_value: Optional[float] = None
    overall_status: Optional[str] = None
    current_phase: Optional[str] = None
    contracting_officer_id: Optional[str] = None
    program_manager_id: Optional[str] = None
    start_date: Optional[str] = None
    target_completion_date: Optional[str] = None


@app.put("/api/projects/{project_id}", tags=["Projects"])
def update_project(
    project_id: str,
    updates: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a procurement project.
    
    Allows updating project details and assigning/reassigning officers.
    Only contracting officers and program managers can update projects.
    Accepts JSON body with optional fields to update.
    """
    # Verify user has permission to update projects
    if current_user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only contracting officers and program managers can update projects"
        )
    
    # Find the project
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields if provided in the request body
    if updates.name is not None:
        project.name = updates.name
    if updates.description is not None:
        project.description = updates.description
    if updates.project_type is not None:
        from backend.models.procurement import ProjectType
        project.project_type = ProjectType(updates.project_type)
    if updates.estimated_value is not None:
        project.estimated_value = updates.estimated_value
    if updates.overall_status is not None:
        from backend.models.procurement import ProjectStatus
        project.overall_status = ProjectStatus(updates.overall_status)
    if updates.current_phase is not None:
        from backend.models.procurement import PhaseName
        project.current_phase = PhaseName(updates.current_phase)
    if updates.start_date is not None:
        from datetime import datetime
        project.start_date = datetime.strptime(updates.start_date, "%Y-%m-%d").date()
    if updates.target_completion_date is not None:
        from datetime import datetime
        project.target_completion_date = datetime.strptime(updates.target_completion_date, "%Y-%m-%d").date()
    
    # Handle contracting officer assignment
    if updates.contracting_officer_id is not None:
        # Verify the user exists and is a contracting officer
        new_co = db.query(User).filter(User.id == updates.contracting_officer_id).first()
        if not new_co:
            raise HTTPException(status_code=404, detail="Contracting officer not found")
        if new_co.role != UserRole.CONTRACTING_OFFICER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have contracting_officer role"
            )
        project.contracting_officer_id = updates.contracting_officer_id
    
    # Handle program manager assignment
    if updates.program_manager_id is not None:
        if updates.program_manager_id == "":
            # Allow unsetting program manager
            project.program_manager_id = None
        else:
            # Verify the user exists and is a program manager
            new_pm = db.query(User).filter(User.id == updates.program_manager_id).first()
            if not new_pm:
                raise HTTPException(status_code=404, detail="Program manager not found")
            if new_pm.role != UserRole.PROGRAM_MANAGER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User must have program_manager role"
                )
            project.program_manager_id = updates.program_manager_id
    
    db.commit()
    db.refresh(project)
    
    return {"message": "Project updated successfully", "project": project.to_dict()}


@app.get("/api/projects/{project_id}/phases", tags=["Projects"])
def get_project_phases(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all phases for a project"""
    phases = db.query(ProcurementPhase).filter(
        ProcurementPhase.project_id == project_id
    ).order_by(ProcurementPhase.phase_order).all()

    return {"phases": [p.to_dict() for p in phases]}


@app.get("/api/projects/{project_id}/documents", tags=["Documents"])
def get_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents for a project"""
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(ProjectDocument.display_order).all()

    return {"documents": [d.to_dict() for d in documents]}


@app.get("/api/documents/{document_id}/uploads", tags=["Documents"])
def get_document_uploads(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upload history for a document"""
    from backend.models.document import DocumentUpload

    uploads = db.query(DocumentUpload).filter(
        DocumentUpload.project_document_id == document_id
    ).order_by(DocumentUpload.version_number.desc()).all()

    # Add uploader info
    uploads_data = []
    for upload in uploads:
        upload_dict = upload.to_dict()
        uploader = db.query(User).filter(User.id == upload.uploaded_by).first()
        if uploader:
            upload_dict["uploader"] = {
                "name": uploader.name,
                "email": uploader.email
            }
        uploads_data.append(upload_dict)

    return {"uploads": uploads_data}


@app.post("/api/documents/{document_id}/upload", tags=["Documents"])
async def upload_document_file(
    document_id: str,
    file: bytes = None,
    file_name: str = "",
    notes: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file for a document (simplified version - stores metadata only)"""
    from backend.models.document import DocumentUpload

    # Verify document exists
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get next version number
    latest_upload = db.query(DocumentUpload).filter(
        DocumentUpload.project_document_id == document_id
    ).order_by(DocumentUpload.version_number.desc()).first()

    next_version = (latest_upload.version_number + 1) if latest_upload else 1

    # Mark previous versions as not current
    db.query(DocumentUpload).filter(
        DocumentUpload.project_document_id == document_id,
        DocumentUpload.is_current_version == True
    ).update({"is_current_version": False})

    # Create upload record (placeholder - real implementation would save file)
    file_path = f"/files/{document_id}_{next_version}_{file_name}" if file_name else f"/files/{document_id}_v{next_version}"

    upload = DocumentUpload(
        project_document_id=document_id,
        file_name=file_name or "document.pdf",
        file_path=file_path,
        file_size=len(file) if file else 0,
        file_type="application/pdf",
        version_number=next_version,
        uploaded_by=current_user.id,
        is_current_version=True,
        notes=notes
    )

    db.add(upload)
    db.commit()
    db.refresh(upload)

    return {"message": "Document uploaded successfully", "upload": upload.to_dict()}


@app.patch("/api/documents/{document_id}", tags=["Documents"])
def update_document(
    document_id: str,
    status: str = None,
    notes: str = None,
    deadline: str = None,
    expiration_date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project document"""
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update fields if provided
    if status:
        from backend.models.document import DocumentStatus
        document.status = DocumentStatus(status)
    if notes is not None:
        document.notes = notes
    if deadline:
        from datetime import date
        document.deadline = date.fromisoformat(deadline)
    if expiration_date:
        from datetime import date
        document.expiration_date = date.fromisoformat(expiration_date)

    db.commit()
    db.refresh(document)

    return {"message": "Document updated successfully", "document": document.to_dict()}


# ============================================================================
# AI DOCUMENT GENERATION ENDPOINTS
# ============================================================================

# Store for tracking generation tasks
document_generation_tasks: Dict[str, Dict] = {}


class DocumentGenerationRequest(BaseModel):
    """Request model for document generation"""
    assumptions: List[Dict[str, str]] = []
    additional_context: Optional[str] = None


class BatchGenerationRequest(BaseModel):
    """Request model for batch document generation"""
    document_ids: List[str]
    assumptions: List[Dict[str, str]] = []


@app.post("/api/documents/{document_id}/generate", tags=["Document Generation"])
async def generate_document_content(
    document_id: str,
    request: DocumentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI content for a single document.
    
    This endpoint:
    1. Validates user permission and document existence
    2. Checks document dependencies are met
    3. Queues background generation task
    4. Returns task_id for status polling
    
    Requires: User must have edit permission (CO, PM, Admin, or assigned user)
    """
    from backend.models.document import ProjectDocument, GenerationStatus
    from backend.services.document_generator import get_document_generator
    
    # Get document
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permission - CO, PM, Admin, or assigned user
    can_generate = False
    if current_user.role in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.ADMIN]:
        can_generate = True
    elif document.assigned_user_id and str(document.assigned_user_id) == str(current_user.id):
        can_generate = True
    
    if not can_generate:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to generate content for this document"
        )
    
    # Check if already generating
    if document.generation_status == GenerationStatus.GENERATING:
        # Check if the task is actually still running in memory
        task_exists = document.generation_task_id and document.generation_task_id in document_generation_tasks
        
        if task_exists:
            # Task is genuinely still running - reject the request
            raise HTTPException(
                status_code=400,
                detail="Document is already being generated. Please wait or cancel the current generation."
            )
        else:
            # Task not in memory - orphaned state (server restart or crash)
            # Reset status to allow new generation
            document.generation_status = GenerationStatus.NOT_GENERATED
            document.generation_task_id = None
            db.commit()
    
    # Check dependencies
    generator = get_document_generator()
    deps_met, missing_deps, available_deps = generator.check_dependencies(
        db, str(document.project_id), document.document_name
    )
    
    if not deps_met:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate: Missing required documents: {', '.join(missing_deps)}"
        )
    
    # Create task ID
    from datetime import datetime
    task_id = f"gen_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize task tracking
    document_generation_tasks[task_id] = {
        "task_id": task_id,
        "document_id": document_id,
        "document_name": document.document_name,
        "status": "pending",
        "progress": 0,
        "message": "Initializing generation...",
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None
    }
    
    # Update document status
    document.generation_status = GenerationStatus.GENERATING
    document.generation_task_id = task_id
    db.commit()

    # Queue background task for single document generation
    background_tasks.add_task(
        run_single_doc_generation,
        task_id,
        document_id,
        request.assumptions,
        request.additional_context
    )
    
    return {
        "message": "Generation started",
        "task_id": task_id,
        "document_id": document_id,
        "document_name": document.document_name
    }


@app.get("/api/documents/{document_id}/generation-status", tags=["Document Generation"])
async def get_document_generation_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the generation status for a document.
    
    Returns current status including progress, content (if complete), and any errors.
    """
    from backend.models.document import ProjectDocument, GenerationStatus
    
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if there's an active task
    task_info = None
    if document.generation_task_id and document.generation_task_id in document_generation_tasks:
        task_info = document_generation_tasks[document.generation_task_id]
    
    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "generation_status": document.generation_status.value.lower() if document.generation_status else "not_generated",
        "generated_content": document.generated_content,
        "generated_at": document.generated_at.isoformat() if document.generated_at else None,
        "ai_quality_score": document.ai_quality_score,
        "task_id": document.generation_task_id,
        "task_info": task_info
    }


@app.get("/api/generation-tasks/{task_id}", tags=["Document Generation"])
async def get_generation_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a specific generation task.
    
    Use this for polling during generation.
    """
    if task_id not in document_generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return document_generation_tasks[task_id]


@app.post("/api/documents/{document_id}/save-generated", tags=["Document Generation"])
def save_generated_content(
    document_id: str,
    content: str = Query(..., description="Generated content to save"),
    quality_score: Optional[int] = Query(None, description="Quality score 0-100"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save generated content to a document.
    
    This can be used when content is generated in the Live Editor and
    needs to be saved back to the document record.
    """
    from backend.models.document import ProjectDocument, GenerationStatus, DocumentStatus
    from datetime import datetime
    
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permission
    can_save = False
    if current_user.role in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.ADMIN]:
        can_save = True
    elif document.assigned_user_id and str(document.assigned_user_id) == str(current_user.id):
        can_save = True
    
    if not can_save:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Save content
    document.generated_content = content
    document.generated_at = datetime.utcnow()
    document.generation_status = GenerationStatus.GENERATED
    if quality_score is not None:
        document.ai_quality_score = quality_score
    
    # Update document status to indicate it has content
    if document.status == DocumentStatus.PENDING:
        document.status = DocumentStatus.UPLOADED
    
    db.commit()
    db.refresh(document)
    
    return {
        "message": "Content saved successfully",
        "document": document.to_dict()
    }


@app.post("/api/projects/{project_id}/generate-batch", tags=["Document Generation"])
async def generate_batch_documents(
    project_id: str,
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI content for multiple documents in dependency order.
    
    Documents are sorted by their dependencies and generated sequentially
    so that each document can use context from previously generated ones.
    """
    from backend.models.document import ProjectDocument, GenerationStatus
    from backend.services.document_generator import get_document_generator
    
    # Verify project exists
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission
    if current_user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only CO, PM, or Admin can batch generate documents")
    
    # Get documents
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.id.in_(request.document_ids),
        ProjectDocument.project_id == project_id
    ).all()
    
    if not documents:
        raise HTTPException(status_code=400, detail="No valid documents found")
    
    # Create batch task ID
    from datetime import datetime
    batch_task_id = f"batch_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize batch task tracking
    document_generation_tasks[batch_task_id] = {
        "task_id": batch_task_id,
        "project_id": project_id,
        "document_ids": request.document_ids,
        "document_names": [d.document_name for d in documents],
        "status": "pending",
        "progress": 0,
        "message": "Initializing batch generation...",
        "created_at": datetime.now().isoformat(),
        "completed_documents": [],
        "failed_documents": [],
        "current_document": None
    }
    
    # Mark documents as generating
    for doc in documents:
        doc.generation_status = GenerationStatus.GENERATING
        doc.generation_task_id = batch_task_id
    db.commit()
    
    # Queue background task for batch generation
    background_tasks.add_task(
        run_batch_generation,
        batch_task_id,
        project_id,
        request.document_ids,
        request.assumptions
    )
    
    return {
        "message": "Batch generation started",
        "task_id": batch_task_id,
        "document_count": len(documents),
        "documents": [{"id": str(d.id), "name": d.document_name} for d in documents]
    }


@app.get("/api/documents/{document_id}/check-dependencies", tags=["Document Generation"])
def check_document_dependencies(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a document's dependencies are met for generation.
    
    Returns dependency status and list of missing/available dependencies.
    """
    from backend.models.document import ProjectDocument
    from backend.services.document_generator import get_document_generator
    
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    generator = get_document_generator()
    deps_met, missing_deps, available_deps = generator.check_dependencies(
        db, str(document.project_id), document.document_name
    )
    
    estimate = generator.get_generation_estimate(document.document_name)
    
    return {
        "document_id": str(document.id),
        "document_name": document.document_name,
        "dependencies_met": deps_met,
        "missing_dependencies": missing_deps,
        "available_dependencies": available_deps,
        "can_generate": deps_met,
        "estimated_minutes": estimate.get("estimated_minutes", 2)
    }


async def run_single_doc_generation(
    task_id: str,
    document_id: str,
    assumptions: List[Dict[str, str]],
    additional_context: Optional[str] = None
):
    """Background task to generate content for a single document from checklist."""
    from backend.database.base import SessionLocal
    from backend.models.document import ProjectDocument, GenerationStatus, DocumentStatus
    from backend.services.document_generator import get_document_generator
    from datetime import datetime
    
    db = SessionLocal()
    try:
        document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not document:
            document_generation_tasks[task_id]["status"] = "failed"
            document_generation_tasks[task_id]["error"] = "Document not found"
            return
        
        # Update task status
        document_generation_tasks[task_id]["status"] = "in_progress"
        document_generation_tasks[task_id]["message"] = f"Generating {document.document_name}..."
        document_generation_tasks[task_id]["progress"] = 10
        
        # Create progress callback
        def progress_callback(task):
            document_generation_tasks[task_id]["progress"] = task.progress
            document_generation_tasks[task_id]["message"] = task.message
        
        # Generate content
        generator = get_document_generator()
        success, content_or_error, metadata = await generator.generate_document(
            db=db,
            document=document,
            assumptions=assumptions,
            additional_context=additional_context,
            progress_callback=progress_callback
        )
        
        if success:
            # Save generated content
            document.generated_content = content_or_error
            document.generated_at = datetime.utcnow()
            document.generation_status = GenerationStatus.GENERATED
            
            # Update document status
            if document.status == DocumentStatus.PENDING:
                document.status = DocumentStatus.UPLOADED
            
            # Save quality score if available
            if metadata and metadata.get("quality_analysis"):
                doc_quality = metadata["quality_analysis"].get(document.document_name, {})
                score = doc_quality.get("score", doc_quality.get("overall_score"))
                if score:
                    document.ai_quality_score = int(score)
            
            db.commit()
            
            # Update task
            document_generation_tasks[task_id]["status"] = "completed"
            document_generation_tasks[task_id]["progress"] = 100
            document_generation_tasks[task_id]["message"] = "Generation complete"
            document_generation_tasks[task_id]["result"] = {
                "content": content_or_error,
                "quality_score": document.ai_quality_score,
                "metadata": metadata
            }
        else:
            # Generation failed
            document.generation_status = GenerationStatus.FAILED
            db.commit()
            
            document_generation_tasks[task_id]["status"] = "failed"
            document_generation_tasks[task_id]["error"] = content_or_error
            document_generation_tasks[task_id]["message"] = f"Generation failed: {content_or_error}"
            
    except Exception as e:
        document_generation_tasks[task_id]["status"] = "failed"
        document_generation_tasks[task_id]["error"] = str(e)
        document_generation_tasks[task_id]["message"] = f"Error: {str(e)}"
        
        # Update document status
        try:
            document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
            if document:
                document.generation_status = GenerationStatus.FAILED
                db.commit()
        except:
            pass
    finally:
        db.close()


async def run_batch_generation(
    batch_task_id: str,
    project_id: str,
    document_ids: List[str],
    assumptions: List[Dict[str, str]]
):
    """Background task to generate multiple documents in order."""
    from backend.database.base import SessionLocal
    from backend.models.document import ProjectDocument, GenerationStatus, DocumentStatus
    from backend.services.document_generator import get_document_generator
    from datetime import datetime
    
    db = SessionLocal()
    try:
        generator = get_document_generator()
        
        # Get documents and sort by dependencies
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(document_ids)
        ).all()
        
        sorted_docs = generator._sort_by_dependencies(documents)
        total_docs = len(sorted_docs)
        
        for i, document in enumerate(sorted_docs):
            # Update task status
            document_generation_tasks[batch_task_id]["current_document"] = document.document_name
            document_generation_tasks[batch_task_id]["message"] = f"Generating {document.document_name} ({i+1}/{total_docs})..."
            document_generation_tasks[batch_task_id]["progress"] = int((i / total_docs) * 100)
            
            try:
                success, content_or_error, metadata = await generator.generate_document(
                    db=db,
                    document=document,
                    assumptions=assumptions
                )
                
                if success:
                    document.generated_content = content_or_error
                    document.generated_at = datetime.utcnow()
                    document.generation_status = GenerationStatus.GENERATED
                    
                    if document.status == DocumentStatus.PENDING:
                        document.status = DocumentStatus.UPLOADED
                    
                    if metadata and metadata.get("quality_analysis"):
                        doc_quality = metadata["quality_analysis"].get(document.document_name, {})
                        score = doc_quality.get("score", doc_quality.get("overall_score"))
                        if score:
                            document.ai_quality_score = int(score)
                    
                    db.commit()
                    document_generation_tasks[batch_task_id]["completed_documents"].append({
                        "id": str(document.id),
                        "name": document.document_name,
                        "quality_score": document.ai_quality_score
                    })
                else:
                    document.generation_status = GenerationStatus.FAILED
                    db.commit()
                    document_generation_tasks[batch_task_id]["failed_documents"].append({
                        "id": str(document.id),
                        "name": document.document_name,
                        "error": content_or_error
                    })
            except Exception as e:
                document.generation_status = GenerationStatus.FAILED
                db.commit()
                document_generation_tasks[batch_task_id]["failed_documents"].append({
                    "id": str(document.id),
                    "name": document.document_name,
                    "error": str(e)
                })
        
        # Complete batch
        document_generation_tasks[batch_task_id]["status"] = "completed"
        document_generation_tasks[batch_task_id]["progress"] = 100
        document_generation_tasks[batch_task_id]["message"] = f"Batch generation complete. {len(document_generation_tasks[batch_task_id]['completed_documents'])}/{total_docs} succeeded."
        document_generation_tasks[batch_task_id]["current_document"] = None
        
    except Exception as e:
        document_generation_tasks[batch_task_id]["status"] = "failed"
        document_generation_tasks[batch_task_id]["error"] = str(e)
        document_generation_tasks[batch_task_id]["message"] = f"Batch generation failed: {str(e)}"
    finally:
        db.close()


# ============================================================================
# APPROVAL WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/documents/{document_id}/request-approval", tags=["Approvals"])
def request_document_approval(
    document_id: str,
    approver_ids: List[str] = Query(None),  # Optional - only needed for manual routing
    upload_id: str = None,
    override_routing: str = Query(None, description="Override routing: manual, auto_co, or default"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request approval for a document using smart routing.
    
    Routing priority:
    1. override_routing parameter (if provided)
    2. Document's configured approval_routing
    3. Fallback to manual selection
    
    Routing types:
    - manual: Use provided approver_ids
    - auto_co: Route to project's assigned Contracting Officer
    - default: Route to document's default_approver_id
    """
    from backend.models.document import DocumentApproval, ApprovalStatus, DocumentStatus, ApprovalAuditLog, ApprovalRouting
    from backend.models.procurement import ProcurementProject

    # Get document
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Determine routing method - use override if provided, else document's setting
    routing = override_routing or (document.approval_routing.value if document.approval_routing else "auto_co")
    
    # Resolve approvers based on routing type
    final_approver_ids = []
    routing_info = ""  # For audit log and response
    
    # Handle DEFAULT routing
    if routing == "default" and document.default_approver_id:
        default_approver = db.query(User).filter(User.id == document.default_approver_id).first()
        if default_approver and default_approver.is_active:
            final_approver_ids.append(str(document.default_approver_id))
            routing_info = f"Routed to default approver: {default_approver.name}"
        else:
            # Fallback to auto_co if default approver not available
            routing = "auto_co"
            routing_info = "Default approver unavailable, falling back to auto_co"
    
    # Handle AUTO_CO routing (or fallback from default)
    if routing == "auto_co" or (routing == "default" and not final_approver_ids):
        project = db.query(ProcurementProject).filter(
            ProcurementProject.id == document.project_id
        ).first()
        
        if project and project.contracting_officer_id:
            co_user = db.query(User).filter(User.id == project.contracting_officer_id).first()
            if co_user and co_user.is_active:
                final_approver_ids.append(str(project.contracting_officer_id))
                routing_info = f"Auto-routed to Project CO: {co_user.name}"
            else:
                routing = "manual"  # Fallback to manual if CO not active
                routing_info = "Project CO unavailable, please select approvers manually"
        else:
            routing = "manual"  # Fallback to manual if no CO assigned
            routing_info = "No CO assigned to project, please select approvers manually"
    
    # Handle MANUAL routing
    if routing == "manual":
        if not approver_ids or len(approver_ids) == 0:
            raise HTTPException(
                status_code=400,
                detail="No approvers specified. Please select approvers or configure document routing."
            )
        
        # Validate all approvers have correct role
        for approver_id in approver_ids:
            approver = db.query(User).filter(User.id == approver_id).first()
            if not approver:
                continue
            if not approver.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"User {approver.name} is not active"
                )
            # Validate approver has appropriate role
            if approver.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.APPROVER]:
                raise HTTPException(
                    status_code=400,
                    detail=f"User {approver.name} does not have approval authority (role: {approver.role.value})"
                )
            final_approver_ids.append(approver_id)
        
        routing_info = f"Manual selection: {len(final_approver_ids)} approver(s)"

    # Ensure we have at least one approver
    if not final_approver_ids:
        raise HTTPException(
            status_code=400,
            detail="Could not determine approvers. Please configure document routing or select manually."
        )

    # Create approval requests for each approver
    approvals_created = []
    for approver_id in final_approver_ids:
        approver = db.query(User).filter(User.id == approver_id).first()
        if not approver:
            continue

        # Check if approval already exists
        existing_approval = db.query(DocumentApproval).filter(
            DocumentApproval.project_document_id == document_id,
            DocumentApproval.approver_id == approver_id,
            DocumentApproval.approval_status == ApprovalStatus.PENDING
        ).first()

        if not existing_approval:
            approval = DocumentApproval(
                project_document_id=document_id,
                document_upload_id=upload_id,
                approver_id=approver_id,
                approval_status=ApprovalStatus.PENDING
            )
            db.add(approval)
            db.flush()  # Flush to get approval.id

            # Create audit log entry with routing info
            audit_log = ApprovalAuditLog(
                approval_id=approval.id,
                action="requested",
                performed_by=current_user.id,
                details=f"Approval requested from {approver.name}. {routing_info}"
            )
            db.add(audit_log)

            approvals_created.append(approval)

    # Update document status to under_review if not already
    if document.status in [DocumentStatus.UPLOADED, DocumentStatus.PENDING]:
        document.status = DocumentStatus.UNDER_REVIEW

    db.commit()

    # Refresh all approvals
    for approval in approvals_created:
        db.refresh(approval)

    return {
        "message": f"Approval requested from {len(approvals_created)} user(s)",
        "routing_method": routing,
        "routing_info": routing_info,
        "approvals": [a.to_dict() for a in approvals_created]
    }


@app.patch("/api/documents/{document_id}/routing", tags=["Documents"])
def update_document_routing(
    document_id: str,
    approval_routing: str = Query(..., description="Routing type: manual, auto_co, or default"),
    default_approver_id: str = Query(None, description="User ID for default approver (required if routing=default)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update approval routing settings for a document.
    
    Only project editors (CO, PM, Admin) can modify routing settings.
    
    Routing types:
    - manual: User manually selects approvers each time
    - auto_co: Automatically route to project's Contracting Officer
    - default: Route to document's configured default approver
    """
    from backend.models.document import ApprovalRouting
    
    # Check user has edit permission (CO, PM, or Admin roles)
    if current_user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only Contracting Officers, Program Managers, or Admins can modify document routing"
        )
    
    # Get document
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Validate routing value
    valid_routing_values = ["manual", "auto_co", "default"]
    if approval_routing not in valid_routing_values:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid routing type. Must be one of: {', '.join(valid_routing_values)}"
        )
    
    # Convert string to enum
    routing_enum = ApprovalRouting(approval_routing)
    
    # If default routing, validate default_approver_id is provided and valid
    if routing_enum == ApprovalRouting.DEFAULT:
        if not default_approver_id:
            raise HTTPException(
                status_code=400, 
                detail="default_approver_id is required when routing type is 'default'"
            )
        
        # Verify approver exists and has correct role
        approver = db.query(User).filter(User.id == default_approver_id).first()
        if not approver:
            raise HTTPException(status_code=404, detail="Default approver user not found")
        
        if not approver.is_active:
            raise HTTPException(status_code=400, detail="Default approver must be an active user")
        
        # Validate approver has appropriate role
        if approver.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.APPROVER]:
            raise HTTPException(
                status_code=400, 
                detail=f"Default approver must have approval authority. {approver.name} has role: {approver.role.value}"
            )
        
        document.default_approver_id = default_approver_id
    
    # Update routing setting
    document.approval_routing = routing_enum
    
    db.commit()
    db.refresh(document)
    
    return {
        "message": f"Document routing updated to '{approval_routing}'",
        "document": document.to_dict()
    }


@app.post("/api/approvals/{approval_id}/approve", tags=["Approvals"])
def approve_document(
    approval_id: str,
    comments: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a document"""
    from backend.models.document import DocumentApproval, ApprovalStatus, DocumentStatus, ApprovalAuditLog
    from datetime import datetime

    approval = db.query(DocumentApproval).filter(DocumentApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # Verify the current user is the assigned approver
    if str(approval.approver_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not authorized to approve this document")

    # Update approval
    approval.approval_status = ApprovalStatus.APPROVED
    approval.approval_date = datetime.now()
    if comments:
        approval.comments = comments

    # Create audit log entry
    audit_log = ApprovalAuditLog(
        approval_id=approval_id,
        action="approved",
        performed_by=current_user.id,
        details=comments or "Approved without comments"
    )
    db.add(audit_log)

    # Check if all approvals are complete
    document = db.query(ProjectDocument).filter(ProjectDocument.id == approval.project_document_id).first()
    all_approvals = db.query(DocumentApproval).filter(
        DocumentApproval.project_document_id == approval.project_document_id
    ).all()

    pending_count = sum(1 for a in all_approvals if a.approval_status == ApprovalStatus.PENDING)
    rejected_count = sum(1 for a in all_approvals if a.approval_status == ApprovalStatus.REJECTED)

    # Update document status based on approvals
    if rejected_count > 0:
        document.status = DocumentStatus.REJECTED
    elif pending_count == 0:
        document.status = DocumentStatus.APPROVED

    db.commit()
    db.refresh(approval)

    return {
        "message": "Document approved successfully",
        "approval": approval.to_dict(),
        "document_status": document.status.value
    }


@app.post("/api/approvals/{approval_id}/reject", tags=["Approvals"])
def reject_document(
    approval_id: str,
    comments: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a document with comments"""
    from backend.models.document import DocumentApproval, ApprovalStatus, DocumentStatus, ApprovalAuditLog
    from datetime import datetime

    approval = db.query(DocumentApproval).filter(DocumentApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # Verify the current user is the assigned approver
    if str(approval.approver_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not authorized to reject this document")

    if not comments:
        raise HTTPException(status_code=400, detail="Comments are required when rejecting a document")

    # Update approval
    approval.approval_status = ApprovalStatus.REJECTED
    approval.approval_date = datetime.now()
    approval.comments = comments

    # Create audit log entry
    audit_log = ApprovalAuditLog(
        approval_id=approval_id,
        action="rejected",
        performed_by=current_user.id,
        details=comments
    )
    db.add(audit_log)

    # Update document status
    document = db.query(ProjectDocument).filter(ProjectDocument.id == approval.project_document_id).first()
    document.status = DocumentStatus.REJECTED

    db.commit()
    db.refresh(approval)

    return {
        "message": "Document rejected",
        "approval": approval.to_dict(),
        "document_status": document.status.value
    }


@app.get("/api/documents/{document_id}/approvals", tags=["Approvals"])
def get_document_approvals(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all approval requests for a document"""
    from backend.models.document import DocumentApproval

    approvals = db.query(DocumentApproval).filter(
        DocumentApproval.project_document_id == document_id
    ).order_by(DocumentApproval.requested_at.desc()).all()

    # Enrich with approver information
    approval_list = []
    for approval in approvals:
        approval_dict = approval.to_dict()
        approver = db.query(User).filter(User.id == approval.approver_id).first()
        if approver:
            approval_dict['approver'] = {
                'id': str(approver.id),
                'name': approver.name,
                'email': approver.email
            }
        approval_list.append(approval_dict)

    return {"approvals": approval_list}


@app.get("/api/approvals/pending", tags=["Approvals"])
def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending approvals for the current user"""
    from backend.models.document import DocumentApproval, ApprovalStatus

    approvals = db.query(DocumentApproval).filter(
        DocumentApproval.approver_id == current_user.id,
        DocumentApproval.approval_status == ApprovalStatus.PENDING
    ).order_by(DocumentApproval.requested_at.desc()).all()

    # Enrich with document and project information
    approval_list = []
    for approval in approvals:
        approval_dict = approval.to_dict()

        # Get document info
        document = db.query(ProjectDocument).filter(ProjectDocument.id == approval.project_document_id).first()
        if document:
            approval_dict['document'] = {
                'id': str(document.id),
                'name': document.document_name,
                'description': document.description,
                'status': document.status.value,
                'category': document.category
            }

            # Get project info
            project = db.query(ProcurementProject).filter(ProcurementProject.id == document.project_id).first()
            if project:
                approval_dict['project'] = {
                    'id': str(project.id),
                    'name': project.name
                }

        approval_list.append(approval_dict)

    return {"approvals": approval_list, "count": len(approval_list)}


@app.post("/api/approvals/{approval_id}/delegate", tags=["Approvals"])
def delegate_approval(
    approval_id: str,
    delegate_to_user_id: str = Query(...),
    reason: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delegate an approval to another user"""
    from backend.models.document import DocumentApproval, ApprovalAuditLog

    approval = db.query(DocumentApproval).filter(DocumentApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Verify current user is the approver
    if str(approval.approver_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned approver can delegate")

    # Verify approval is still pending
    if approval.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only delegate pending approvals")

    # Get delegate user
    delegate_user = db.query(User).filter(User.id == delegate_to_user_id).first()
    if not delegate_user:
        raise HTTPException(status_code=404, detail="Delegate user not found")

    # Check if delegate user has appropriate role
    if delegate_user.role not in ['contracting_officer', 'program_manager', 'approver']:
        raise HTTPException(status_code=400, detail="Delegate must have approval authority")

    # Store original approver and update to delegated approver
    original_approver_id = approval.approver_id
    approval.delegated_from_id = original_approver_id
    approval.approver_id = delegate_to_user_id

    # Create audit log entry
    audit_log = ApprovalAuditLog(
        approval_id=approval_id,
        action="delegated",
        performed_by=current_user.id,
        details=f"Delegated from {current_user.name} to {delegate_user.name}. Reason: {reason or 'No reason provided'}"
    )
    db.add(audit_log)
    db.commit()

    return {
        "message": f"Approval delegated to {delegate_user.name}",
        "approval": approval.to_dict()
    }


@app.get("/api/approvals/{approval_id}/audit-trail", tags=["Approvals"])
def get_approval_audit_trail(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete audit trail for an approval"""
    from backend.models.document import DocumentApproval, ApprovalAuditLog

    approval = db.query(DocumentApproval).filter(DocumentApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Get all audit log entries for this approval
    audit_logs = db.query(ApprovalAuditLog).filter(
        ApprovalAuditLog.approval_id == approval_id
    ).order_by(ApprovalAuditLog.timestamp.desc()).all()

    # Enrich with user information
    audit_trail = []
    for log in audit_logs:
        log_dict = log.to_dict()
        user = db.query(User).filter(User.id == log.performed_by).first()
        if user:
            log_dict['performed_by_user'] = {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        audit_trail.append(log_dict)

    return {
        "approval_id": approval_id,
        "audit_trail": audit_trail
    }


@app.get("/api/documents/{document_id}/approval-history", tags=["Approvals"])
def get_document_approval_history(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete approval history for a document including all audit trails"""
    from backend.models.document import ProjectDocument, DocumentApproval, ApprovalAuditLog

    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get all approvals for this document
    approvals = db.query(DocumentApproval).filter(
        DocumentApproval.project_document_id == document_id
    ).order_by(DocumentApproval.requested_at.desc()).all()

    history = []
    for approval in approvals:
        approval_dict = approval.to_dict()

        # Get approver info
        approver = db.query(User).filter(User.id == approval.approver_id).first()
        if approver:
            approval_dict['approver'] = {
                'id': str(approver.id),
                'name': approver.name,
                'email': approver.email,
                'role': approver.role
            }

        # Get delegated from user if applicable
        if approval.delegated_from_id:
            delegated_from = db.query(User).filter(User.id == approval.delegated_from_id).first()
            if delegated_from:
                approval_dict['delegated_from'] = {
                    'id': str(delegated_from.id),
                    'name': delegated_from.name,
                    'email': delegated_from.email
                }

        # Get audit trail for this approval
        audit_logs = db.query(ApprovalAuditLog).filter(
            ApprovalAuditLog.approval_id == approval.id
        ).order_by(ApprovalAuditLog.timestamp.asc()).all()

        approval_dict['audit_trail'] = []
        for log in audit_logs:
            log_dict = log.to_dict()
            user = db.query(User).filter(User.id == log.performed_by).first()
            if user:
                log_dict['performed_by_user'] = {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email
                }
            approval_dict['audit_trail'].append(log_dict)

        history.append(approval_dict)

    return {
        "document_id": document_id,
        "document_name": document.document_name,
        "history": history
    }


@app.delete("/api/uploads/{upload_id}", tags=["Documents"])
def delete_document_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document upload"""
    from backend.models.document import DocumentUpload

    upload = db.query(DocumentUpload).filter(DocumentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # TODO: Delete actual file from storage

    db.delete(upload)
    db.commit()

    return {"message": "Upload deleted successfully"}


@app.get("/api/projects/{project_id}/steps", tags=["Steps"])
def get_project_steps(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all steps for a project"""
    steps = db.query(ProcurementStep).filter(
        ProcurementStep.project_id == project_id
    ).order_by(ProcurementStep.step_order).all()

    # Convert to dict with assigned user info
    steps_data = []
    for step in steps:
        step_dict = step.to_dict()
        # Add assigned user info if available
        if step.assigned_user_id:
            assigned_user = db.query(User).filter(User.id == step.assigned_user_id).first()
            if assigned_user:
                step_dict["assigned_user"] = {
                    "name": assigned_user.name,
                    "email": assigned_user.email
                }
        steps_data.append(step_dict)

    return {"steps": steps_data}


@app.patch("/api/steps/{step_id}", tags=["Steps"])
def update_step(
    step_id: str,
    status: str = None,
    completion_date: str = None,
    notes: str = None,
    assigned_user_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a procurement step"""
    step = db.query(ProcurementStep).filter(ProcurementStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # Update fields if provided
    if status:
        from backend.models.procurement import StepStatus
        step.status = StepStatus(status)
    if completion_date:
        from datetime import date
        step.completion_date = date.fromisoformat(completion_date)
    if notes is not None:
        step.notes = notes
    if assigned_user_id:
        step.assigned_user_id = assigned_user_id

    db.commit()
    db.refresh(step)

    return {"message": "Step updated successfully", "step": step.to_dict()}


@app.patch("/api/phases/{phase_id}", tags=["Phases"])
def update_phase(
    phase_id: str,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a procurement phase"""
    phase = db.query(ProcurementPhase).filter(ProcurementPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Update fields if provided
    if status:
        from backend.models.procurement import PhaseStatus
        phase.status = PhaseStatus(status)
    if start_date:
        from datetime import date
        phase.start_date = date.fromisoformat(start_date)
    if end_date:
        from datetime import date
        phase.actual_completion_date = date.fromisoformat(end_date)

    db.commit()
    db.refresh(phase)

    return {"message": "Phase updated successfully", "phase": phase.to_dict()}


@app.post("/api/phases/{phase_id}/create-default-steps", tags=["Phases"])
def create_default_steps(
    phase_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create default steps for a phase if none exist.
    
    Uses database-level row locking (SELECT FOR UPDATE) to prevent race conditions
    when multiple requests try to create steps simultaneously (e.g., React StrictMode).
    """
    # Lock the phase row to prevent concurrent step creation
    # This serializes requests - second request waits until first commits
    phase = db.query(ProcurementPhase).filter(
        ProcurementPhase.id == phase_id
    ).with_for_update().first()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Check if steps already exist using count for reliability
    existing_count = db.query(ProcurementStep).filter(
        ProcurementStep.phase_id == phase_id
    ).count()

    if existing_count > 0:
        # Return existing steps instead of error for better UX
        existing_steps = db.query(ProcurementStep).filter(
            ProcurementStep.phase_id == phase_id
        ).order_by(ProcurementStep.step_order).all()
        return {
            "message": "Steps already exist for this phase", 
            "created": False,
            "steps": [s.to_dict() for s in existing_steps]
        }

    # Create default steps based on phase name
    default_steps_map = {
        'pre_solicitation': [
            {'name': 'Initial Needs Assessment', 'description': 'Identify and document the procurement need and requirements', 'requires_approval': False},
            {'name': 'Market Research', 'description': 'Conduct market research to identify potential vendors and solutions', 'requires_approval': False},
            {'name': 'Requirements Definition', 'description': 'Define detailed technical and functional requirements', 'requires_approval': True},
            {'name': 'Budget Approval', 'description': 'Obtain budget approval and funding authorization', 'requires_approval': True},
            {'name': 'Acquisition Strategy Development', 'description': 'Develop comprehensive acquisition strategy document', 'requires_approval': True},
            {'name': 'Independent Cost Estimate', 'description': 'Prepare independent government cost estimate', 'requires_approval': False},
            {'name': 'Solicitation Planning', 'description': 'Finalize solicitation timeline and resource allocation', 'requires_approval': False},
        ],
        'solicitation': [
            {'name': 'Draft Solicitation Review', 'description': 'Review draft solicitation with legal and technical teams', 'requires_approval': True},
            {'name': 'RFP/RFQ Publication', 'description': 'Publish solicitation to contracting platform', 'requires_approval': False},
            {'name': 'Pre-Proposal Conference', 'description': 'Conduct pre-proposal conference with potential vendors', 'requires_approval': False},
            {'name': 'Vendor Question Period', 'description': 'Answer vendor questions and issue amendments if needed', 'requires_approval': False},
            {'name': 'Proposal Submission Deadline', 'description': 'Receive and log all vendor proposals', 'requires_approval': False},
            {'name': 'Initial Completeness Review', 'description': 'Review proposals for completeness and responsiveness', 'requires_approval': False},
            {'name': 'Technical Evaluation', 'description': 'Conduct detailed technical evaluation of proposals', 'requires_approval': True},
        ],
        'post_solicitation': [
            {'name': 'Detailed Evaluation', 'description': 'Complete detailed evaluation with scoring matrix', 'requires_approval': False},
            {'name': 'Competitive Range Determination', 'description': 'Determine competitive range and notify vendors', 'requires_approval': True},
            {'name': 'Clarification Requests', 'description': 'Issue clarification requests to vendors as needed', 'requires_approval': False},
            {'name': 'Negotiations', 'description': 'Conduct negotiations with vendors in competitive range', 'requires_approval': False},
            {'name': 'Best and Final Offers', 'description': 'Request and evaluate best and final offers', 'requires_approval': False},
            {'name': 'Source Selection Decision', 'description': 'Make final source selection decision', 'requires_approval': True},
            {'name': 'Pre-Award Notifications', 'description': 'Notify successful and unsuccessful vendors', 'requires_approval': False},
            {'name': 'Contract Award', 'description': 'Execute and award the contract', 'requires_approval': True},
            {'name': 'Post-Award Debrief', 'description': 'Provide debriefings to unsuccessful vendors if requested', 'requires_approval': False},
            {'name': 'Implementation Kickoff', 'description': 'Hand off to project implementation team', 'requires_approval': False},
        ]
    }

    default_steps = default_steps_map.get(phase.phase_name, [])

    if not default_steps:
        return {"message": "No default steps defined for this phase", "created": False}

    # Create steps
    from backend.models.procurement import StepStatus
    for i, step_data in enumerate(default_steps):
        new_step = ProcurementStep(
            phase_id=phase_id,
            project_id=phase.project_id,
            step_name=step_data['name'],
            step_description=step_data['description'],
            step_order=i + 1,
            requires_approval=step_data['requires_approval'],
            status=StepStatus.NOT_STARTED
        )
        db.add(new_step)

    db.commit()

    # Fetch and return the created steps
    created_steps = db.query(ProcurementStep).filter(
        ProcurementStep.phase_id == phase_id
    ).order_by(ProcurementStep.step_order).all()

    return {
        "message": "Default steps created successfully",
        "created": True,
        "steps": [s.to_dict() for s in created_steps]
    }


@app.post("/api/phases/{phase_id}/cleanup-duplicate-steps", tags=["Phases"])
def cleanup_duplicate_steps(
    phase_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove duplicate steps from a phase, keeping only the first occurrence of each step_name.
    
    This endpoint fixes issues caused by race conditions where steps were created twice.
    It keeps the step with the lowest step_order for each unique step_name.
    """
    # Verify phase exists
    phase = db.query(ProcurementPhase).filter(ProcurementPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # Get all steps for this phase, ordered by step_order
    all_steps = db.query(ProcurementStep).filter(
        ProcurementStep.phase_id == phase_id
    ).order_by(ProcurementStep.step_order).all()
    
    # Track seen step names and identify duplicates
    seen_names = set()
    duplicates_to_delete = []
    
    for step in all_steps:
        if step.step_name in seen_names:
            # This is a duplicate - mark for deletion
            duplicates_to_delete.append(step)
        else:
            # First occurrence - keep it
            seen_names.add(step.step_name)
    
    # Delete duplicates
    deleted_count = len(duplicates_to_delete)
    for dup in duplicates_to_delete:
        db.delete(dup)
    
    # Renumber remaining steps to ensure sequential ordering
    remaining_steps = db.query(ProcurementStep).filter(
        ProcurementStep.phase_id == phase_id
    ).order_by(ProcurementStep.step_order).all()
    
    for i, step in enumerate(remaining_steps):
        step.step_order = i + 1
    
    db.commit()
    
    # Return cleaned up steps
    final_steps = db.query(ProcurementStep).filter(
        ProcurementStep.phase_id == phase_id
    ).order_by(ProcurementStep.step_order).all()
    
    return {
        "message": f"Removed {deleted_count} duplicate steps",
        "deleted_count": deleted_count,
        "remaining_steps": len(final_steps),
        "steps": [s.to_dict() for s in final_steps]
    }


@app.post("/api/projects/{project_id}/cleanup-all-duplicate-steps", tags=["Projects"])
def cleanup_all_project_duplicate_steps(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove duplicate steps from all phases of a project.
    
    Convenience endpoint to clean up an entire project at once.
    """
    # Verify project exists
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all phases for this project
    phases = db.query(ProcurementPhase).filter(
        ProcurementPhase.project_id == project_id
    ).all()
    
    total_deleted = 0
    phase_results = []
    
    for phase in phases:
        # Get all steps for this phase
        all_steps = db.query(ProcurementStep).filter(
            ProcurementStep.phase_id == phase.id
        ).order_by(ProcurementStep.step_order).all()
        
        # Track seen step names and identify duplicates
        seen_names = set()
        duplicates_to_delete = []
        
        for step in all_steps:
            if step.step_name in seen_names:
                duplicates_to_delete.append(step)
            else:
                seen_names.add(step.step_name)
        
        # Delete duplicates
        for dup in duplicates_to_delete:
            db.delete(dup)
        
        # Renumber remaining steps
        remaining_steps = db.query(ProcurementStep).filter(
            ProcurementStep.phase_id == phase.id
        ).order_by(ProcurementStep.step_order).all()
        
        for i, step in enumerate(remaining_steps):
            step.step_order = i + 1
        
        deleted_count = len(duplicates_to_delete)
        total_deleted += deleted_count
        
        phase_results.append({
            "phase_id": phase.id,
            "phase_name": phase.phase_name,
            "deleted_count": deleted_count,
            "remaining_steps": len(remaining_steps)
        })
    
    db.commit()
    
    return {
        "message": f"Cleaned up {total_deleted} duplicate steps across {len(phases)} phases",
        "total_deleted": total_deleted,
        "phases": phase_results
    }


# ============================================================================
# PHASE TRANSITION / GATE ENFORCEMENT ENDPOINTS
# ============================================================================

@app.get("/api/phases/{phase_id}/validate-transition", tags=["Phase Transitions"])
def validate_phase_transition(
    phase_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate if a phase transition is allowed based on document approvals.
    
    Checks:
    - All required documents for current phase exist
    - All required documents have approved status
    - User has permission to request transition
    - Returns the required gatekeeper role
    """
    from backend.services.phase_gate_service import phase_gate_service
    from backend.models.procurement import ProcurementPhase
    
    # Get the current phase
    phase = db.query(ProcurementPhase).filter(ProcurementPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # Determine the next phase
    next_phase = phase_gate_service.get_next_phase(phase.phase_name.value)
    if not next_phase:
        return {
            "can_transition": False,
            "blocking_issues": ["This is the final phase - no further transitions available"],
            "warnings": [],
            "document_status": {},
            "required_gatekeeper": None,
            "user_can_request": False,
            "from_phase": phase.phase_name.value,
            "to_phase": None
        }
    
    # Validate the transition
    validation = phase_gate_service.validate_transition(
        db=db,
        project_id=str(phase.project_id),
        from_phase=phase.phase_name.value,
        to_phase=next_phase,
        user=current_user
    )
    
    # Add eligible gatekeepers to the response
    eligible_gatekeepers = phase_gate_service.get_eligible_gatekeepers(
        db=db,
        project_id=str(phase.project_id),
        from_phase=phase.phase_name.value,
        to_phase=next_phase
    )
    
    return {
        **validation,
        "from_phase": phase.phase_name.value,
        "to_phase": next_phase,
        "eligible_gatekeepers": eligible_gatekeepers
    }


@app.post("/api/phases/{phase_id}/request-transition", tags=["Phase Transitions"])
def request_phase_transition(
    phase_id: str,
    gatekeeper_id: str = Query(None, description="UUID of the gatekeeper to assign"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request approval to transition to the next phase.
    
    Creates a phase transition request that must be approved by a gatekeeper
    (typically a Contracting Officer or Source Selection Authority).
    """
    from backend.services.phase_gate_service import phase_gate_service
    from backend.models.procurement import ProcurementPhase, PhaseTransitionRequest, TransitionStatus
    
    # Get the current phase
    phase = db.query(ProcurementPhase).filter(ProcurementPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # Determine the next phase
    next_phase = phase_gate_service.get_next_phase(phase.phase_name.value)
    if not next_phase:
        raise HTTPException(status_code=400, detail="This is the final phase - no further transitions available")
    
    # Check for existing pending request
    existing_request = db.query(PhaseTransitionRequest).filter(
        PhaseTransitionRequest.project_id == phase.project_id,
        PhaseTransitionRequest.from_phase == phase.phase_name,
        PhaseTransitionRequest.status == TransitionStatus.PENDING
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=400, 
            detail="A pending transition request already exists for this phase"
        )
    
    # Validate the transition
    validation = phase_gate_service.validate_transition(
        db=db,
        project_id=str(phase.project_id),
        from_phase=phase.phase_name.value,
        to_phase=next_phase,
        user=current_user
    )
    
    # Check if user can request
    if not validation["user_can_request"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to request phase transitions"
        )
    
    # Allow request even with warnings (blocking issues still block)
    if not validation["can_transition"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot request transition: {'; '.join(validation['blocking_issues'])}"
        )
    
    # Create the transition request
    transition_request = phase_gate_service.create_transition_request(
        db=db,
        project_id=str(phase.project_id),
        from_phase=phase.phase_name.value,
        to_phase=next_phase,
        requested_by=str(current_user.id),
        gatekeeper_id=gatekeeper_id,
        validation_results=validation
    )
    
    # Create a notification for the gatekeeper if assigned
    if gatekeeper_id:
        from backend.models.notification import Notification
        import uuid as uuid_module
        notification = Notification(
            user_id=uuid_module.UUID(gatekeeper_id),
            notification_type="phase_transition_request",
            title="Phase Transition Request",
            message=f"A phase transition request has been submitted for your approval",
            data={
                "transition_request_id": str(transition_request.id),
                "project_id": str(phase.project_id),
                "from_phase": phase.phase_name.value,
                "to_phase": next_phase
            }
        )
        db.add(notification)
        db.commit()
    
    return {
        "message": "Phase transition request created successfully",
        "transition_request": transition_request.to_dict()
    }


@app.get("/api/phase-transitions/pending", tags=["Phase Transitions"])
def get_pending_phase_transitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending phase transition requests for the current user.
    
    Returns transitions where:
    - User is the assigned gatekeeper, OR
    - User is a CO/Admin and transition requires CO approval
    """
    from backend.models.procurement import PhaseTransitionRequest, TransitionStatus
    from backend.models.user import UserRole
    
    # Get pending transitions assigned to this user
    pending = db.query(PhaseTransitionRequest).filter(
        PhaseTransitionRequest.status == TransitionStatus.PENDING
    ).all()
    
    # Filter based on user role
    # Admins and COs can see all pending transitions they're eligible to approve
    user_transitions = []
    for transition in pending:
        # If explicitly assigned to this user
        if transition.gatekeeper_id and str(transition.gatekeeper_id) == str(current_user.id):
            user_transitions.append(transition)
        # Or if user is CO/Admin and no specific gatekeeper assigned
        elif not transition.gatekeeper_id and current_user.role in [UserRole.CONTRACTING_OFFICER, UserRole.ADMIN]:
            user_transitions.append(transition)
    
    return {
        "pending_transitions": [t.to_dict() for t in user_transitions],
        "count": len(user_transitions)
    }


@app.post("/api/phase-transitions/{transition_id}/approve", tags=["Phase Transitions"])
def approve_phase_transition(
    transition_id: str,
    comments: str = Query(None, description="Optional approval comments"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a phase transition request.
    
    This will:
    - Update the transition request status to approved
    - Update the project's current phase
    - Mark the old phase as completed
    - Mark the new phase as in_progress
    """
    from backend.services.phase_gate_service import phase_gate_service
    from backend.models.procurement import PhaseTransitionRequest, TransitionStatus
    from backend.models.user import UserRole
    
    # Get the transition request
    transition = db.query(PhaseTransitionRequest).filter(
        PhaseTransitionRequest.id == transition_id
    ).first()
    
    if not transition:
        raise HTTPException(status_code=404, detail="Transition request not found")
    
    if transition.status != TransitionStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Transition request is not pending (status: {transition.status.value})"
        )
    
    # Verify user can approve
    can_approve = False
    if transition.gatekeeper_id and str(transition.gatekeeper_id) == str(current_user.id):
        can_approve = True
    elif current_user.role in [UserRole.CONTRACTING_OFFICER, UserRole.ADMIN]:
        can_approve = True
    
    if not can_approve:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to approve this transition"
        )
    
    # Approve the transition
    updated_transition, success = phase_gate_service.approve_transition(
        db=db,
        transition_request=transition,
        gatekeeper=current_user,
        comments=comments
    )
    
    # Create notification for the requester
    from backend.models.notification import Notification
    notification = Notification(
        user_id=transition.requested_by,
        notification_type="phase_transition_approved",
        title="Phase Transition Approved",
        message=f"Your phase transition request has been approved",
        data={
            "transition_request_id": str(transition.id),
            "project_id": str(transition.project_id),
            "from_phase": transition.from_phase.value,
            "to_phase": transition.to_phase.value,
            "approved_by": current_user.name
        }
    )
    db.add(notification)
    db.commit()
    
    return {
        "message": "Phase transition approved successfully",
        "transition_request": updated_transition.to_dict()
    }


@app.post("/api/phase-transitions/{transition_id}/reject", tags=["Phase Transitions"])
def reject_phase_transition(
    transition_id: str,
    comments: str = Query(..., description="Required rejection reason"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a phase transition request.
    
    Requires comments explaining why the transition was rejected.
    """
    from backend.services.phase_gate_service import phase_gate_service
    from backend.models.procurement import PhaseTransitionRequest, TransitionStatus
    from backend.models.user import UserRole
    
    # Get the transition request
    transition = db.query(PhaseTransitionRequest).filter(
        PhaseTransitionRequest.id == transition_id
    ).first()
    
    if not transition:
        raise HTTPException(status_code=404, detail="Transition request not found")
    
    if transition.status != TransitionStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Transition request is not pending (status: {transition.status.value})"
        )
    
    # Verify user can reject
    can_reject = False
    if transition.gatekeeper_id and str(transition.gatekeeper_id) == str(current_user.id):
        can_reject = True
    elif current_user.role in [UserRole.CONTRACTING_OFFICER, UserRole.ADMIN]:
        can_reject = True
    
    if not can_reject:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to reject this transition"
        )
    
    if not comments or not comments.strip():
        raise HTTPException(
            status_code=400,
            detail="Comments are required when rejecting a phase transition"
        )
    
    # Reject the transition
    updated_transition = phase_gate_service.reject_transition(
        db=db,
        transition_request=transition,
        gatekeeper=current_user,
        comments=comments
    )
    
    # Create notification for the requester
    from backend.models.notification import Notification
    notification = Notification(
        user_id=transition.requested_by,
        notification_type="phase_transition_rejected",
        title="Phase Transition Rejected",
        message=f"Your phase transition request has been rejected",
        data={
            "transition_request_id": str(transition.id),
            "project_id": str(transition.project_id),
            "from_phase": transition.from_phase.value,
            "to_phase": transition.to_phase.value,
            "rejected_by": current_user.name,
            "reason": comments
        }
    )
    db.add(notification)
    db.commit()
    
    return {
        "message": "Phase transition rejected",
        "transition_request": updated_transition.to_dict()
    }


@app.get("/api/projects/{project_id}/transition-history", tags=["Phase Transitions"])
def get_project_transition_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the history of phase transitions for a project.
    
    Returns all transition requests (pending, approved, rejected) for the project.
    """
    from backend.models.procurement import PhaseTransitionRequest
    
    # Verify project exists
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all transitions for this project
    transitions = db.query(PhaseTransitionRequest).filter(
        PhaseTransitionRequest.project_id == project_id
    ).order_by(PhaseTransitionRequest.requested_at.desc()).all()
    
    return {
        "project_id": project_id,
        "transitions": [t.to_dict() for t in transitions],
        "count": len(transitions)
    }


# ============================================================================
# Document Generation Endpoints
# ============================================================================

@app.post("/api/projects/{project_id}/generate-document", tags=["Document Generation"])
async def generate_document(
    project_id: str,
    document_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger AI document generation for a project
    This will run your existing scripts/generate_all_phases_alms.py in the background
    """
    project = db.query(ProcurementProject).filter(ProcurementProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Integrate with your existing document generation code
    # For now, return a placeholder response
    return {
        "message": "Document generation started",
        "project_id": project_id,
        "document_type": document_type,
        "status": "processing"
    }


# ============================================================================
# Notification Endpoints
# ============================================================================

@app.get("/api/notifications", tags=["Notifications"])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = False
):
    """Get notifications for the current user"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()

    return {"notifications": [n.to_dict() for n in notifications]}


@app.patch("/api/notifications/{notification_id}/read", tags=["Notifications"])
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@app.patch("/api/notifications/read-all", tags=["Notifications"])
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

    return {"message": "All notifications marked as read"}


@app.delete("/api/notifications/{notification_id}", tags=["Notifications"])
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted"}


# ============================================================================
# WebSocket Endpoint for Real-time Updates
# ============================================================================

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time document generation progress
    Front-end connects here to receive live updates during document generation
    """
    await ws_manager.connect(websocket, project_id)

    try:
        while True:
            # Wait for messages from client (keep connection alive)
            data = await websocket.receive_text()

            # You can handle client messages here if needed
            # For now, just echo back
            await websocket.send_text(f"Message received: {data}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)


# ============================================================================
# RAG (Document Upload for Generation) Endpoints
# ============================================================================

@app.post("/api/rag/upload", tags=["RAG"])
async def upload_document_to_rag(
    file: UploadFile = File(...),
    category: str = Query(None, description="Document category: strategy, market_research, requirements, or templates"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document to the RAG system for document generation

    This endpoint accepts document uploads and processes them into the
    RAG vector database for use in AI-powered document generation.

    Supported formats: PDF, DOCX, PPTX, XLSX, TXT, MD, and more
    
    Categories:
    - strategy: Acquisition strategy documents
    - market_research: Market research and analysis
    - requirements: Requirements documents, CDRLs
    - templates: Standard forms and templates
    """
    try:
        # Read file content
        file_content = await file.read()

        # Get RAG service
        rag_service = get_rag_service()

        # Prepare metadata
        metadata = {
            "uploaded_by_name": current_user.name,
            "uploaded_by_email": current_user.email
        }
        
        # Add category if provided
        if category:
            valid_categories = ["strategy", "market_research", "requirements", "templates"]
            if category not in valid_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
                )
            metadata["category"] = category

        # Process and upload document
        result = rag_service.upload_and_process_document(
            file_content=file_content,
            filename=file.filename,
            user_id=str(current_user.id),
            metadata=metadata
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to process document")
            )

        return {
            "message": result["message"],
            "filename": result["filename"],
            "chunks_created": result["chunks_created"],
            "file_size": result["file_size"],
            "category": category
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@app.get("/api/rag/documents", tags=["RAG"])
def list_rag_documents(
    current_user: User = Depends(get_current_user)
):
    """
    List all documents uploaded to the RAG system

    Returns a list of all documents that have been processed
    into the RAG vector database.
    """
    try:
        rag_service = get_rag_service()
        documents = rag_service.list_uploaded_documents()

        return {
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@app.delete("/api/rag/documents/{document_id}", tags=["RAG"])
def delete_rag_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document from the RAG system
    
    Removes the document and its associated chunks from the vector store.
    The document_id should be the filename of the uploaded document.
    
    Args:
        document_id: The filename/identifier of the document to delete
    
    Returns:
        Success message with deletion details
    """
    try:
        rag_service = get_rag_service()
        
        # Attempt to delete the document from the RAG system
        result = rag_service.delete_document(document_id)
        
        if result.get("success"):
            return {
                "message": f"Document '{document_id}' deleted successfully",
                "deleted_chunks": result.get("deleted_chunks", 0),
                "document_id": document_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found in RAG system"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@app.get("/api/rag/stats", tags=["RAG"])
def get_rag_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about the RAG system

    Returns information about the vector store and uploaded documents.
    """
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_vector_store_stats()

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}"
        )


@app.post("/api/rag/search", tags=["RAG"])
def search_rag_documents(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of results to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for relevant document chunks in the RAG system

    Performs semantic search across all processed documents.
    """
    try:
        rag_service = get_rag_service()
        results = rag_service.search_documents(query=query, k=k)

        return {
            "query": query,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )


@app.post("/api/extract-assumptions", tags=["RAG"])
async def extract_assumptions(
    current_user: User = Depends(get_current_user)
):
    """
    Extract key assumptions from uploaded RAG documents using AI

    Analyzes all documents in the RAG system and extracts:
    - Contract type and structure
    - Evaluation criteria
    - Security and compliance requirements
    - Timeline constraints
    - Budget assumptions
    - Key performance parameters

    Returns structured assumptions with source references.
    """
    try:
        import anthropic

        rag_service = get_rag_service()

        # Get all uploaded documents
        documents = rag_service.list_uploaded_documents()

        if not documents:
            return {
                "assumptions": [],
                "message": "No documents uploaded yet. Please upload documents first."
            }

        # Search for key assumption categories
        assumption_queries = [
            "contract type structure IDIQ BPA requirements",
            "evaluation criteria factors best value price technical",
            "security requirements CMMC CUI compliance DFARS",
            "schedule timeline milestones delivery dates",
            "budget cost ceiling funding IGCE",
            "performance requirements KPP KSA technical specifications"
        ]

        # Gather relevant context from RAG
        all_context = []
        for query in assumption_queries:
            results = rag_service.search_documents(query=query, k=3)
            all_context.extend(results)

        # Build context string for AI
        context_text = "\n\n---\n\n".join([
            f"Source: {r['metadata'].get('source', 'Unknown')} (from {r['metadata'].get('file_path', 'Unknown')})\n{r['content']}"
            for r in all_context[:15]  # Limit to top 15 chunks to stay within token limits
        ])

        # Use Anthropic Claude to extract structured assumptions
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""You are a DoD acquisition expert analyzing uploaded procurement documents.

Extract 5-8 key assumptions that should guide document generation. Focus on:
1. Contract type/structure (IDIQ, BPA, FFP, etc.)
2. Evaluation approach (LPTA, Best Value Tradeoff, etc.)
3. Security/compliance requirements (CMMC, CUI, DFARS clauses)
4. Timeline/schedule constraints
5. Budget/cost parameters
6. Performance requirements

For each assumption, provide:
- Clear, concise text (1-2 sentences)
- Source reference (document name and section)
- High confidence only (don't speculate)

DOCUMENT CONTEXT:
{context_text}

Respond with ONLY a JSON array in this exact format:
[
  {{
    "text": "Assumption text here",
    "source": "Document name Section X.Y"
  }},
  ...
]

If no clear assumptions can be extracted, return an empty array []."""
            }]
        )

        # Parse AI response
        import json
        import re

        response_text = message.content[0].text.strip()

        # Try to extract JSON from the response
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            assumptions_data = json.loads(json_match.group(0))
        else:
            # Fallback if no JSON found
            assumptions_data = []

        # Add IDs to assumptions
        assumptions = []
        for idx, assumption in enumerate(assumptions_data, 1):
            assumptions.append({
                "id": f"a{idx}",
                "text": assumption.get("text", ""),
                "source": assumption.get("source", "Unknown")
            })

        return {
            "assumptions": assumptions,
            "total": len(assumptions),
            "documents_analyzed": len(documents),
            "message": f"Extracted {len(assumptions)} assumptions from {len(documents)} documents"
        }

    except Exception as e:
        import traceback
        print(f"Error extracting assumptions: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting assumptions: {str(e)}"
        )


# ============================================================================
# Project Knowledge API - Project-Scoped Document Management
# ============================================================================

@app.get("/api/projects/{project_id}/knowledge", tags=["Knowledge"])
async def get_project_knowledge(
    project_id: str,
    phase: Optional[str] = Query(None, description="Filter by phase"),
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    current_user: User = Depends(get_current_user)
):
    """
    Get all knowledge documents for a specific project.
    
    Knowledge documents are reference materials (regulations, templates, market research, etc.)
    that are indexed into RAG and used to inform AI-generated documents.
    
    Optional filters:
    - phase: Filter by procurement phase (pre_solicitation, solicitation, post_solicitation)
    - purpose: Filter by document purpose (regulation, template, market_research, prior_award, strategy_memo)
    """
    try:
        rag_service = get_rag_service()
        
        # Get all RAG documents
        all_docs = rag_service.list_uploaded_documents()
        
        # Filter by project_id
        project_docs = []
        for doc in all_docs:
            metadata = doc.get('metadata', {})
            doc_project_id = metadata.get('project_id')
            
            # Include documents that match this project OR have no project_id (legacy docs)
            if doc_project_id == project_id:
                # Apply additional filters
                if phase and metadata.get('phase') != phase:
                    continue
                if purpose and metadata.get('purpose') != purpose:
                    continue
                
                project_docs.append({
                    "id": doc.get('filename', ''),
                    "project_id": project_id,
                    "filename": doc.get('filename', ''),
                    "file_type": doc.get('file_type', 'unknown'),
                    "file_size": doc.get('file_size', 0),
                    "phase": metadata.get('phase'),
                    "purpose": metadata.get('purpose'),
                    "upload_date": metadata.get('upload_timestamp', doc.get('upload_date', '')),
                    "uploaded_by": metadata.get('uploaded_by', ''),
                    "rag_indexed": True,  # If it's in RAG, it's indexed
                    "chunk_count": metadata.get('chunk_count'),
                    "chunk_ids": metadata.get('chunk_ids', [])
                })
        
        return {
            "documents": project_docs,
            "total": len(project_docs)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching project knowledge: {str(e)}"
        )


@app.get("/api/projects/{project_id}/knowledge/stats", tags=["Knowledge"])
async def get_project_knowledge_stats(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get knowledge document statistics for a project.
    
    Returns counts of documents grouped by phase and purpose,
    useful for displaying summary badges and filters.
    
    Response includes:
    - total: Total number of knowledge documents
    - by_phase: Count per phase (pre_solicitation, solicitation, post_solicitation)
    - by_purpose: Count per purpose (regulation, template, market_research, etc.)
    - indexed_count: Number of documents successfully indexed in RAG
    """
    try:
        rag_service = get_rag_service()
        
        # Get all RAG documents
        all_docs = rag_service.list_uploaded_documents()
        
        # Initialize stats structure
        stats = {
            "total": 0,
            "indexed_count": 0,
            "by_phase": {
                "pre_solicitation": 0,
                "solicitation": 0,
                "post_solicitation": 0,
                "unassigned": 0
            },
            "by_purpose": {
                "regulation": 0,
                "template": 0,
                "market_research": 0,
                "prior_award": 0,
                "strategy_memo": 0,
                "other": 0
            }
        }
        
        # Count documents for this project
        for doc in all_docs:
            metadata = doc.get('metadata', {})
            doc_project_id = metadata.get('project_id')
            
            # Only count documents matching this project
            if doc_project_id == project_id:
                stats["total"] += 1
                
                # Count indexed documents
                chunk_count = metadata.get('chunk_count', 0)
                if chunk_count and chunk_count > 0:
                    stats["indexed_count"] += 1
                
                # Count by phase
                doc_phase = metadata.get('phase')
                if doc_phase in stats["by_phase"]:
                    stats["by_phase"][doc_phase] += 1
                else:
                    stats["by_phase"]["unassigned"] += 1
                
                # Count by purpose
                doc_purpose = metadata.get('purpose')
                if doc_purpose in stats["by_purpose"]:
                    stats["by_purpose"][doc_purpose] += 1
                else:
                    stats["by_purpose"]["other"] += 1
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching knowledge stats: {str(e)}"
        )


@app.post("/api/projects/{project_id}/knowledge/upload", tags=["Knowledge"])
async def upload_project_knowledge(
    project_id: str,
    file: UploadFile = File(...),
    phase: str = Query(..., description="Procurement phase: pre_solicitation, solicitation, post_solicitation"),
    purpose: str = Query(..., description="Document purpose: regulation, template, market_research, prior_award, strategy_memo"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document to a project's knowledge base.
    
    The document is:
    1. Saved to storage
    2. Tagged with project_id, phase, and purpose
    3. Processed and indexed into the RAG vector store
    
    This makes the document available for AI-powered document generation
    with full traceability to the source.
    
    Args:
        project_id: The project to associate this document with
        file: The document file (PDF, DOCX, TXT, MD, XLSX, PPTX)
        phase: The procurement phase this document supports
        purpose: The document's purpose/category
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.txt', '.md', '.xlsx', '.pptx', '.doc'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate phase
        valid_phases = ['pre_solicitation', 'solicitation', 'post_solicitation']
        if phase not in valid_phases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
            )
        
        # Validate purpose
        valid_purposes = ['regulation', 'template', 'market_research', 'prior_award', 'strategy_memo']
        if purpose not in valid_purposes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid purpose. Must be one of: {', '.join(valid_purposes)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Get RAG service and upload with project metadata
        rag_service = get_rag_service()
        
        # Upload with enhanced metadata including project_id, phase, and purpose
        result = rag_service.upload_and_process_document(
            file_content=content,
            filename=file.filename,
            user_id=str(current_user.id),
            metadata={
                "project_id": project_id,
                "phase": phase,
                "purpose": purpose,
                "category": purpose  # For backward compatibility with existing RAG queries
            }
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to process document")
            )
        
        return {
            "id": result.get("saved_as", file.filename),
            "filename": file.filename,
            "file_type": file_ext.replace('.', ''),
            "file_size": result.get("file_size", len(content)),
            "chunks_created": result.get("chunks_created", 0),
            "chunk_ids": result.get("chunk_ids", []),
            "message": f"Successfully uploaded and indexed {file.filename} for project"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error uploading project knowledge: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@app.delete("/api/projects/{project_id}/knowledge/{document_id}", tags=["Knowledge"])
async def delete_project_knowledge(
    project_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document from a project's knowledge base.
    
    This removes the document file and its associated chunks from the RAG vector store.
    AI-generated documents that previously used this source will not be affected.
    """
    try:
        rag_service = get_rag_service()
        
        # Delete from RAG
        result = rag_service.delete_document(document_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Document not found")
            )
        
        return {
            "message": f"Successfully deleted {document_id}",
            "deleted_chunks": result.get("deleted_chunks", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


# ============================================================================
# Document Lineage API - Track Sources of AI-Generated Content
# ============================================================================

@app.get("/api/documents/{document_id}/lineage", tags=["Lineage"])
async def get_document_lineage(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get lineage information for a document.
    
    For AI-generated documents: Returns source documents that influenced generation
    For uploaded documents: Returns documents that were derived from this source
    
    This provides explainability for AI decisions by showing:
    - Which source documents were used
    - How relevant each source was (relevance_score)
    - Which RAG chunks were retrieved
    """
    try:
        from backend.models.lineage import DocumentLineage
        
        # Get lineage records where this document is the derived document (sources)
        sources_query = db.query(DocumentLineage).filter(
            DocumentLineage.derived_document_id == document_id
        ).all()
        
        # Get lineage records where this document is the source (derived documents)
        derived_query = db.query(DocumentLineage).filter(
            DocumentLineage.source_document_id == document_id
        ).all()
        
        # Also check by source_filename for RAG-only documents
        derived_by_filename = db.query(DocumentLineage).filter(
            DocumentLineage.source_filename.isnot(None)
        ).all()
        
        sources = [lineage.to_dict() for lineage in sources_query]
        derived = [lineage.to_dict() for lineage in derived_query]
        
        return {
            "document_id": document_id,
            "sources": sources,  # Documents that influenced this one
            "derived_from_this": derived,  # Documents created from this source
            "total_sources": len(sources),
            "total_derived": len(derived)
        }
        
    except Exception as e:
        import traceback
        print(f"Error fetching lineage: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching lineage: {str(e)}"
        )


class LineageRecordRequest(BaseModel):
    """Request model for creating a lineage record"""
    source_document_id: Optional[str] = None
    source_filename: Optional[str] = None
    influence_type: str = "data_source"
    relevance_score: float = 0.0
    chunk_ids_used: List[str] = []
    context: Optional[str] = None


@app.post("/api/documents/{document_id}/lineage", tags=["Lineage"])
async def record_document_lineage(
    document_id: str,
    request: LineageRecordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record a lineage relationship for a document.
    
    Called after AI generation to record which source documents were used.
    
    Args:
        document_id: The derived (generated) document ID
        request: Lineage details including source, influence type, and relevance
    """
    try:
        from backend.models.lineage import DocumentLineage, InfluenceType
        import uuid as uuid_lib
        
        # Create lineage record
        lineage = DocumentLineage(
            id=uuid_lib.uuid4(),
            source_document_id=request.source_document_id,
            source_filename=request.source_filename,
            derived_document_id=document_id,
            influence_type=InfluenceType(request.influence_type),
            relevance_score=request.relevance_score,
            chunk_ids_used=request.chunk_ids_used,
            chunks_used_count=len(request.chunk_ids_used),
            context=request.context
        )
        
        db.add(lineage)
        db.commit()
        db.refresh(lineage)
        
        return {
            "id": str(lineage.id),
            "message": "Lineage record created successfully",
            "derived_document_id": document_id,
            "source": request.source_document_id or request.source_filename
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error recording lineage: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording lineage: {str(e)}"
        )


@app.post("/api/documents/{document_id}/lineage/batch", tags=["Lineage"])
async def record_batch_lineage(
    document_id: str,
    sources: List[LineageRecordRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record multiple lineage relationships at once.
    
    Used after AI generation to record all sources in a single transaction.
    More efficient than individual calls for bulk lineage recording.
    """
    try:
        from backend.models.lineage import DocumentLineage, InfluenceType
        import uuid as uuid_lib
        
        created_records = []
        
        for source in sources:
            lineage = DocumentLineage(
                id=uuid_lib.uuid4(),
                source_document_id=source.source_document_id,
                source_filename=source.source_filename,
                derived_document_id=document_id,
                influence_type=InfluenceType(source.influence_type),
                relevance_score=source.relevance_score,
                chunk_ids_used=source.chunk_ids_used,
                chunks_used_count=len(source.chunk_ids_used),
                context=source.context
            )
            db.add(lineage)
            created_records.append(str(lineage.id))
        
        db.commit()
        
        return {
            "message": f"Created {len(created_records)} lineage records",
            "derived_document_id": document_id,
            "lineage_ids": created_records,
            "sources_count": len(sources)
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error recording batch lineage: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording batch lineage: {str(e)}"
        )


@app.get("/api/chunks", tags=["Lineage"])
async def get_chunk_content(
    ids: str = Query(..., description="Comma-separated list of chunk IDs"),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve content for specific RAG chunks by their IDs.
    
    Used for chunk-level traceability in the document lineage view,
    allowing users to see exactly which content segments influenced
    AI-generated documents.
    
    Args:
        ids: Comma-separated list of chunk IDs (e.g., "chunk_1,chunk_2,chunk_3")
        
    Returns:
        List of chunk objects with content, source document info, and metadata
    """
    try:
        from backend.services.rag_service import get_rag_service
        
        # Parse comma-separated chunk IDs
        chunk_ids = [id.strip() for id in ids.split(",") if id.strip()]
        
        if not chunk_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid chunk IDs provided"
            )
        
        # Limit to prevent abuse (max 50 chunks per request)
        if len(chunk_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 chunk IDs per request"
            )
        
        # Get RAG service and retrieve chunks
        rag_service = get_rag_service()
        chunks = rag_service.get_chunks_by_ids(chunk_ids)
        
        return {
            "chunks": chunks,
            "requested_count": len(chunk_ids),
            "found_count": len(chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error fetching chunks: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chunk content: {str(e)}"
        )


@app.get("/api/documents/{document_id}/timeline", tags=["Lineage"])
async def get_document_timeline(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get lifecycle timeline events for a document.
    
    Returns a chronological list of events in the document's lifecycle:
    - uploaded: When the document was created/uploaded
    - indexed: When RAG indexing completed (for knowledge documents)
    - generated: When AI generation occurred (for AI-generated documents)
    - used_as_source: When this document influenced other generations
    
    This provides a complete audit trail for compliance and explainability.
    """
    try:
        from backend.models.document import ProjectDocument
        from backend.models.lineage import DocumentLineage, KnowledgeDocument
        
        events = []
        
        # 1. Get the main document info
        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # 2. Add creation/upload event
        if document.created_at:
            events.append({
                "type": "uploaded",
                "timestamp": document.created_at.isoformat(),
                "actor": str(document.assigned_user_id) if document.assigned_user_id else None,
                "details": {
                    "document_name": document.document_name,
                    "category": document.category,
                    "phase": document.phase.value if document.phase else None
                }
            })
        
        # 3. Check if this is an AI-generated document and add generation event
        if document.generation_status and document.generation_status.value == "GENERATED":
            if document.generated_at:
                # Count sources used from lineage
                sources_count = db.query(DocumentLineage).filter(
                    DocumentLineage.derived_document_id == document_id
                ).count()
                
                events.append({
                    "type": "generated",
                    "timestamp": document.generated_at.isoformat(),
                    "actor": None,  # AI generated
                    "details": {
                        "sources_used": sources_count,
                        "quality_score": document.ai_quality_score
                    }
                })
        
        # 4. Check for knowledge document indexing events
        # Look for matching knowledge document by filename pattern
        knowledge_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.project_id == document.project_id
        ).first()
        
        if knowledge_doc and knowledge_doc.rag_indexed:
            events.append({
                "type": "indexed",
                "timestamp": knowledge_doc.created_at.isoformat() if knowledge_doc.created_at else None,
                "actor": str(knowledge_doc.uploaded_by) if knowledge_doc.uploaded_by else None,
                "details": {
                    "chunks_created": knowledge_doc.chunk_count,
                    "filename": knowledge_doc.filename
                }
            })
        
        # 5. Check for "used as source" events - when this doc influenced others
        derived_lineages = db.query(DocumentLineage).filter(
            DocumentLineage.source_document_id == document_id
        ).all()
        
        for lineage in derived_lineages:
            # Get the derived document for details
            derived_doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == lineage.derived_document_id
            ).first()
            
            if derived_doc and lineage.created_at:
                events.append({
                    "type": "used_as_source",
                    "timestamp": lineage.created_at.isoformat(),
                    "actor": None,
                    "details": {
                        "derived_document_id": str(lineage.derived_document_id),
                        "derived_document_name": derived_doc.document_name if derived_doc else None,
                        "influence_type": lineage.influence_type.value if lineage.influence_type else None,
                        "relevance_score": lineage.relevance_score,
                        "chunks_used": lineage.chunks_used_count
                    }
                })
        
        # 6. Sort events by timestamp (oldest first for timeline display)
        events.sort(key=lambda x: x.get("timestamp") or "")
        
        return {
            "document_id": document_id,
            "document_name": document.document_name,
            "events": events,
            "total_events": len(events)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error fetching document timeline: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching document timeline: {str(e)}"
        )


@app.get("/api/documents/{document_id}/influence-graph", tags=["Lineage"])
async def get_influence_graph(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get influence graph data for document visualization.
    
    Returns a graph structure showing:
    - nodes: All documents in the influence chain (sources and derived)
    - edges: Lineage relationships with relevance weights
    
    Used to render an interactive influence graph showing how knowledge
    documents influenced AI-generated content.
    """
    try:
        from backend.models.document import ProjectDocument
        from backend.models.lineage import DocumentLineage
        
        nodes = {}  # Use dict to deduplicate by document ID
        edges = []
        
        # 1. Get the main document
        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # Determine if this is a source or generated document
        is_generated = document.generation_status and document.generation_status.value == "GENERATED"
        
        # Add the main document as a node
        nodes[document_id] = {
            "id": document_id,
            "label": document.document_name,
            "type": "generated" if is_generated else "source",
            "metadata": {
                "category": document.category,
                "phase": document.phase.value if document.phase else None,
                "status": document.status.value if document.status else None,
                "generation_status": document.generation_status.value if document.generation_status else None
            }
        }
        
        # 2. Get sources that influenced this document
        source_lineages = db.query(DocumentLineage).filter(
            DocumentLineage.derived_document_id == document_id
        ).all()
        
        for lineage in source_lineages:
            # Add source node
            source_id = str(lineage.source_document_id) if lineage.source_document_id else lineage.source_filename
            
            if source_id and source_id not in nodes:
                # Try to get source document details
                if lineage.source_document_id:
                    source_doc = db.query(ProjectDocument).filter(
                        ProjectDocument.id == lineage.source_document_id
                    ).first()
                    if source_doc:
                        nodes[source_id] = {
                            "id": source_id,
                            "label": source_doc.document_name,
                            "type": "source",
                            "metadata": {
                                "category": source_doc.category,
                                "phase": source_doc.phase.value if source_doc.phase else None
                            }
                        }
                    else:
                        # Document not found, use lineage info
                        nodes[source_id] = {
                            "id": source_id,
                            "label": lineage.source_filename or "Unknown Source",
                            "type": "source",
                            "metadata": {}
                        }
                else:
                    # RAG-only source (filename without project document)
                    nodes[source_id] = {
                        "id": source_id,
                        "label": lineage.source_filename or "RAG Source",
                        "type": "source",
                        "metadata": {
                            "is_rag_file": True
                        }
                    }
            
            # Add edge from source to this document
            if source_id:
                edges.append({
                    "source": source_id,
                    "target": document_id,
                    "weight": lineage.relevance_score or 0.0,
                    "chunks_count": lineage.chunks_used_count or 0,
                    "influence_type": lineage.influence_type.value if lineage.influence_type else "data_source"
                })
        
        # 3. Get documents derived from this one (if it's a source)
        derived_lineages = db.query(DocumentLineage).filter(
            DocumentLineage.source_document_id == document_id
        ).all()
        
        for lineage in derived_lineages:
            derived_id = str(lineage.derived_document_id)
            
            if derived_id not in nodes:
                derived_doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == lineage.derived_document_id
                ).first()
                
                if derived_doc:
                    nodes[derived_id] = {
                        "id": derived_id,
                        "label": derived_doc.document_name,
                        "type": "generated",
                        "metadata": {
                            "category": derived_doc.category,
                            "phase": derived_doc.phase.value if derived_doc.phase else None
                        }
                    }
            
            # Add edge from this document to derived
            edges.append({
                "source": document_id,
                "target": derived_id,
                "weight": lineage.relevance_score or 0.0,
                "chunks_count": lineage.chunks_used_count or 0,
                "influence_type": lineage.influence_type.value if lineage.influence_type else "data_source"
            })
        
        return {
            "document_id": document_id,
            "nodes": list(nodes.values()),
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error fetching influence graph: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching influence graph: {str(e)}"
        )


# ============================================================================
# Document Generation Endpoints
# ============================================================================

# In-memory task storage (in production, use Redis or database)
generation_tasks = {}

from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import asyncio


class DocumentRequest(BaseModel):
    name: str
    section: Optional[str] = None
    category: str
    linkedAssumptions: List[str]


class GenerateDocumentsRequest(BaseModel):
    assumptions: List[Dict[str, str]]
    documents: List[DocumentRequest]


class AnalyzeDocumentsRequest(BaseModel):
    document_names: List[str]


@app.post("/api/analyze-generation-plan", tags=["Generation"])
async def analyze_generation_plan(
    request: AnalyzeDocumentsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze document selection and provide phase detection, recommendations, and validation

    This endpoint helps users understand:
    - Which procurement phase their documents belong to
    - Whether documents from mixed phases are selected
    - What additional documents might be needed
    - Phase completeness status
    """
    try:
        # Get coordinator (with specialized agents enabled)
        coordinator = get_generation_coordinator(use_specialized_agents=True)

        # Analyze the plan
        analysis = coordinator.analyze_generation_plan(request.document_names)

        return {
            "status": "success",
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze generation plan: {str(e)}"
        )


@app.post("/api/generate-documents", tags=["Generation"])
async def generate_documents(
    request: GenerateDocumentsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate acquisition documents based on assumptions and selected document types

    This endpoint kicks off an asynchronous generation task that:
    1. Uses RAG to retrieve relevant context
    2. Calls specialized agents to generate each document section
    3. Validates and formats the output
    4. Returns structured sections ready for the editor
    """
    try:
        task_id = str(uuid.uuid4())

        # Initialize task status
        generation_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": "Initializing document generation...",
            "result": None,
            "documents_requested": len(request.documents),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }

        # Start generation in background
        asyncio.create_task(run_document_generation(task_id, request))

        return {
            "message": "Document generation started",
            "task_id": task_id,
            "documents_requested": len(request.documents)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start document generation: {str(e)}"
        )


@app.get("/api/generation-status/{task_id}", tags=["Generation"])
async def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a document generation task"""
    if task_id not in generation_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return generation_tasks[task_id]


async def run_document_generation(task_id: str, request: GenerateDocumentsRequest):
    """
    Background task to generate documents using specialized agents and RAG
    """
    try:
        # Check if specialized agents should be used (feature flag)
        use_specialized_agents = os.getenv("USE_AGENT_BASED_GENERATION", "true").lower() == "true"

        # Get generation coordinator
        coordinator = get_generation_coordinator(use_specialized_agents=use_specialized_agents)

        # Extract document names and linked assumptions
        document_names = [doc.name for doc in request.documents]
        linked_assumptions = {
            doc.name: doc.linkedAssumptions
            for doc in request.documents
        }

        # Create generation task
        gen_task = GenerationTask(
            task_id=task_id,
            document_names=document_names,
            assumptions=request.assumptions,
            linked_assumptions=linked_assumptions
        )

        # Progress callback to update global task status
        def update_progress(task: GenerationTask):
            generation_tasks[task_id]["status"] = task.status
            generation_tasks[task_id]["progress"] = task.progress
            generation_tasks[task_id]["message"] = task.message

        # Run generation with progress tracking
        completed_task = await coordinator.generate_documents(
            task=gen_task,
            progress_callback=update_progress
        )

        # Update final result
        if completed_task.status == "completed":
            generation_tasks[task_id]["status"] = "completed"
            generation_tasks[task_id]["progress"] = 100
            generation_tasks[task_id]["message"] = "Document generation complete!"
            generation_tasks[task_id]["result"] = {
                "sections": completed_task.sections,
                "citations": completed_task.citations,
                "agent_metadata": completed_task.agent_metadata,
                "phase_info": completed_task.phase_info,
                "collaboration_metadata": completed_task.collaboration_metadata,  # Phase 4
                "quality_analysis": completed_task.quality_analysis  # Precomputed quality scores per section
            }
        else:
            generation_tasks[task_id]["status"] = "failed"
            generation_tasks[task_id]["message"] = completed_task.message
            generation_tasks[task_id]["errors"] = completed_task.errors

    except Exception as e:
        import traceback
        print(f"Error in document generation: {str(e)}")
        print(traceback.format_exc())

        generation_tasks[task_id]["status"] = "failed"
        generation_tasks[task_id]["message"] = f"Generation failed: {str(e)}"


# ============================================================================
# Agent Comparison Endpoints (Phase 6)
# ============================================================================

class AgentVariantRequest(BaseModel):
    """Request model for agent variant configuration"""
    id: str
    name: str
    model: str
    temperature: float
    agentClass: Optional[str] = None
    description: str


class ComparisonRequest(BaseModel):
    """Request model for agent comparison"""
    documentName: str
    requirements: str
    variants: List[AgentVariantRequest]
    context: str = ""


@app.post("/api/comparison/start", tags=["Comparison"])
async def start_comparison(
    request: ComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a multi-agent comparison task

    Generates the same document with different agents/models to compare results.
    """
    try:
        comparison_service = get_comparison_service()

        # Convert request variants to AgentVariant objects
        variants = [
            AgentVariant(
                variant_id=v.id,
                name=v.name,
                model=v.model,
                temperature=v.temperature,
                agent_class=v.agentClass,
                description=v.description
            )
            for v in request.variants
        ]

        # Create comparison task
        task_id = comparison_service.create_comparison_task(
            document_name=request.documentName,
            requirements=request.requirements,
            variants=variants,
            context=request.context
        )

        # Run comparison in background
        import asyncio
        asyncio.create_task(comparison_service.run_comparison(task_id))

        return {
            "status": "success",
            "task_id": task_id,
            "variants_count": len(variants),
            "message": f"Comparison started for {request.documentName}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start comparison: {str(e)}"
        )


@app.get("/api/comparison/status/{task_id}", tags=["Comparison"])
async def get_comparison_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a comparison task"""
    try:
        comparison_service = get_comparison_service()
        status_data = comparison_service.get_comparison_status(task_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comparison task {task_id} not found"
            )

        return status_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison status: {str(e)}"
        )


@app.get("/api/comparison/results/{task_id}", tags=["Comparison"])
async def get_comparison_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get full results of a comparison task"""
    try:
        comparison_service = get_comparison_service()
        results = comparison_service.get_comparison_results(task_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comparison task {task_id} not found"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison results: {str(e)}"
        )


@app.get("/api/comparison/winner/{task_id}", tags=["Comparison"])
async def get_comparison_winner(
    task_id: str,
    criteria: str = Query("quality", pattern="^(quality|speed|length|citations)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get the winning variant based on specified criteria

    - **quality**: Highest quality score
    - **speed**: Fastest generation time
    - **length**: Most words
    - **citations**: Most citations
    """
    try:
        comparison_service = get_comparison_service()
        winner = comparison_service.get_winner(task_id, criteria)

        if not winner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comparison task {task_id} not found or has no results"
            )

        return {
            "task_id": task_id,
            "criteria": criteria,
            "winner": {
                "variant_id": winner.variant.variant_id,
                "variant_name": winner.variant.name,
                "model": winner.variant.model,
                "quality_score": winner.quality_score,
                "generation_time": winner.generation_time,
                "word_count": winner.word_count,
                "citations_count": winner.citations_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison winner: {str(e)}"
        )


# ============================================================================
# Export Endpoints
# ============================================================================

# Pydantic models for export requests
class ExportPrepareRequest(BaseModel):
    """
    Request model for export preparation
    
    Attributes:
        sections: Dictionary of section name -> HTML content
        citations: List of citation dictionaries
        metadata: Document metadata
        section_order: Optional custom section order
        selected_sections: Optional list of specific sections to export (None = all)
    """
    sections: Dict[str, str]
    citations: List[Dict] = []
    metadata: Dict = {}
    section_order: Optional[List[str]] = None
    selected_sections: Optional[List[str]] = None  # NEW: Filter to specific sections


class ComplianceReportRequest(BaseModel):
    compliance_analysis: Dict


# Initialize export service
export_service = ExportService()


@app.post("/api/export/prepare", tags=["Export"])
async def prepare_export(request: ExportPrepareRequest = Body(...)):
    """
    Prepare export by assembling document and creating temporary files

    Returns export_id and estimated file sizes
    
    If selected_sections is provided, only those sections will be exported.
    Otherwise, all sections are exported.
    """
    try:
        # Filter sections if specific ones are requested
        # This enables individual document/section export
        sections_to_export = request.sections
        if request.selected_sections:
            sections_to_export = {
                name: content 
                for name, content in request.sections.items() 
                if name in request.selected_sections
            }
        
        # Determine section order for filtered sections
        section_order = request.section_order
        if request.selected_sections and section_order:
            # Filter section_order to only include selected sections
            section_order = [s for s in section_order if s in request.selected_sections]
        elif request.selected_sections:
            # Use selected_sections order if no explicit order provided
            section_order = request.selected_sections
        
        export_id, file_sizes = export_service.prepare_export(
            sections=sections_to_export,
            citations=request.citations,
            metadata=request.metadata,
            section_order=section_order
        )

        return {
            "export_id": export_id,
            "file_sizes": file_sizes,
            "status": "ready",
            "sections_exported": list(sections_to_export.keys())  # Return what was actually exported
        }
    except Exception as e:
        import traceback
        print(f"Error preparing export: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Export preparation failed: {str(e)}")


@app.get("/api/export/{export_id}/pdf", tags=["Export"])
async def download_pdf(export_id: str):
    """
    Generate and download PDF file
    """
    try:
        pdf_file = export_service.generate_pdf(export_id)

        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename="document.pdf"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Export {export_id} not found")
    except Exception as e:
        import traceback
        print(f"Error generating PDF: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.get("/api/export/{export_id}/docx", tags=["Export"])
async def download_docx(export_id: str, program_name: Optional[str] = None):
    """
    Generate and download DOCX file
    """
    try:
        docx_file = export_service.generate_docx(export_id, program_name)

        return FileResponse(
            path=str(docx_file),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="document.docx"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Export {export_id} not found")
    except Exception as e:
        import traceback
        print(f"Error generating DOCX: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")


@app.get("/api/export/{export_id}/json", tags=["Export"])
async def download_json(export_id: str):
    """
    Download JSON metadata file
    """
    try:
        json_file = export_service.generate_json(export_id)

        return FileResponse(
            path=str(json_file),
            media_type="application/json",
            filename="metadata.json"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Export {export_id} not found")
    except Exception as e:
        import traceback
        print(f"Error retrieving JSON: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"JSON retrieval failed: {str(e)}")


@app.post("/api/export/compliance-report", tags=["Export"])
async def generate_compliance_report(request: ComplianceReportRequest = Body(...)):
    """
    Generate compliance report PDF
    """
    try:
        pdf_file = export_service.generate_compliance_report(
            compliance_analysis=request.compliance_analysis
        )

        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename="compliance_report.pdf"
        )
    except Exception as e:
        import traceback
        print(f"Error generating compliance report: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Compliance report generation failed: {str(e)}")


@app.get("/api/export/history", tags=["Export"])
async def get_export_history(max_count: int = 10):
    """
    Get list of recent exports
    """
    try:
        history = export_service.get_export_history(max_count)
        return {"exports": history}
    except Exception as e:
        import traceback
        print(f"Error retrieving export history: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve export history: {str(e)}")


@app.delete("/api/export/cleanup", tags=["Export"])
async def cleanup_old_exports(max_age_hours: int = 24):
    """
    Clean up exports older than specified hours (default: 24)
    """
    try:
        export_service.cleanup_old_exports(max_age_hours)
        return {"status": "success", "message": f"Cleaned up exports older than {max_age_hours} hours"}
    except Exception as e:
        import traceback
        print(f"Error cleaning up exports: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


class BatchExportRequest(BaseModel):
    """Request model for batch export of generated documents"""
    document_ids: List[str]  # List of ProjectDocument IDs to export
    format: str = "pdf"  # Export format: 'pdf', 'docx', or 'markdown'


@app.post("/api/projects/{project_id}/export-generated-batch", tags=["Export"])
async def export_generated_batch(
    project_id: str,
    request: BatchExportRequest,
    db: Session = Depends(get_db)
):
    """
    Batch export multiple AI-generated documents as a ZIP file.
    
    Accepts a list of document IDs and an export format.
    Returns a ZIP file containing all exported documents.
    
    Supported formats:
    - pdf: PDF files
    - docx: Microsoft Word documents
    - markdown: Raw markdown files
    """
    import zipfile
    import io
    import tempfile
    
    try:
        # Validate project exists
        project = db.query(ProcurementProject).filter(
            ProcurementProject.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Fetch the specified documents
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(request.document_ids),
            ProjectDocument.project_id == project_id,
            ProjectDocument.generation_status == GenerationStatus.GENERATED
        ).all()
        
        if not documents:
            raise HTTPException(
                status_code=404, 
                detail="No generated documents found with the specified IDs"
            )
        
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documents:
                if not doc.generated_content:
                    continue
                
                # Sanitize filename
                safe_name = doc.document_name.replace('/', '-').replace('\\', '-').replace(' ', '_')
                
                if request.format == 'markdown':
                    # Add markdown file directly
                    filename = f"{safe_name}.md"
                    zip_file.writestr(filename, doc.generated_content)
                    
                elif request.format == 'pdf':
                    # Create temporary files for PDF conversion
                    with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w') as md_temp:
                        md_temp.write(doc.generated_content)
                        md_path = md_temp.name
                    
                    pdf_path = md_path.replace('.md', '.pdf')
                    
                    try:
                        # Convert to PDF using existing utility
                        from backend.utils.convert_md_to_pdf import convert_markdown_to_pdf
                        convert_markdown_to_pdf(md_path, pdf_path)
                        
                        # Add PDF to ZIP
                        filename = f"{safe_name}.pdf"
                        with open(pdf_path, 'rb') as pdf_file:
                            zip_file.writestr(filename, pdf_file.read())
                    finally:
                        # Clean up temp files
                        import os
                        if os.path.exists(md_path):
                            os.remove(md_path)
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                            
                elif request.format == 'docx':
                    # Create temporary files for DOCX conversion
                    with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w') as md_temp:
                        md_temp.write(doc.generated_content)
                        md_path = md_temp.name
                    
                    docx_path = md_path.replace('.md', '.docx')
                    
                    try:
                        # Convert to DOCX using existing utility
                        from backend.utils.convert_md_to_docx import convert_markdown_to_docx
                        convert_markdown_to_docx(md_path, docx_path, doc.document_name)
                        
                        # Add DOCX to ZIP
                        filename = f"{safe_name}.docx"
                        with open(docx_path, 'rb') as docx_file:
                            zip_file.writestr(filename, docx_file.read())
                    finally:
                        # Clean up temp files
                        import os
                        if os.path.exists(md_path):
                            os.remove(md_path)
                        if os.path.exists(docx_path):
                            os.remove(docx_path)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported format: {request.format}. Use 'pdf', 'docx', or 'markdown'"
                    )
        
        # Reset buffer position
        zip_buffer.seek(0)
        
        # Generate filename for the ZIP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{project.name.replace(' ', '_')}_generated_docs_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in batch export: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Batch export failed: {str(e)}")


# ============================================================================
# Guided Flow Endpoints
# ============================================================================

class GuidedFlowSaveRequest(BaseModel):
    document_id: str
    field_values: Dict[str, Any]
    user_id: str

class GuidedFlowSuggestionRequest(BaseModel):
    document_id: str
    field_id: str
    user_id: str
    company_name: Optional[str] = None
    suggest_from_previous: bool = True
    suggest_from_rag: bool = False
    custom_prompt: Optional[str] = None


@app.get("/api/guided-flow/document/{document_id}", tags=["Guided Flow"])
async def get_guided_document(document_id: str):
    """
    Get guided document structure by ID

    Returns the document structure with all fields, sections, and metadata
    for guided completion flow.
    """
    try:
        # For MVP, return Section K example
        # In production, this would fetch from database based on document_id
        from backend.data.guided_documents import get_section_k_document

        document = get_section_k_document()

        return {
            "success": True,
            "document": document
        }
    except Exception as e:
        import traceback
        print(f"Error retrieving guided document: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve guided document: {str(e)}")


@app.post("/api/guided-flow/save", tags=["Guided Flow"])
async def save_guided_progress(
    request: GuidedFlowSaveRequest,
    db: Session = Depends(get_db)
):
    """
    Save guided flow progress

    Saves current field values and progress for a guided document.
    Auto-save triggered on field completion.
    """
    try:
        # Store field values in database
        # For MVP, we'll just return success
        # In production, store in ProjectDocument table with field_values JSON column

        print(f"Saving guided flow progress for document {request.document_id}")
        print(f"Fields saved: {len(request.field_values)}")

        return {
            "success": True,
            "document_id": request.document_id,
            "saved_at": "2025-11-19T12:00:00Z",
            "fields_saved": len(request.field_values)
        }
    except Exception as e:
        import traceback
        print(f"Error saving guided flow progress: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save progress: {str(e)}")


@app.post("/api/guided-flow/suggest", tags=["Guided Flow"])
async def get_field_suggestion(request: GuidedFlowSuggestionRequest):
    """
    Get AI-powered field suggestion

    Returns smart suggestions based on:
    - Previous contract data (if suggest_from_previous=true)
    - RAG knowledge base (if suggest_from_rag=true)
    - Custom AI prompt
    """
    try:
        import anthropic
        from anthropic import Anthropic

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

        client = Anthropic(api_key=api_key)

        # Build prompt based on suggestion sources
        prompt_parts = []

        if request.suggest_from_previous:
            prompt_parts.append(f"Based on previous contracts for company: {request.company_name or 'Unknown'}")

        if request.suggest_from_rag:
            # Query RAG for relevant context
            rag_service = get_rag_service()
            rag_context = await rag_service.retrieve_context(
                document_name="Section K",
                query=f"field {request.field_id}"
            )
            prompt_parts.append(f"Knowledge base context: {rag_context}")

        if request.custom_prompt:
            prompt_parts.append(request.custom_prompt)

        combined_prompt = "\n\n".join(prompt_parts)
        combined_prompt += f"\n\nProvide a suggested value for field '{request.field_id}'. Return ONLY the value, no explanation."

        # Call Claude for suggestion
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": combined_prompt
            }]
        )

        suggested_value = response.content[0].text.strip()

        # Determine confidence (simplified for MVP)
        confidence = 0.8 if request.suggest_from_previous else 0.6

        # Determine source
        source = "previous_contract" if request.suggest_from_previous else \
                 "rag_knowledge" if request.suggest_from_rag else \
                 "ai_generated"

        return {
            "value": suggested_value,
            "source": source,
            "confidence": confidence,
            "explanation": f"Suggested based on {source}",
            "contract_id": "CONTRACT-2024-001" if request.suggest_from_previous else None
        }
    except Exception as e:
        import traceback
        print(f"Error getting field suggestion: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")


# WebSocket for Real-Time Collaboration
@app.websocket("/api/ws/guided-flow/{document_id}")
async def guided_flow_websocket(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time guided flow collaboration

    Handles:
    - Field updates from collaborators
    - Field locking when someone is editing
    - Collaborator presence (join/leave)
    """
    await ws_manager.connect(websocket, room=f"guided-flow-{document_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("event")

            # Broadcast to all users in this document room
            await ws_manager.broadcast(
                data,
                room=f"guided-flow-{document_id}",
                exclude=websocket  # Don't send back to sender
            )

            # Log event
            print(f"[Guided Flow WS] {event_type} - Document: {document_id}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room=f"guided-flow-{document_id}")
        print(f"[Guided Flow WS] Client disconnected from document {document_id}")
    except Exception as e:
        print(f"[Guided Flow WS] Error: {str(e)}")
        ws_manager.disconnect(websocket, room=f"guided-flow-{document_id}")


# ============================================================================
# Copilot AI Assistant Endpoints
# ============================================================================

class CopilotAssistRequest(BaseModel):
    """Request model for Copilot AI assistance"""
    action: str  # answer, rewrite, expand, summarize, citations, compliance, custom, web_search, fix_issue
    selected_text: str
    context: str = ""  # Surrounding text for better understanding
    custom_prompt: Optional[str] = None  # For custom action
    section_name: str = ""
    search_type: Optional[str] = None  # For web_search: general, vendor, pricing, awards, small_business


@app.post("/api/copilot/assist", tags=["Copilot"])
async def copilot_assist(
    request: CopilotAssistRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI Copilot assistance for document editing
    
    Provides intelligent assistance based on selected text:
    - answer: Answer questions about the highlighted text
    - rewrite: Improve/rewrite the selected text
    - expand: Elaborate on the selected content
    - summarize: Summarize the selected text
    - citations: Add FAR/DFARS citations to the selection
    - compliance: Check selection for compliance issues
    - custom: Execute custom user prompt on selection
    - fix_issue: Generate AI-powered contextual fix for placeholders (e.g., TBD)
    
    Returns:
        AI-generated response based on the action type
    """
    try:
        import anthropic
        from anthropic import Anthropic

        # Load configuration from external file (editable without code changes)
        from backend.config.copilot_config_loader import get_copilot_config
        config = get_copilot_config()

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

        client = Anthropic(api_key=api_key)

        # Get system prompt from config (includes dynamic date)
        system_prompt = config.get_system_prompt()

        # Extract request parameters
        action = request.action.lower()
        selected_text = request.selected_text
        context = request.context
        section = request.section_name

        # Handle standard actions via config
        if action in config.get_available_actions():
            # Validate custom action has prompt
            if action == "custom" and not request.custom_prompt:
                raise HTTPException(status_code=400, detail="Custom prompt required for 'custom' action")

            # Build prompt from config template
            user_prompt = config.get_action_prompt(
                action=action,
                selected_text=selected_text,
                context=context,
                section=section,
                custom_prompt=request.custom_prompt
            )

        elif action == "web_search":
            # Web search using Tavily API
            try:
                from backend.agents.tools.web_search_tool import WebSearchTool
                
                # Initialize web search tool
                web_search = WebSearchTool()
                
                # Determine search type and execute appropriate search
                search_type = request.search_type or "general"
                search_results = []
                
                if search_type == "vendor":
                    # Search for vendor information
                    search_results = web_search.search_vendor_information(selected_text)
                elif search_type == "pricing":
                    # Search for market pricing
                    search_results = web_search.search_market_pricing(selected_text)
                elif search_type == "awards":
                    # Search for recent contract awards
                    search_results = web_search.search_recent_awards(selected_text)
                elif search_type == "small_business":
                    # Search for small business info
                    search_results = web_search.search_small_business_info(selected_text)
                else:
                    # General web search
                    search_results = web_search.search(
                        query=f"{selected_text} government acquisition DoD procurement",
                        max_results=5,
                        search_depth="advanced"
                    )
                
                # Format results for display
                if search_results:
                    formatted_results = "## Web Search Results\n\n"
                    for i, result in enumerate(search_results, 1):
                        formatted_results += f"### {i}. {result.get('title', 'Untitled')}\n"
                        formatted_results += f"**Source:** [{result.get('url', 'N/A')}]({result.get('url', '#')})\n\n"
                        formatted_results += f"{result.get('content', 'No content available')}\n\n"
                        if result.get('published_date'):
                            formatted_results += f"*Published: {result.get('published_date')}*\n\n"
                        formatted_results += "---\n\n"
                    
                    # Use Claude to synthesize results into a helpful summary
                    synthesis_prompt = f"""Based on the following web search results about "{selected_text}", provide a helpful summary for a government acquisition professional:

{formatted_results}

CONTEXT FROM DOCUMENT:
{context if context else 'No additional context provided'}

Please provide:
1. Key findings relevant to government acquisition
2. Any pricing or market data found
3. Relevant vendors or contractors mentioned
4. Important considerations or recommendations

Format your response clearly with headers and bullet points."""

                    user_prompt = synthesis_prompt
                else:
                    return {
                        "action": action,
                        "result": f"No web search results found for: {selected_text}\n\nTry refining your search terms or check if TAVILY_API_KEY is configured.",
                        "selected_text": selected_text[:100] + "..." if len(selected_text) > 100 else selected_text,
                        "section": section,
                        "search_type": search_type
                    }
                    
            except ImportError as e:
                raise HTTPException(status_code=500, detail=f"Web search tool not available: {str(e)}")
            except ValueError as e:
                raise HTTPException(status_code=500, detail=f"Web search configuration error: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")

        elif action == "fix_issue":
            # AI-powered contextual fix for placeholders and issues
            # Analyzes surrounding context to generate intelligent replacements
            
            placeholder = selected_text  # The text to be replaced (e.g., "TBD")
            
            # Build context-aware prompt for intelligent fix generation
            user_prompt = f"""You are analyzing a DoD procurement document. A placeholder or issue needs to be fixed with an appropriate value.

PLACEHOLDER TEXT TO REPLACE: "{placeholder}"

SECTION: {section if section else "Unknown section"}

SURROUNDING CONTEXT:
{context if context else "No additional context provided"}

YOUR TASK:
1. Analyze the surrounding context to understand what type of value is expected
2. Consider these possibilities:
   - If near currency values (e.g., $1,200,000), suggest a currency amount
   - If near dates, suggest an appropriate date
   - If near time periods (e.g., "Option Period 1"), suggest a duration or value
   - If in a table with similar values, match the format of other entries
   - If describing requirements, suggest specific requirement text

3. Generate an appropriate replacement value that:
   - Matches the expected data type (currency, date, text, etc.)
   - Fits naturally in the surrounding context
   - Uses professional DoD procurement language if text
   - Uses realistic placeholder values (not obviously fake)

IMPORTANT: Return ONLY the replacement value. No explanation, no quotes around the value, just the value itself.

Examples of good responses:
- For currency: $1,500,000
- For dates: March 30, 2025
- For durations: 12 months
- For text: "comprehensive IT infrastructure support services"
"""

        elif action == "fix_hallucination":
            # AI-powered fix for potentially hallucinated or unsourced claims
            # Provides options to: add citation, rewrite claim, or flag for verification
            
            suspicious_text = selected_text  # The text flagged as potential hallucination
            
            # Build prompt for hallucination fix - offers 3 resolution strategies
            user_prompt = f"""You are reviewing a potentially unsourced or hallucinated claim in a DoD procurement document.

SUSPICIOUS TEXT: "{suspicious_text}"

SECTION: {section if section else "Unknown section"}

SURROUNDING CONTEXT:
{context if context else "No additional context provided"}

The text above was flagged because it may contain:
- Vague references like "research shows" or "studies indicate" without citations
- Specific claims that weren't in the original source documents
- Unverifiable statistics or facts

YOUR TASK:
Provide a fixed version that EITHER:

1. ADDS A CITATION if you can identify a likely source:
   - FAR (Federal Acquisition Regulation) reference
   - DFARS (Defense Federal Acquisition Regulation Supplement) reference
   - Standard DoD policy reference
   Example: "Per FAR 15.304, evaluation factors..."

2. REWRITES to remove the unverifiable claim while preserving the intent:
   - Remove vague phrases like "research shows"
   - Make the statement factual or procedural
   Example: "The contractor shall..." instead of "Studies show contractors should..."

3. FLAGS for manual verification if the claim should be kept but needs sourcing:
   - Add [VERIFY: source needed] marker
   Example: "[VERIFY: source needed] According to industry reports, the average..."

IMPORTANT RULES:
- Return ONLY the replacement text
- Do NOT include explanations
- Choose the BEST option based on the context
- Prefer option 1 (citation) if a legitimate source exists
- Use option 2 (rewrite) if the claim is unnecessary fluff
- Use option 3 (flag) only if the information is important but truly needs verification

REPLACEMENT TEXT:"""

        elif action == "fix_compliance":
            # AI-powered fix for compliance issues - adds proper FAR/DFARS citations
            # Used when document is missing required regulatory references
            
            text_to_fix = selected_text  # The text that needs a compliance citation
            
            # Build prompt for compliance fix - focuses on adding proper citations
            user_prompt = f"""You are a DoD acquisition compliance expert. A section of a procurement document needs proper FAR/DFARS citations.

TEXT NEEDING CITATION: "{text_to_fix}"

SECTION: {section if section else "Unknown section"}

SURROUNDING CONTEXT:
{context if context else "No additional context provided"}

The text above was flagged for missing regulatory compliance references.

YOUR TASK:
Rewrite the text to include the appropriate FAR or DFARS citation. Common citations include:

- FAR Part 1: Federal Acquisition Regulations System
- FAR Part 2: Definitions
- FAR Part 4: Administrative Matters
- FAR Part 5: Publicizing Contract Actions
- FAR Part 6: Competition Requirements
- FAR Part 8: Required Sources of Supplies and Services
- FAR Part 9: Contractor Qualifications
- FAR Part 10: Market Research
- FAR Part 11: Describing Agency Needs
- FAR Part 12: Acquisition of Commercial Products/Services
- FAR Part 13: Simplified Acquisition Procedures
- FAR Part 14: Sealed Bidding
- FAR Part 15: Contracting by Negotiation (15.3 for source selection)
- FAR Part 16: Types of Contracts
- FAR Part 19: Small Business Programs
- FAR Part 22: Application of Labor Laws
- FAR Part 25: Foreign Acquisition
- FAR Part 31: Contract Cost Principles
- FAR Part 32: Contract Financing
- FAR Part 52: Solicitation Provisions and Contract Clauses
- DFARS 252: DoD-specific clauses (252.204-7012 for CUI, etc.)

RULES:
- Return ONLY the rewritten text with the citation included
- Integrate the citation naturally into the sentence
- Use format like "In accordance with FAR X.XXX, ..." or "Per FAR X.XXX, ..."
- Choose the most appropriate FAR/DFARS citation for the context
- Do NOT include explanations, just the fixed text

REWRITTEN TEXT WITH CITATION:"""

        else:
            available = config.get_available_actions() + ["web_search", "fix_issue", "fix_hallucination", "fix_compliance"]
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}. Valid actions: {', '.join(available)}")

        # Call Claude for assistance (model and settings from config)
        response = client.messages.create(
            model=config.get_model(),
            max_tokens=config.get_max_tokens(),
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )
        
        result_text = response.content[0].text.strip()
        
        return {
            "action": action,
            "result": result_text,
            "selected_text": selected_text[:100] + "..." if len(selected_text) > 100 else selected_text,
            "section": section,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in copilot assist: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Copilot assistance failed: {str(e)}")


# ============================================================================
# Quality Analysis Endpoints
# ============================================================================

class QualityAnalyzeRequest(BaseModel):
    """
    Request model for quality analysis
    
    Attributes:
        content: The document content to analyze
        section_name: Name of the section being analyzed (for context)
        project_info: Optional project information for cross-validation
    """
    content: str
    section_name: str = "Document"
    project_info: Dict = {}


@app.post("/api/quality/analyze", tags=["Quality"])
async def analyze_quality(
    request: QualityAnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run comprehensive quality analysis on document content using QualityAgent
    
    Returns all 5 quality categories:
    - Hallucination: Checks for fabricated facts and unsupported claims
    - Vague Language: Detects imprecise terms like "several", "many", "possibly"
    - Citations: Validates DoD-compliant citations (FAR/DFARS)
    - Compliance: Checks for legal/regulatory issues
    - Completeness: Evaluates word count and structure
    
    Each category includes:
    - Score (0-100)
    - Specific issues found
    - Improvement suggestions
    """
    try:
        # Get API key from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY not configured"
            )
        
        # Initialize QualityAgent
        quality_agent = QualityAgent(api_key=api_key)
        
        # Build task for QualityAgent
        task = {
            'content': request.content,
            'section_name': request.section_name,
            'project_info': request.project_info,
            'research_findings': {},
            'evaluation_type': 'full'
        }
        
        # Execute quality evaluation
        result = quality_agent.execute(task)
        
        # Format response with breakdown of all 5 categories
        response = {
            "score": result.get('score', 0),
            "grade": result.get('grade', 'Unknown'),
            "breakdown": {
                "hallucination": {
                    "score": result['detailed_checks']['hallucination']['score'],
                    "risk_level": result['detailed_checks']['hallucination']['risk_level'],
                    "issues": result['detailed_checks']['hallucination'].get('issues', []),
                    "suggestions": result['detailed_checks']['hallucination'].get('suggestions', []),
                    # Include examples (suspicious text snippets) for frontend issue cards
                    "examples": result['detailed_checks']['hallucination'].get('examples', [])
                },
                "vague_language": {
                    "score": result['detailed_checks']['vague_language']['score'],
                    "count": result['detailed_checks']['vague_language']['count'],
                    "issues": result['detailed_checks']['vague_language'].get('issues', []),
                    "suggestions": result['detailed_checks']['vague_language'].get('suggestions', [])
                },
                "citations": {
                    "score": result['detailed_checks']['citations']['score'],
                    "valid": result['detailed_checks']['citations'].get('citations_found', 0),
                    "invalid": result['detailed_checks']['citations'].get('invalid_citations', 0),
                    "issues": result['detailed_checks']['citations'].get('issues', []),
                    "suggestions": result['detailed_checks']['citations'].get('suggestions', [])
                },
                "compliance": {
                    "score": result['detailed_checks']['compliance']['score'],
                    "level": result['detailed_checks']['compliance']['level'],
                    "issues": result['detailed_checks']['compliance'].get('issues', []),
                    "suggestions": result['detailed_checks']['compliance'].get('suggestions', [])
                },
                "completeness": {
                    "score": result['detailed_checks']['completeness']['score'],
                    "word_count": result['detailed_checks']['completeness']['word_count'],
                    "paragraph_count": result['detailed_checks']['completeness']['paragraph_count'],
                    "issues": result['detailed_checks']['completeness'].get('issues', []),
                    "suggestions": result['detailed_checks']['completeness'].get('suggestions', [])
                }
            },
            "issues": result.get('issues', []),
            "suggestions": result.get('suggestions', []),
            "weights": {
                "hallucination": 0.30,
                "vague_language": 0.15,
                "citations": 0.20,
                "compliance": 0.25,
                "completeness": 0.10
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in quality analysis: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DoD Procurement API"}


@app.get("/", tags=["Root"])
def root():
    """Root endpoint"""
    return {
        "message": "DoD Procurement Document Generation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", 8000))
    RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="info"
    )
