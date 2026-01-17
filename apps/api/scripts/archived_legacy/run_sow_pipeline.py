"""
Run SOW Pipeline: Generate Statement of Work documents
Uses SOW Writer Agent with RAG system referencing SOW manual
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.sow_orchestrator import SOWOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """
    Execute SOW generation pipeline
    """

    print("\n" + "="*70)
    print("STATEMENT OF WORK GENERATION PIPELINE")
    print("="*70)
    print()

    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return 1

    # Configuration
    vector_db_path = "data/vector_db/faiss_index"

    # Check vector store exists
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("⚠️  No vector store found!")
        print(f"\nPlease ensure your SOW manual is indexed:")
        print("1. Add SOW manual to data/documents/")
        print("2. Run: python scripts/add_documents_to_rag.py data/documents/SOW_Manual.pdf")
        return 1

    # Project information - CUSTOMIZE THIS
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "date": "10/04/2025",
        "product_service": "Cloud-based inventory management and logistics tracking system",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
        "background": "Modernization of legacy 15-year-old inventory system",
        "primary_objectives": "Real-time tracking, 99.9% uptime, ERP integration, mobile access"
    }

    # SOW Sections Configuration - BASED ON OFFICIAL STANDARD STRUCTURE
    # Source: FAR Part 11, Standard SOW Template (23-54 pages typical)
    sow_sections_config = [
        {
            "name": "1. Scope",
            "requirements": """Provide detailed work description, tasks to be performed, geographic coverage, and period of performance.
Clearly state what is included and excluded from the scope.""",
            "context": {
                "be_specific": True,
                "include_exclusions": True
            }
        },
        {
            "name": "2. Applicable Documents",
            "requirements": """List all referenced standards, regulations, technical specifications, and incorporating documents.
Include FAR clauses, military standards (MIL-STD), industry standards (ISO, IEEE), and agency-specific regulations.""",
            "context": {
                "include_standards": True,
                "include_regulations": True
            }
        },
        {
            "name": "3. Requirements",
            "requirements": """Provide comprehensive task-by-task breakdown with specific methodologies, tools and technologies required,
personnel qualifications needed, and facilities and equipment specifications.
This is the most detailed section (10-30 pages typical).""",
            "context": {
                "task_breakdown": True,
                "include_qualifications": True,
                "include_methodologies": True
            }
        },
        {
            "name": "4. Deliverables",
            "requirements": """Specify item-by-item listing of all deliverables with delivery schedule, format requirements,
quantities, and acceptance criteria. Include documentation, software, hardware, reports, and data deliverables.""",
            "context": {
                "include_formats": True,
                "include_schedules": True,
                "include_acceptance": True
            }
        },
        {
            "name": "5. Performance Standards",
            "requirements": """Define quality metrics, timeliness requirements, and customer satisfaction goals.
Specify measurable performance indicators and acceptable quality levels (AQL).""",
            "context": {
                "include_metrics": True,
                "include_AQL": True
            }
        },
        {
            "name": "6. Government Furnished Property/Services",
            "requirements": """List equipment provided by government, facilities access, information systems access,
and support services. Include availability schedules and access procedures.""",
            "context": {
                "include_equipment": True,
                "include_access": True
            }
        },
        {
            "name": "7. Travel Requirements",
            "requirements": """Specify expected travel (if any), approval process for travel, and required documentation.
Include estimated number of trips, locations, and duration.""",
            "context": {}
        },
        {
            "name": "8. Security Requirements",
            "requirements": """Define personnel security (clearances, background checks), physical security (facility access, badging),
information security (data protection, encryption), and compliance requirements (NIST, CMMC, FedRAMP).""",
            "context": {
                "include_clearances": True,
                "include_cybersecurity": True
            }
        },
        {
            "name": "9. Meetings and Reports",
            "requirements": """Specify meeting frequency (kickoff, status, reviews), report types and frequency (monthly, quarterly, annual),
and presentation requirements. Include format and distribution requirements.""",
            "context": {
                "include_frequency": True,
                "include_formats": True
            }
        },
        {
            "name": "10. Transition",
            "requirements": """Define transition-in plan (knowledge transfer from incumbent, personnel onboarding, system access),
transition-out plan (knowledge transfer to successor, data turnover, equipment return), and continuity requirements.""",
            "context": {
                "include_transition_in": True,
                "include_transition_out": True
            }
        }
    ]

    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        vector_store = VectorStore(api_key, index_path=vector_db_path)

        if not vector_store.load():
            print("❌ Failed to load vector store")
            return 1

        retriever = Retriever(vector_store, top_k=5)  # Retrieve top 5 SOW manual chunks
        print("✓ RAG system loaded")
        print()

        # Initialize SOW orchestrator
        orchestrator = SOWOrchestrator(
            api_key=api_key,
            retriever=retriever,
            model="claude-sonnet-4-20250514"
        )

        # Execute SOW workflow
        result = orchestrator.execute_sow_workflow(
            project_info=project_info,
            sow_sections_config=sow_sections_config,
            output_path="outputs/sow/statement_of_work.md"
        )

        if result['status'] == 'success':
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nYour Statement of Work is ready: {result['output_path']}")
            print(f"\nTime elapsed: {result['elapsed_time']:.1f}s")
            print()
            return 0
        else:
            print("\n❌ SOW generation failed")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
