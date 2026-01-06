"""
Run Agent Pipeline: Enhanced with web search capabilities
Uses RAG system + coordinated agents + live web search to generate market research reports
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from backend.agents.orchestrator import Orchestrator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


def main():
    """
    Execute the enhanced agent-based market research pipeline
    """

    print("\n" + "="*70)
    print("ENHANCED AGENT-BASED MARKET RESEARCH PIPELINE")
    print("With Real-Time Web Search & External Data")
    print("="*70)
    print()

    # Load environment variables
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    tavily_key = os.environ.get('TAVILY_API_KEY')

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return 1

    if not tavily_key:
        print("⚠️  Warning: TAVILY_API_KEY not set - web search will be disabled")
        print("   To enable web search for current market data:")
        print("   1. Get free API key at: https://tavily.com")
        print("   2. Add to .env file: TAVILY_API_KEY='your-key'")
        print("   3. Or export: export TAVILY_API_KEY='your-key'")
        print("\n   Continuing with RAG-only mode...\n")
    
    # Configuration
    vector_db_path = "data/vector_db/faiss_index"
    
    # Check if vector store exists
    if not os.path.exists(f"{vector_db_path}.faiss"):
        print("⚠️  No vector store found!")
        print(f"\nPlease run setup first: python scripts/setup_rag_system.py")
        print("\nThis will process your documents and create the knowledge base.")
        return 1
    
    # Project information - CUSTOMIZE THIS
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "report_title": "Cloud-Based Inventory Management Services",
        "date": "10/03/2025",
        "product_service": "Comprehensive cloud-based inventory management and logistics tracking system",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
        "background_context": "Current inventory system is 15 years old and lacks modern cloud capabilities. Previous contract was $1.8M over 5 years.",
        "critical_requirements": "Real-time tracking, 99.9% uptime, integration with existing ERP systems, mobile access",
        "schedule_constraints": "Must be operational by Q2 FY2026",
        "vendor_research": "Conducted RFI in March 2025 with 12 responses, held industry day in April 2025 with 8 vendors",
        "potential_vendors": "TechLogistics Inc., CloudTrack Systems, MilSpec Software Solutions",
        "small_business_potential": "4 of 12 respondents were small businesses with relevant experience",
    }
    
    # Sections configuration
    sections_config = [
        {
            "name": "Product/Service Description",
            "guidance": """Include a description of the service to be addressed by this market research
report. Information shall be provided to state current and projected service
requirements to be addressed by this acquisition. Provide an estimated dollar amount
and projected period of contract performance for this requirement."""
        },
        {
            "name": "Background",
            "guidance": """Provide a short narrative on what this service shall be used to support. For
follow on contracts, include information relative to the previous awards such as:
past acquisition strategies supported, changes in the marketplace (suppliers, trends, technologies)"""
        },
        {
            "name": "Performance Requirements",
            "guidance": """State the critical performance requirements which the service must meet.
Identify as appropriate any critical and long lead schedule items which will impact
contract performance and delivery requirements."""
        },
        {
            "name": "Market Research Conducted",
            "guidance": """List any market research conducted to include:
- Requests for Information (RFIs) / Sources Sought notices
- Individual correspondence with potential sources
- Industry days
- Discussions with other buyers for similar services"""
        },
        {
            "name": "Industry Capabilities",
            "guidance": """List of potential vendors and known sources of supply that could be solicited
to provide the service required. Include location, point of contact information and an
assessment of their potential capabilities to meet our requirements."""
        },
        {
            "name": "Small Business Opportunities",
            "guidance": """Provide an assessment of the potential opportunities for small business set
aside and direct award opportunities."""
        },
        {
            "name": "Commercial Opportunities",
            "guidance": """Provide pertinent information that a contracting officer can use to conduct an
assessment as to whether the service meets the definitions of FAR Part 2 in terms of
commercial items or non-developmental items."""
        },
        {
            "name": "Conclusions and Recommendations",
            "guidance": """Summarize your data analysis with recommendations for:
- Acquisition strategies to pursue
- List of potential contract vehicles
- Relevant risks to be considered"""
        }
    ]
    
    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        vector_store = VectorStore(api_key, index_path=vector_db_path)
        
        if not vector_store.load():
            print("❌ Failed to load vector store")
            return 1
        
        retriever = Retriever(vector_store, top_k=7)
        print("✓ RAG system loaded")
        print()

        # Initialize orchestrator with web search
        print("Initializing orchestrator...")
        orchestrator = Orchestrator(
            api_key=api_key,
            retriever=retriever,
            tavily_api_key=tavily_key,  # Pass Tavily API key for web search
            model="claude-sonnet-4-20250514"
        )
        print("✓ Orchestrator initialized")
        if tavily_key:
            print("✓ Web search enabled - will fetch current market data")
        else:
            print("⚠️  Web search disabled - using RAG only")
        print()
        
        # Execute workflow
        result = orchestrator.execute_full_workflow(
            project_info=project_info,
            sections_config=sections_config,
            output_path="outputs/reports/agent_generated_report.md"
        )
        
        if result['status'] == 'success':
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nYour report is ready: {result['output_path']}")
            print()
            return 0
        else:
            print("\n❌ Workflow failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
