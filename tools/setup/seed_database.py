"""
Database seeding script - Create sample users and projects
Run this after initializing the database to populate with test data
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.base import SessionLocal, init_db
from backend.models.user import User, UserRole
from backend.models.procurement import (
    ProcurementProject, ProcurementPhase, ProcurementStep,
    ProjectType, ProjectStatus, PhaseName, PhaseStatus, StepStatus
)
from backend.models.document import (
    DocumentChecklistTemplate, ProjectDocument,
    DocumentStatus
)
from backend.middleware.auth import get_password_hash


def seed_users(db):
    """Create sample users"""
    print("📝 Seeding users...")

    users = [
        User(
            email="john.contracting@navy.mil",
            name="John Smith",
            hashed_password=get_password_hash("SecureTest123!"),
            role=UserRole.CONTRACTING_OFFICER,
            department="Navy Acquisition"
        ),
        User(
            email="sarah.pm@navy.mil",
            name="Sarah Johnson",
            hashed_password=get_password_hash("SecureTest123!"),
            role=UserRole.PROGRAM_MANAGER,
            department="Navy Programs"
        ),
        User(
            email="mike.approver@navy.mil",
            name="Mike Wilson",
            hashed_password=get_password_hash("SecureTest123!"),
            role=UserRole.APPROVER,
            department="Navy Legal"
        ),
        User(
            email="viewer@navy.mil",
            name="Demo Viewer",
            hashed_password=get_password_hash("SecureTest123!"),
            role=UserRole.VIEWER,
            department="Navy Oversight"
        ),
    ]

    for user in users:
        db.add(user)

    db.commit()
    print(f"✅ Created {len(users)} users")
    return users


def seed_document_templates(db):
    """Create RFP document templates"""
    print("📄 Seeding document templates...")

    templates = [
        # Pre-Solicitation Phase - Required documents for phase gate transition
        # These document names MUST match phase_definitions.yaml required_documents
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Market Research Report",  # Required for phase gate
            description="Comprehensive market research documenting available sources, pricing benchmarks, and market conditions per FAR Part 10",
            category="Market Research",
            phase=PhaseName.PRE_SOLICITATION,
            is_required=True,
            typical_deadline_days=20,
            requires_approval=True,
            display_order=1
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Acquisition Plan",  # Required for phase gate
            description="Comprehensive acquisition planning document per FAR Part 7, outlining approach, timeline, milestones, and resources",
            category="Strategic",
            phase=PhaseName.PRE_SOLICITATION,
            is_required=True,
            typical_deadline_days=30,
            requires_approval=True,
            display_order=2
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Acquisition Strategy",  # Additional strategic document
            description="High-level acquisition strategy document outlining overall approach and key decisions",
            category="Strategic",
            phase=PhaseName.PRE_SOLICITATION,
            is_required=False,  # Not required for phase gate
            typical_deadline_days=25,
            requires_approval=True,
            display_order=3
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Performance Work Statement (PWS)",  # Required for phase gate
            description="Performance-based work requirements and objectives per FAR Part 11",
            category="Technical",
            phase=PhaseName.PRE_SOLICITATION,
            is_required=True,
            typical_deadline_days=45,
            requires_approval=True,
            display_order=4
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Independent Government Cost Estimate (IGCE)",  # Required for phase gate
            description="Detailed cost estimate prepared by government team for budget validation",
            category="Financial",
            phase=PhaseName.PRE_SOLICITATION,
            is_required=True,
            typical_deadline_days=45,
            requires_approval=True,
            display_order=5
        ),
        # Solicitation Phase
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Source Selection Plan",
            description="Detailed plan for evaluating and selecting proposals",
            category="Administrative",
            phase=PhaseName.SOLICITATION,
            is_required=True,
            typical_deadline_days=15,
            requires_approval=True,
            display_order=10
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Section L - Instructions to Offerors",
            description="Detailed instructions for proposal preparation and submission",
            category="Administrative",
            phase=PhaseName.SOLICITATION,
            is_required=True,
            typical_deadline_days=30,
            requires_approval=True,
            display_order=11
        ),
        # Post-Solicitation Phase - Documents for evaluation and award
        # These are initialized when transitioning from solicitation to post_solicitation
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Technical Evaluation Report",
            description="Comprehensive evaluation of technical proposals per FAR 15.305, documenting strengths, weaknesses, and ratings",
            category="Evaluation",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=45,
            requires_approval=True,
            display_order=20
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Past Performance Evaluation",
            description="Assessment of offerors' past performance on similar contracts per FAR 15.305(a)(2)",
            category="Evaluation",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=30,
            requires_approval=True,
            display_order=21
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Cost/Price Analysis",
            description="Detailed analysis of proposed costs and pricing per FAR 15.404, ensuring fair and reasonable pricing",
            category="Financial",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=30,
            requires_approval=True,
            display_order=22
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Competitive Range Determination",
            description="Documentation of competitive range decision identifying offerors for discussions per FAR 15.306",
            category="Administrative",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=15,
            requires_approval=True,
            display_order=23
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Source Selection Decision Document (SSDD)",
            description="Final source selection decision and rationale documenting the award determination per FAR 15.308",
            category="Administrative",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=30,
            requires_approval=True,
            display_order=24
        ),
        DocumentChecklistTemplate(
            contract_type=ProjectType.RFP,
            document_name="Contract Award Documentation",
            description="Complete contract award package including SF-26, award notification, and supporting documents",
            category="Legal",
            phase=PhaseName.POST_SOLICITATION,
            is_required=True,
            typical_deadline_days=15,
            requires_approval=True,
            display_order=25
        ),
    ]

    for template in templates:
        db.add(template)

    db.commit()
    print(f"✅ Created {len(templates)} document templates")


def seed_sample_project(db, users):
    """Create a sample procurement project"""
    print("🚀 Seeding sample project...")

    contracting_officer = users[0]  # John Smith
    program_manager = users[1]  # Sarah Johnson

    # Create project
    project = ProcurementProject(
        name="Advanced Navy Training System (ANTS)",
        description="Procurement for next-generation pilot training simulation system with AI-enhanced capabilities",
        project_type=ProjectType.RFP,
        estimated_value=25000000.00,  # $25M
        contracting_officer_id=contracting_officer.id,
        program_manager_id=program_manager.id,
        current_phase=PhaseName.PRE_SOLICITATION,
        overall_status=ProjectStatus.IN_PROGRESS,
        start_date=date.today() - timedelta(days=30),
        target_completion_date=date.today() + timedelta(days=180),
        created_by=contracting_officer.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create phases
    phases = [
        ProcurementPhase(
            project_id=project.id,
            phase_name=PhaseName.PRE_SOLICITATION,
            phase_order=1,
            status=PhaseStatus.IN_PROGRESS,
            start_date=date.today() - timedelta(days=30),
            estimated_duration_days=60
        ),
        ProcurementPhase(
            project_id=project.id,
            phase_name=PhaseName.SOLICITATION,
            phase_order=2,
            status=PhaseStatus.NOT_STARTED,
            estimated_duration_days=90
        ),
        ProcurementPhase(
            project_id=project.id,
            phase_name=PhaseName.POST_SOLICITATION,
            phase_order=3,
            status=PhaseStatus.NOT_STARTED,
            estimated_duration_days=45
        ),
    ]
    db.add_all(phases)
    db.commit()

    # Create some steps for the active phase
    pre_sol_phase = phases[0]
    steps = [
        ProcurementStep(
            phase_id=pre_sol_phase.id,
            project_id=project.id,
            step_name="Market Research",
            step_description="Conduct comprehensive market research to identify potential vendors",
            step_order=1,
            status=StepStatus.COMPLETED,
            assigned_user_id=program_manager.id,
            deadline=date.today() - timedelta(days=10),
            completion_date=date.today() - timedelta(days=12)
        ),
        ProcurementStep(
            phase_id=pre_sol_phase.id,
            project_id=project.id,
            step_name="Draft PWS",
            step_description="Develop Performance Work Statement using AI assistance",
            step_order=2,
            status=StepStatus.IN_PROGRESS,
            assigned_user_id=contracting_officer.id,
            deadline=date.today() + timedelta(days=7)
        ),
        ProcurementStep(
            phase_id=pre_sol_phase.id,
            project_id=project.id,
            step_name="Prepare IGCE",
            step_description="Prepare Independent Government Cost Estimate",
            step_order=3,
            status=StepStatus.NOT_STARTED,
            assigned_user_id=program_manager.id,
            deadline=date.today() + timedelta(days=14)
        ),
    ]
    db.add_all(steps)
    db.commit()

    # Create project documents from templates
    templates = db.query(DocumentChecklistTemplate).filter(
        DocumentChecklistTemplate.contract_type == ProjectType.RFP
    ).all()

    documents = []
    for template in templates:
        doc = ProjectDocument(
            project_id=project.id,
            document_name=template.document_name,
            description=template.description,
            category=template.category,
            phase=template.phase,
            is_required=template.is_required,
            status=DocumentStatus.PENDING,
            requires_approval=template.requires_approval,
            display_order=template.display_order,
            deadline=date.today() + timedelta(days=template.typical_deadline_days) if template.typical_deadline_days else None
        )
        documents.append(doc)

    db.add_all(documents)
    db.commit()

    print(f"✅ Created sample project: {project.name}")
    print(f"   - {len(phases)} phases")
    print(f"   - {len(steps)} steps")
    print(f"   - {len(documents)} documents")


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 60)

    # Initialize database
    init_db()

    # Create session
    db = SessionLocal()

    try:
        # Seed data
        users = seed_users(db)
        seed_document_templates(db)
        seed_sample_project(db, users)

        print("=" * 60)
        print("✅ Database seeding completed successfully!")
        print()
        print("📧 Test User Credentials:")
        print("   Contracting Officer: john.contracting@navy.mil / SecureTest123!")
        print("   Program Manager: sarah.pm@navy.mil / SecureTest123!")
        print("   Approver: mike.approver@navy.mil / SecureTest123!")
        print("   Viewer: viewer@navy.mil / SecureTest123!")
        print()
        print("🚀 You can now start the API server:")
        print("   cd backend && python main.py")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
