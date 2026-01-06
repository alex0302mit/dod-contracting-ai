"""
Run RFP Pipeline: Generate Request for Proposal documents
Uses RFP Writer Agent with RAG system referencing RFP guide
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.rfp_orchestrator import RFPOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """
    Execute RFP generation pipeline
    """
    
    print("\n" + "="*70)
    print("REQUEST FOR PROPOSAL GENERATION PIPELINE")
    print("="*70)
    print()
    
    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    # Configuration
    vector_db_path = "data/vector_db/faiss_index"
    
    # Check vector store
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("⚠️  No vector store found!")
        print("\nPlease ensure RFP guide is indexed in the RAG system")
        print("Run: python scripts/setup_rag_system.py")
        return 1
    
    # Project information - CUSTOMIZE THIS
    project_info = {
        "solicitation_number": "W56KGU-25-R-0042",
        "program_name": "Advanced Logistics Management System (ALMS)",
        "contracting_officer": "John Smith",
        "issuing_office": "DOD/ARMY/LOGISTICS CONTRACTING OFFICE",
        "issue_date": "May 1, 2025",
        "closing_date": "June 15, 2025",
        "contract_type": "Firm-Fixed-Price",
        "naics_code": "541512",
        "small_business_set_aside": "Total Small Business Set-Aside",
        "place_of_performance": "Fort Lee, VA and CONUS-wide",
        "period_of_performance": "Base period: 12 months + Two 12-month option periods",
        "estimated_value": "$2.5 million (base + options)",
        "budget": "$2,500,000",
        "mission": "Modernize inventory tracking and logistics management",
        "security_clearance": "None required (unclassified)",
        "description": "Development and deployment of cloud-based logistics management platform"
    }
    
    # RFP Sections Configuration - BASED ON FAR PART 15
    # Standard Uniform Contract Format (FAR 15.204-1)
    rfp_sections_config = [
        # PART I - THE SCHEDULE
        {
            "name": "Section A - Solicitation/Contract Form",
            "guidance": """Standard Form 33 (SF-33) information.
Include: Solicitation number, type, closing date, issuing office, contract type, and requisition/purchase request number.
This is the formal cover sheet of the RFP.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section B - Supplies or Services and Prices/Costs",
            "guidance": """Detailed description of what is being acquired.
Include: Line items (CLINs), descriptions, quantities, unit prices (or basis for pricing), and total estimated value.
For ALMS: Software development, deployment, training, support services.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section C - Description/Specifications/Statement of Work",
            "guidance": """Technical requirements and work statement.
This section should include or reference the Statement of Work (SOW) or Statement of Objectives (SOO).
Define technical specifications, performance requirements, and scope of work.
For ALMS: System capabilities, performance standards, integration requirements, security requirements.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section D - Packaging and Marking",
            "guidance": """Packaging, packing, preservation, and marking requirements.
For IT services/software: Typically minimal - delivery of software via electronic means, documentation format, media types.
May include requirements for data packages, technical documentation, and source code delivery.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section E - Inspection and Acceptance",
            "guidance": """Define how the Government will inspect and accept deliverables.
Include: Inspection location, acceptance criteria, testing requirements, and acceptance procedures.
For ALMS: System testing, user acceptance testing (UAT), performance benchmarks, security testing.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section F - Deliverables or Performance",
            "guidance": """List of deliverables, delivery schedule, and performance locations.
Include: Deliverable items, due dates, delivery locations, and format requirements.
For ALMS: Software releases, documentation, training materials, progress reports, test reports.""",
            "section_type": "solicitation"
        },
        {
            "name": "Section G - Contract Administration Data",
            "guidance": """Administrative requirements and points of contact.
Include: Accounting and appropriation data, contracting officer information, payment office, contract administration office.
Specify invoicing procedures, payment terms, and reporting requirements.""",
            "section_type": "contract"
        },
        {
            "name": "Section H - Special Contract Requirements",
            "guidance": """Special clauses and requirements specific to this acquisition.
May include: Security requirements (NIST 800-171), Section 508 accessibility, cloud services requirements, proprietary data handling, intellectual property, and any unique terms.
For ALMS: Cybersecurity compliance, data rights, source code escrow, transition-out requirements.""",
            "section_type": "contract"
        },
        
        # PART II - CONTRACT CLAUSES
        {
            "name": "Section I - Contract Clauses",
            "guidance": """Required and applicable FAR and DFARS clauses.
Include clauses by reference (title, date, and FAR/DFARS number) or full text if required.
Categories: General provisions, representations and certifications, terms and conditions.
Must include small business clauses if set-aside.""",
            "section_type": "contract"
        },
        
        # PART III - LIST OF ATTACHMENTS
        {
            "name": "Section J - List of Attachments",
            "guidance": """List all documents, exhibits, and attachments referenced in the RFP.
Examples:
- Attachment 1: Statement of Work (SOW)
- Attachment 2: Price Schedule Template
- Attachment 3: Past Performance Questionnaire
- Attachment 4: System Architecture Diagram
- Attachment 5: Sample Contract (if applicable)""",
            "section_type": "solicitation"
        },
        
        # PART IV - REPRESENTATIONS AND INSTRUCTIONS
        {
            "name": "Section K - Representations, Certifications, and Other Statements",
            "guidance": """Offeror representations and certifications required before award.
Typically includes reference to FAR 52.212-3 (commercial) or SAM.gov annual representations.
May include specific certifications for small business status, cybersecurity, conflict of interest, organizational conflicts of interest (OCI).""",
            "section_type": "instructions"
        },
        {
            "name": "Section L - Instructions, Conditions, and Notices to Offerors",
            "guidance": """Detailed proposal preparation instructions.
Include:
- Proposal format and organization
- Page limits for each volume/section
- Number of copies required
- Submission method (electronic via SAM.gov or physical delivery)
- Proposal due date and time
- Questions and answers process
- Pre-proposal conference details (if applicable)
- Proposal validity period (usually 60-90 days)

For ALMS RFP:
Volume 1 - Technical Proposal (page limit: 50 pages)
Volume 2 - Past Performance (5 references)
Volume 3 - Price Proposal (separate, sealed)""",
            "section_type": "instructions"
        },
        {
            "name": "Section M - Evaluation Factors for Award",
            "guidance": """Evaluation criteria and source selection process.
Define in order of importance:
1. Evaluation factors (Technical, Past Performance, Price)
2. Subfactors under each factor
3. Relative importance or weights
4. Rating scales or adjectival ratings
5. Trade-off process (best value vs. LPTA)
6. Evaluation methodology

Example for ALMS:
Factor 1: Technical Approach (Most Important)
  - Subfactor 1a: System Architecture and Design
  - Subfactor 1b: Development Methodology and Schedule
  - Subfactor 1c: Cybersecurity Approach
Factor 2: Past Performance (Less Important than Technical)
Factor 3: Price (Less Important than Past Performance)
Award will be made on best value trade-off basis.""",
            "section_type": "evaluation"
        }
    ]
    
    try:
        # Initialize RAG
        print("Initializing RAG system...")
        vector_store = VectorStore(api_key, index_path=vector_db_path)
        
        if not vector_store.load():
            print("❌ Failed to load vector store")
            return 1
        
        retriever = Retriever(vector_store, top_k=5)
        print("✓ RAG system loaded\n")
        
        # Initialize orchestrator
        orchestrator = RFPOrchestrator(
            api_key=api_key,
            retriever=retriever,
            model="claude-sonnet-4-20250514"
        )
        
        # Execute workflow
        result = orchestrator.execute_rfp_workflow(
            project_info=project_info,
            rfp_sections_config=rfp_sections_config,
            output_path="outputs/rfp/request_for_proposal.md"
        )
        
        if result['status'] == 'success':
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nYour Request for Proposal is ready:")
            print(f"  {result['output_path']}")
            print(f"\nTime elapsed: {result['elapsed_time']:.1f}s")
            print()
            print("Next steps:")
            print("  1. Review the RFP for accuracy and completeness")
            print("  2. Have legal counsel review contract terms")
            print("  3. Coordinate with contracting officer")
            print("  4. Post synopsis on SAM.gov (15 days before RFP release)")
            print("  5. Release RFP on SAM.gov")
            print()
            return 0
        else:
            print("\n❌ RFP generation failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
