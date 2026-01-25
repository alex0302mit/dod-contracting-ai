"""
Migration script to add recommended and optional documents to Solicitation and Post-Solicitation phases.

This script adds 18 new document templates across two phases:

Solicitation Phase (9 new documents):
Required:
- SF33 - Solicitation, Offer and Award
- Section B - Supplies/Services and Prices
- Section H - Special Contract Requirements
- Section I - Contract Clauses
- Section K - Representations and Certifications
- Section M - Evaluation Factors
Optional:
- Draft RFP for Industry Review
- Q&A Document
- Site Visit Materials

Post-Solicitation Phase (9 new documents):
Required:
- Evaluation Scorecard
- SF26 - Award/Contract
- Award Notification
Recommended:
- Past Performance Questionnaire (PPQ)
- Debriefing Letter
Optional:
- Discussion Question Set
- Clarification Requests
- Public Award Announcement
- Post-Award Orientation Materials

This script also:
- Updates display_order for existing Post-Solicitation templates (20→30, 21→31, etc.)
- Adds the new documents to existing RFP projects
- Updates display_order for existing project documents

Run with: python tools/migrations/migrate_all_phase_documents.py
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.base import SessionLocal, init_db
from backend.models.procurement import ProjectType, PhaseName, ProcurementProject
from backend.models.document import DocumentChecklistTemplate, ProjectDocument, DocumentStatus


# New Solicitation Phase templates (display_order 17-25)
NEW_SOLICITATION_TEMPLATES = [
    # Required - Forms
    {
        "contract_type": ProjectType.RFP,
        "document_name": "SF33 - Solicitation, Offer and Award",
        "description": "Standard Form 33 cover page for formal solicitations per FAR 53.214",
        "category": "Forms",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 20,
        "requires_approval": True,
        "display_order": 17
    },
    # Required - RFP Sections
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Section B - Supplies/Services and Prices",
        "description": "Description of supplies/services with pricing structure per FAR 15.204-2",
        "category": "RFP Sections",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 25,
        "requires_approval": True,
        "display_order": 18
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Section H - Special Contract Requirements",
        "description": "Special contract requirements specific to the procurement per FAR 15.204-8",
        "category": "RFP Sections",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 25,
        "requires_approval": True,
        "display_order": 19
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Section I - Contract Clauses",
        "description": "Contract clauses incorporated by reference and full text per FAR 15.204-9",
        "category": "RFP Sections",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 20,
        "requires_approval": True,
        "display_order": 20
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Section K - Representations and Certifications",
        "description": "Offeror representations and certifications per FAR 15.204-11",
        "category": "RFP Sections",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 15,
        "requires_approval": True,
        "display_order": 21
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Section M - Evaluation Factors",
        "description": "Evaluation factors and significant subfactors for award per FAR 15.204-13",
        "category": "RFP Sections",
        "phase": PhaseName.SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 25,
        "requires_approval": True,
        "display_order": 22
    },
    # Optional
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Draft RFP for Industry Review",
        "description": "Draft solicitation released to industry for feedback before final issuance",
        "category": "Administrative",
        "phase": PhaseName.SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 30,
        "requires_approval": False,
        "display_order": 23
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Q&A Document",
        "description": "Compilation of questions and answers from industry during solicitation period",
        "category": "Administrative",
        "phase": PhaseName.SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 35,
        "requires_approval": False,
        "display_order": 24
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Site Visit Materials",
        "description": "Materials for site visit including agenda, safety requirements, and logistics",
        "category": "Administrative",
        "phase": PhaseName.SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 20,
        "requires_approval": False,
        "display_order": 25
    },
]

# New Post-Solicitation Phase templates (display_order 36-44)
NEW_POST_SOLICITATION_TEMPLATES = [
    # Required - Evaluation
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Evaluation Scorecard",
        "description": "Standardized scorecard for evaluating proposals against stated criteria",
        "category": "Evaluation",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 20,
        "requires_approval": True,
        "display_order": 36
    },
    # Recommended - Evaluation
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Past Performance Questionnaire (PPQ)",
        "description": "Questionnaire sent to offeror references to assess past performance",
        "category": "Evaluation",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 25,
        "requires_approval": False,
        "display_order": 37
    },
    # Optional - Evaluation
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Discussion Question Set",
        "description": "Prepared questions for discussions/negotiations with offerors in competitive range",
        "category": "Evaluation",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 15,
        "requires_approval": False,
        "display_order": 38
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Clarification Requests",
        "description": "Formal requests for clarification sent to offerors per FAR 15.306(a)",
        "category": "Administrative",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 10,
        "requires_approval": False,
        "display_order": 39
    },
    # Required - Award
    {
        "contract_type": ProjectType.RFP,
        "document_name": "SF26 - Award/Contract",
        "description": "Standard Form 26 for contract award per FAR 53.214",
        "category": "Forms",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 10,
        "requires_approval": True,
        "display_order": 40
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Award Notification",
        "description": "Official notification to successful offeror of contract award per FAR 15.503",
        "category": "Award",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 5,
        "requires_approval": True,
        "display_order": 41
    },
    # Recommended - Award
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Debriefing Letter",
        "description": "Written debriefing to unsuccessful offerors per FAR 15.506",
        "category": "Award",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 10,
        "requires_approval": True,
        "display_order": 42
    },
    # Optional - Award
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Public Award Announcement",
        "description": "Press release or public announcement of contract award",
        "category": "Award",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 15,
        "requires_approval": False,
        "display_order": 43
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Post-Award Orientation Materials",
        "description": "Materials for post-award kickoff meeting including transition plan and key contacts",
        "category": "Award",
        "phase": PhaseName.POST_SOLICITATION,
        "is_required": False,
        "typical_deadline_days": 20,
        "requires_approval": False,
        "display_order": 44
    },
]

# Existing Post-Solicitation documents to update display_order (20→30, 21→31, etc.)
POST_SOLICITATION_DISPLAY_ORDER_UPDATES = {
    "Technical Evaluation Report": 30,
    "Past Performance Evaluation": 31,
    "Cost/Price Analysis": 32,
    "Competitive Range Determination": 33,
    "Source Selection Decision Document (SSDD)": 34,
    "Contract Award Documentation": 35,
}


def run_migration():
    """Add solicitation and post-solicitation templates and update display_order."""
    print("\n" + "="*70)
    print("All Phase Documents Migration")
    print("Adding Solicitation and Post-Solicitation recommended/optional documents")
    print("="*70)

    db = SessionLocal()

    try:
        templates_added = 0
        templates_skipped = 0
        templates_updated = 0

        # Phase 1: Update existing Post-Solicitation document display_order
        print("\n[Phase 1] Updating existing Post-Solicitation template display_order...")
        for doc_name, new_order in POST_SOLICITATION_DISPLAY_ORDER_UPDATES.items():
            existing = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == ProjectType.RFP,
                DocumentChecklistTemplate.document_name == doc_name
            ).first()

            if existing and existing.display_order != new_order:
                old_order = existing.display_order
                existing.display_order = new_order
                print(f"  [UPDATE] '{doc_name}': display_order {old_order} -> {new_order}")
                templates_updated += 1
            elif existing:
                print(f"  [SKIP] '{doc_name}' already has display_order {new_order}")
            else:
                print(f"  [WARN] '{doc_name}' not found in database")

        db.commit()

        # Phase 2: Add new Solicitation templates
        print("\n[Phase 2] Adding new Solicitation templates...")
        for template_data in NEW_SOLICITATION_TEMPLATES:
            existing = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == template_data["contract_type"],
                DocumentChecklistTemplate.document_name == template_data["document_name"]
            ).first()

            if existing:
                print(f"  [SKIP] '{template_data['document_name']}' already exists")
                templates_skipped += 1
            else:
                template = DocumentChecklistTemplate(**template_data)
                db.add(template)
                print(f"  [ADD]  '{template_data['document_name']}'")
                templates_added += 1

        # Phase 3: Add new Post-Solicitation templates
        print("\n[Phase 3] Adding new Post-Solicitation templates...")
        for template_data in NEW_POST_SOLICITATION_TEMPLATES:
            existing = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == template_data["contract_type"],
                DocumentChecklistTemplate.document_name == template_data["document_name"]
            ).first()

            if existing:
                print(f"  [SKIP] '{template_data['document_name']}' already exists")
                templates_skipped += 1
            else:
                template = DocumentChecklistTemplate(**template_data)
                db.add(template)
                print(f"  [ADD]  '{template_data['document_name']}'")
                templates_added += 1

        db.commit()

        # Phase 4: Update existing project documents display_order
        print("\n[Phase 4] Updating display_order for Post-Solicitation docs in existing projects...")
        for doc_name, new_order in POST_SOLICITATION_DISPLAY_ORDER_UPDATES.items():
            updated = db.query(ProjectDocument).filter(
                ProjectDocument.document_name == doc_name,
                ProjectDocument.display_order != new_order
            ).update({ProjectDocument.display_order: new_order})
            if updated:
                print(f"  [UPDATE] '{doc_name}': {updated} project documents updated to display_order {new_order}")

        db.commit()

        # Phase 5: Add new documents to existing RFP projects
        print("\n[Phase 5] Adding new documents to existing RFP projects...")
        projects = db.query(ProcurementProject).filter(
            ProcurementProject.project_type == ProjectType.RFP
        ).all()

        project_docs_added = 0
        project_docs_skipped = 0

        all_new_templates = NEW_SOLICITATION_TEMPLATES + NEW_POST_SOLICITATION_TEMPLATES

        for project in projects:
            print(f"\n  Project: {project.name} (ID: {project.id})")

            for template_data in all_new_templates:
                existing_doc = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == project.id,
                    ProjectDocument.document_name == template_data["document_name"]
                ).first()

                if existing_doc:
                    print(f"    [SKIP] '{template_data['document_name']}' already exists")
                    project_docs_skipped += 1
                else:
                    doc = ProjectDocument(
                        project_id=project.id,
                        document_name=template_data["document_name"],
                        description=template_data["description"],
                        category=template_data["category"],
                        phase=template_data["phase"],
                        is_required=template_data["is_required"],
                        status=DocumentStatus.PENDING,
                        requires_approval=template_data["requires_approval"],
                        display_order=template_data["display_order"],
                        deadline=date.today() + timedelta(days=template_data["typical_deadline_days"]) if template_data.get("typical_deadline_days") else None
                    )
                    db.add(doc)
                    print(f"    [ADD]  '{template_data['document_name']}'")
                    project_docs_added += 1

        db.commit()

        # Summary
        print("\n" + "="*70)
        print(f"Migration complete!")
        print(f"\n  Templates:")
        print(f"    - Added: {templates_added} templates")
        print(f"    - Skipped: {templates_skipped} templates (already exist)")
        print(f"    - Updated: {templates_updated} display_order values")
        print(f"\n  Project Documents:")
        print(f"    - Added: {project_docs_added} documents across {len(projects)} projects")
        print(f"    - Skipped: {project_docs_skipped} documents (already exist)")
        print("="*70)

        # Show template counts by phase
        for phase_name in [PhaseName.PRE_SOLICITATION, PhaseName.SOLICITATION, PhaseName.POST_SOLICITATION]:
            phase_templates = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == ProjectType.RFP,
                DocumentChecklistTemplate.phase == phase_name
            ).order_by(DocumentChecklistTemplate.display_order).all()

            required_count = sum(1 for t in phase_templates if t.is_required)
            optional_count = len(phase_templates) - required_count

            print(f"\n{phase_name.value} templates ({len(phase_templates)} total):")
            print(f"  Required: {required_count}, Optional: {optional_count}")
            for t in phase_templates:
                req = "✓ Required" if t.is_required else "  Optional"
                print(f"  {req} | Order {t.display_order:2} | {t.document_name}")

    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
