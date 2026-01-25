"""
Migration script to add pre-solicitation recommended and optional document templates.

Adds these documents to the Pre-Solicitation phase:
Recommended:
- Sources Sought Notice
- Quality Assurance Surveillance Plan (QASP)

Optional:
- Pre-Solicitation Notice
- Industry Day Materials
- Request for Information (RFI)

This script also:
- Updates display_order for Solicitation phase documents to avoid conflicts
- Adds the new documents to existing RFP projects

Run with: python tools/migrations/migrate_presol_optional_templates.py
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


# New pre-solicitation templates to add
NEW_PRESOL_TEMPLATES = [
    # Recommended documents
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Sources Sought Notice",
        "description": "Capability assessment notice for industry engagement per FAR Part 10",
        "category": "Market Research",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": False,  # Recommended, not required
        "typical_deadline_days": 25,
        "requires_approval": False,
        "display_order": 6
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Quality Assurance Surveillance Plan (QASP)",
        "description": "Performance standards and monitoring methods for contract oversight",
        "category": "Technical",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": False,  # Recommended, not required
        "typical_deadline_days": 50,
        "requires_approval": True,
        "display_order": 7
    },
    # Optional documents
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Pre-Solicitation Notice",
        "description": "Early market notification to inform potential offerors",
        "category": "Market Research",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": False,  # Optional
        "typical_deadline_days": 15,
        "requires_approval": False,
        "display_order": 8
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Industry Day Materials",
        "description": "Presentation and handout materials for vendor engagement events",
        "category": "Market Research",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": False,  # Optional
        "typical_deadline_days": 20,
        "requires_approval": False,
        "display_order": 9
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Request for Information (RFI)",
        "description": "Market feedback request to gather industry input on requirements",
        "category": "Market Research",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": False,  # Optional
        "typical_deadline_days": 18,
        "requires_approval": False,
        "display_order": 10
    },
]

# Solicitation documents to update display_order
SOLICITATION_DISPLAY_ORDER_UPDATES = {
    "Source Selection Plan": 15,
    "Section L - Instructions to Offerors": 16,
}


def run_migration():
    """Add pre-solicitation optional templates and update display_order."""
    print("\n" + "="*60)
    print("Pre-Solicitation Recommended/Optional Templates Migration")
    print("="*60)

    db = SessionLocal()

    try:
        added_count = 0
        skipped_count = 0
        updated_count = 0

        # Add new pre-solicitation templates
        print("\n[Phase 1] Adding new pre-solicitation templates...")
        for template_data in NEW_PRESOL_TEMPLATES:
            # Check if template already exists
            existing = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == template_data["contract_type"],
                DocumentChecklistTemplate.document_name == template_data["document_name"]
            ).first()

            if existing:
                print(f"  [SKIP] '{template_data['document_name']}' already exists")
                skipped_count += 1
            else:
                # Create new template
                template = DocumentChecklistTemplate(**template_data)
                db.add(template)
                print(f"  [ADD]  '{template_data['document_name']}'")
                added_count += 1

        # Update display_order for solicitation documents
        print("\n[Phase 2] Updating solicitation document display_order...")
        for doc_name, new_order in SOLICITATION_DISPLAY_ORDER_UPDATES.items():
            existing = db.query(DocumentChecklistTemplate).filter(
                DocumentChecklistTemplate.contract_type == ProjectType.RFP,
                DocumentChecklistTemplate.document_name == doc_name
            ).first()

            if existing and existing.display_order != new_order:
                old_order = existing.display_order
                existing.display_order = new_order
                print(f"  [UPDATE] '{doc_name}': display_order {old_order} -> {new_order}")
                updated_count += 1
            elif existing:
                print(f"  [SKIP] '{doc_name}' already has display_order {new_order}")
            else:
                print(f"  [WARN] '{doc_name}' not found in database")

        db.commit()

        # Phase 3: Add new documents to existing RFP projects
        print("\n[Phase 3] Adding documents to existing RFP projects...")
        projects = db.query(ProcurementProject).filter(
            ProcurementProject.project_type == ProjectType.RFP
        ).all()

        project_docs_added = 0
        project_docs_skipped = 0

        for project in projects:
            print(f"\n  Project: {project.name} (ID: {project.id})")

            for template_data in NEW_PRESOL_TEMPLATES:
                # Check if this document already exists for this project
                existing_doc = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == project.id,
                    ProjectDocument.document_name == template_data["document_name"]
                ).first()

                if existing_doc:
                    print(f"    [SKIP] '{template_data['document_name']}' already exists")
                    project_docs_skipped += 1
                else:
                    # Create new project document
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

        # Also update display_order for existing solicitation documents in projects
        print("\n[Phase 4] Updating display_order for solicitation docs in existing projects...")
        for doc_name, new_order in SOLICITATION_DISPLAY_ORDER_UPDATES.items():
            updated = db.query(ProjectDocument).filter(
                ProjectDocument.document_name == doc_name,
                ProjectDocument.display_order != new_order
            ).update({ProjectDocument.display_order: new_order})
            if updated:
                print(f"  [UPDATE] '{doc_name}': {updated} project documents updated to display_order {new_order}")

        db.commit()

        print("\n" + "="*60)
        print(f"Migration complete!")
        print(f"  Templates:")
        print(f"    - Added: {added_count} templates")
        print(f"    - Skipped: {skipped_count} templates (already exist)")
        print(f"    - Updated: {updated_count} display_order values")
        print(f"  Project Documents:")
        print(f"    - Added: {project_docs_added} documents across {len(projects)} projects")
        print(f"    - Skipped: {project_docs_skipped} documents (already exist)")
        print("="*60)

        # Show all pre-solicitation templates now in database
        presol_templates = db.query(DocumentChecklistTemplate).filter(
            DocumentChecklistTemplate.contract_type == ProjectType.RFP,
            DocumentChecklistTemplate.phase == PhaseName.PRE_SOLICITATION
        ).order_by(DocumentChecklistTemplate.display_order).all()

        print(f"\nPre-Solicitation templates ({len(presol_templates)} total):")
        for t in presol_templates:
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
