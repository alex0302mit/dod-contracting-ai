"""
Run SOO Pipeline: Generate Statement of Objectives documents
Enhanced with web search for current market intelligence
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.soo_orchestrator import SOOOrchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """
    Execute enhanced SOO generation pipeline
    """

    print("\n" + "="*70)
    print("ENHANCED STATEMENT OF OBJECTIVES GENERATION PIPELINE")
    print("With Real-Time Web Search & Market Data")
    print("="*70)
    print()

    # Load environment
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    tavily_key = os.environ.get('TAVILY_API_KEY')

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1

    if not tavily_key:
        print("⚠️  Warning: TAVILY_API_KEY not set - web search disabled")
        print("   For current market data, add to .env: TAVILY_API_KEY='your-key'")
        print("   Continuing with RAG-only mode...\n")
    
    # Configuration
    vector_db_path = "data/vector_db/faiss_index"
    
    # Check vector store
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("⚠️  No vector store found!")
        print("\nPlease ensure SOO guide/examples are indexed")
        return 1
    
    # Project information - CUSTOMIZE THIS
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "date": "10/05/2025",
        "mission": "Modernize inventory tracking to improve readiness",
        "budget": "$2.5 million",
        "period_of_performance": "36 months",
        "current_challenges": "Legacy system causing delays, manual tracking, no mobile access",
        "desired_outcomes": "Real-time visibility, 99.9% uptime, ERP integration"
    }
    
    # SOO Sections Configuration - BASED ON OFFICIAL DoD TEMPLATE
    # Source: DoD Joint SOO Template (FAR 37.602, DFARS PGI 237.170-2)
    soo_sections_config = [
        {
            "name": "1. Purpose",
            "guidance": """Describe the overarching mission need and purpose of the acquisition.
Focus on the end result or outcome desired, not the method to achieve it.
Example: The purpose is to enhance operational readiness by implementing an integrated logistics and data analytics platform.""",
            "focus": "outcomes"
        },
        {
            "name": "2. Scope",
            "guidance": """Define the boundaries of the effort, functional areas, and systems involved.
Include all activities expected under the contract without being overly prescriptive.
Example: The scope includes research, design, integration, testing, and support for advanced decision-support systems across multiple DoD components.""",
            "focus": "scope"
        },
        {
            "name": "3. Background",
            "guidance": """Provide context, including previous efforts, capability gaps, or challenges that led to this requirement.
Include any relevant lessons learned or related programs.
Example: The current maintenance framework lacks automated performance tracking and cross-platform integration, resulting in reduced readiness and increased sustainment costs.""",
            "focus": "outcomes"
        },
        {
            "name": "4. Objectives",
            "guidance": """List specific, outcome-based objectives that define success for the program.
Each objective should be measurable, achievable, and mission-aligned.
Examples:
- Improve data accuracy across logistics systems by 15% within 12 months
- Develop and demonstrate predictive maintenance algorithms to achieve 20% reduction in downtime
- Deliver personnel support services that meet 98% on-time staffing requirements""",
            "focus": "outcomes"
        },
        {
            "name": "5. Performance Measures / Standards",
            "guidance": """Identify measurable indicators of success that will be used to evaluate contractor performance.
Include metrics, thresholds, and data sources.
Example: Maintain system uptime ≥ 95%; data accuracy ≥ 90%; customer satisfaction ≥ 4.5/5 rating.""",
            "focus": "performance"
        },
        {
            "name": "6. Deliverables",
            "guidance": """List the key outputs or deliverables expected from the contractor.
Include documents, prototypes, systems, or data packages.
Example: Monthly progress reports, prototype demonstration, technical documentation, and transition plan.""",
            "focus": "outcomes"
        },
        {
            "name": "7. Period of Performance",
            "guidance": """Specify the anticipated duration of the contract, including base and option periods.
Example: Base period – 12 months; Option Year 1 – 12 months; Option Year 2 – 12 months.""",
            "focus": "outcomes"
        },
        {
            "name": "8. Government Roles and Responsibilities",
            "guidance": """Define Government-provided resources, data, access, and coordination responsibilities.
Clarify the Government's role in oversight or support.
Example: The Government will provide access to testing facilities, classified networks, and subject matter experts for coordination.""",
            "focus": "outcomes"
        },
        {
            "name": "9. Constraints",
            "guidance": """Identify known limitations such as budgetary, technical, security, interoperability, or environmental constraints.
Example: Work must comply with DoD cybersecurity requirements (NIST SP 800-171) and Section 508 accessibility standards.""",
            "focus": "constraints"
        },
        {
            "name": "10. References",
            "guidance": """List applicable laws, regulations, and guidance documents used in preparing the SOO.
Examples:
- FAR 37.602 – Performance-Based Acquisition
- DFARS PGI 237.170-2 – Performance-Based Acquisition Procedures
- DoD Source Selection Procedures (2022)
- Defense Acquisition University (DAU) Performance-Based Acquisition Guidebook""",
            "focus": "outcomes"
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

        # Initialize orchestrator with web search
        orchestrator = SOOOrchestrator(
            api_key=api_key,
            retriever=retriever,
            tavily_api_key=tavily_key,  # Pass Tavily API key
            model="claude-sonnet-4-20250514"
        )
        
        # Execute workflow
        result = orchestrator.execute_soo_workflow(
            project_info=project_info,
            soo_sections_config=soo_sections_config,
            output_path="outputs/soo/statement_of_objectives.md"
        )
        
        if result['status'] == 'success':
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nYour Statement of Objectives is ready:")
            print(f"  {result['output_path']}")
            print(f"\nTime elapsed: {result['elapsed_time']:.1f}s")
            print()
            return 0
        else:
            print("\n❌ SOO generation failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
