"""
Migration script to add missing document templates that match phase gate requirements.

The phase_definitions.yaml requires these documents for Pre-Solicitation phase:
- Market Research Report
- Acquisition Plan
- Performance Work Statement (PWS)
- Independent Government Cost Estimate (IGCE)

This script adds any missing templates to existing databases.

Run with: python -m backend.scripts.migrate_add_missing_templates
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.base import SessionLocal, init_db
from backend.models.procurement import ProjectType, PhaseName
from backend.models.document import DocumentChecklistTemplate


# Templates that must exist for phase gate validation to work correctly
# These document names MUST match what's in phase_definitions.yaml
REQUIRED_TEMPLATES = [
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Market Research Report",
        "description": "Comprehensive market research documenting available sources, pricing benchmarks, and market conditions per FAR Part 10",
        "category": "Market Research",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 20,
        "requires_approval": True,
        "display_order": 1
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Acquisition Plan",
        "description": "Comprehensive acquisition planning document per FAR Part 7, outlining approach, timeline, milestones, and resources",
        "category": "Strategic",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 30,
        "requires_approval": True,
        "display_order": 2
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Performance Work Statement (PWS)",
        "description": "Performance-based work requirements and objectives per FAR Part 11",
        "category": "Technical",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 45,
        "requires_approval": True,
        "display_order": 4
    },
    {
        "contract_type": ProjectType.RFP,
        "document_name": "Independent Government Cost Estimate (IGCE)",
        "description": "Detailed cost estimate prepared by government team for budget validation",
        "category": "Financial",
        "phase": PhaseName.PRE_SOLICITATION,
        "is_required": True,
        "typical_deadline_days": 45,
        "requires_approval": True,
        "display_order": 5
    },
]


def run_migration():
    """Add missing document templates to the database."""
    print("\n" + "="*60)
    print("Adding Missing Document Templates Migration")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        added_count = 0
        skipped_count = 0
        
        for template_data in REQUIRED_TEMPLATES:
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
        
        db.commit()
        
        print("\n" + "="*60)
        print(f"Migration complete!")
        print(f"  - Added: {added_count} templates")
        print(f"  - Skipped: {skipped_count} templates (already exist)")
        print("="*60)
        
        # Show all templates now in database
        all_templates = db.query(DocumentChecklistTemplate).filter(
            DocumentChecklistTemplate.contract_type == ProjectType.RFP
        ).order_by(DocumentChecklistTemplate.display_order).all()
        
        print(f"\nCurrent RFP templates ({len(all_templates)} total):")
        for t in all_templates:
            req = "✓ Required" if t.is_required else "  Optional"
            print(f"  {req} | {t.phase.value if t.phase else 'N/A':20} | {t.document_name}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
